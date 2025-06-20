"""
Updated review analysis and filtering for hackathon review system.
Now uses RDF ontology and dynamic prompt generation.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

from src.infrastructure.config import CORE_DOMAINS
from src.infrastructure.llm_interface import (
    analyze_review_sentiment, 
    generate_artificial_review,
    generate_final_review_from_ontology
)
from src.infrastructure.logging_utils import logger
from src.infrastructure.config import LLM_CONFIG

class ReviewAnalyzer:
    """Class for analyzing and processing project reviews using RDF ontology."""
    
    def __init__(self, ontology, reviewer_profiler):
        """
        Initialize the review analyzer.
        
        Args:
            ontology: RDF Ontology object with dynamic prompt generation
            reviewer_profiler: ReviewerProfile object for reviewer classification
        """
        self.ontology = ontology
        self.reviewer_profiler = reviewer_profiler
    
    def analyze_project_reviews(self, project) -> None:
        """
        Analyze and process all reviews for a project using RDF ontology.
        
        Args:
            project: Project object
        """
        # Step 1: Filter reviews based on relevance and expertise
        self.reviewer_profiler.filter_reviews(project)
        
        # Step 2: Analyze sentiment and extract scores from reviews
        self._analyze_review_sentiments(project)
        
        # Step 3: Check for missing domains and generate artificial reviews if needed
        self._generate_missing_domain_reviews(project)
        
        # Step 4: Calculate final scores across dimensions (now dynamic from ontology)
        feedback_scores = self._calculate_feedback_scores(project)
        project.set_feedback_scores(feedback_scores)
        
        # Step 5: Generate final textual feedback using dynamic prompts
        final_review = self._generate_final_review(project)
        project.set_final_review(final_review)
    
    def _analyze_review_sentiments(self, project) -> None:
        """
        Analyze sentiments and extract scores from reviews using dynamic prompts.
        
        Args:
            project: Project object
        """
        for review in project.reviews:
            if not review.get("sentiment_scores") and review.get("is_accepted", False):
                review_text = review.get("text_review", "")
                # Pass ontology to sentiment analysis for dynamic prompts
                sentiment_scores = analyze_review_sentiment(review_text, self.ontology)
                review["sentiment_scores"] = sentiment_scores
    
    def _generate_missing_domain_reviews(self, project) -> None:
        """
        Generate artificial reviews for missing domains using RDF ontology.
        
        Args:
            project: Project object
        """
        # Get domains with accepted reviews
        covered_domains = set()
        for review in project.reviews:
            if review.get("is_accepted", False):
                domain = review.get("domain")
                if domain:
                    covered_domains.add(domain)
        
        # Get all available domains from ontology (dynamic)
        available_domains = self.ontology.get_domains()
        
        # Check for missing domains that are relevant to the project
        missing_domains = []
        project_description = project.get_full_description()
        
        for domain in available_domains:
            if domain not in covered_domains:
                # Check if domain is relevant to the project
                relevance = self.reviewer_profiler.check_domain_relevance(
                    project_description, domain
                )
                
                # Only generate reviews for somewhat relevant domains
                if relevance >= 0.2:
                    missing_domains.append(domain)
        
        # Generate artificial reviews for missing domains using dynamic prompts
        for domain in missing_domains:
            try:
                artificial_review = generate_artificial_review(
                    project_description, 
                    domain,
                    self.ontology  # Pass ontology for dynamic prompt generation
                )
                
                # Add sentiment scores to the artificial review using dynamic analysis
                sentiment_scores = analyze_review_sentiment(
                    artificial_review.get("text_review", ""), 
                    self.ontology
                )
                artificial_review["sentiment_scores"] = sentiment_scores
                artificial_review["is_accepted"] = True
                artificial_review["relevance_score"] = self.reviewer_profiler.check_domain_relevance(
                    project_description, domain
                )
                
                # Add to project reviews
                project.add_artificial_review(artificial_review)
                
                logger.info(f"Generated artificial review for domain: {domain}")
                
            except Exception as e:
                logger.error(f"Failed to generate artificial review for domain {domain}: {str(e)}")
    
    def _calculate_feedback_scores(self, project) -> Dict[str, float]:
        """
        Calculate aggregate feedback scores across dimensions (now dynamic from ontology).
        
        Args:
            project: Project object
            
        Returns:
            Dictionary of dimension names to aggregated scores
        """
        # Get all available dimensions from ontology dynamically
        available_dimensions = self.ontology.rdf_ontology.get_impact_dimensions()
        dimension_ids = [dim["id"] for dim in available_dimensions]
        
        logger.info(f"Calculating scores for dimensions: {dimension_ids}")
        
        # Collect all scores by dimension
        dimension_scores = defaultdict(list)
        dimension_weights = defaultdict(list)
        
        for review in project.reviews:
            if review.get("is_accepted", False) and review.get("sentiment_scores"):
                domain = review.get("domain", "")
                expertise_level = review.get("expertise_level", "beginner")
                confidence_score = review.get("confidence_score", 50)
                sentiment_scores = review.get("sentiment_scores", {})
                
                # Calculate weight based on expertise and confidence
                weight = self._calculate_review_weight(expertise_level, confidence_score)
                
                # Adjust weight for artificial reviews
                if review.get("is_artificial", False):
                    weight *= 0.7
                
                # Get relevant dimensions for this domain from ontology
                relevant_dimensions = self.ontology.get_relevant_dimensions_for_domain(domain)
                
                # Add scores for each dimension
                for dimension, score in sentiment_scores.items():
                    if dimension != "overall_sentiment" and dimension in dimension_ids:
                        # Higher weight for dimensions relevant to the domain
                        dimension_weight = weight
                        if dimension in relevant_dimensions:
                            dimension_weight *= 1.5
                        
                        dimension_scores[dimension].append(score)
                        dimension_weights[dimension].append(dimension_weight)
        
        # Calculate weighted average for each dimension
        feedback_scores = {}
        for dimension_id in dimension_ids:
            scores = dimension_scores.get(dimension_id, [])
            weights = dimension_weights.get(dimension_id, [])
            
            if scores and weights:
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                total_weight = sum(weights)
                feedback_scores[dimension_id] = round(weighted_sum / total_weight, 1)
            else:
                # Default score if no reviews cover this dimension
                feedback_scores[dimension_id] = 3.0
        
        logger.info(f"Calculated feedback scores: {feedback_scores}")
        return feedback_scores
    
    def _calculate_review_weight(self, expertise_level: str, confidence_score: int) -> float:
        """Calculate review weight based on expertise level and confidence."""
        # Base weight from expertise level
        expertise_weights = {
            "expert": 3.0,
            "seasoned": 2.5,
            "talented": 2.0,
            "skilled": 1.5,
            "beginner": 1.0
        }
        
        base_weight = expertise_weights.get(expertise_level, 1.0)
        
        # Adjust by confidence score (normalize 0-100 to 0.5-1.5 multiplier)
        confidence_multiplier = 0.5 + (confidence_score / 100.0)
        
        return base_weight * confidence_multiplier
    
    def _generate_final_review(self, project) -> str:
        """Generate a final textual review using dynamic prompts from ontology."""
        
        # Prepare project info
        project_info = {
            "name": project.project_data.get("name", ""),
            "description": project.project_data.get("description", ""),
            "work_done": project.project_data.get("work_done", "")
        }
        
        # Prepare reviews data
        reviews_data = []
        for review in project.reviews:
            if review.get("is_accepted", False):
                reviews_data.append({
                    "domain": review.get("domain", "unknown"),
                    "expertise_level": review.get("expertise_level", "beginner"),
                    "confidence_score": review.get("confidence_score", 0),
                    "sentiment_scores": review.get("sentiment_scores", {}),
                    "is_artificial": review.get("is_artificial", False),
                    "text_review": review.get("text_review", ""),
                    "reviewer_name": review.get("reviewer_name", "Anonymous")
                })
        
        # Get feedback scores
        feedback_scores = project.feedback_scores
        
        logger.debug(f"Generating final review with {len(reviews_data)} reviews")
        
        # Use dynamic prompt generation from ontology
        max_retries = LLM_CONFIG.get("max_retries", 3)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                final_review = generate_final_review_from_ontology(
                    project_info, reviews_data, feedback_scores, self.ontology
                )
                return final_review
            except Exception as e:
                retry_count += 1
                retry_delay = LLM_CONFIG.get("retry_delay", 2)
                logger.warning(f"Error generating final review (attempt {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error("Failed to generate final review after maximum retries.")
                    # Return a basic summary as fallback
                    return self._generate_fallback_review(project_info, feedback_scores)
                
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    def _generate_fallback_review(self, project_info: Dict[str, Any], feedback_scores: Dict[str, float]) -> str:
        """Generate a basic fallback review if LLM generation fails."""
        
        # Calculate overall score
        overall_score = sum(feedback_scores.values()) / len(feedback_scores) if feedback_scores else 3.0
        
        # Basic review template
        review = f"""# Review Summary for {project_info.get('name', 'Project')}

## Overall Assessment
This project received an overall score of {overall_score:.1f}/5.0 based on multi-perspective analysis.

## Dimension Scores
"""
        
        # Add dimension scores
        for dimension, score in feedback_scores.items():
            dim_name = dimension.replace("_", " ").title()
            review += f"- **{dim_name}**: {score}/5.0\n"
        
        review += """
## Summary
The evaluation was based on reviews from multiple domain experts. This automated summary was generated as a fallback when the primary review generation system was unavailable.

For detailed analysis, please review the individual expert assessments and dimension scores above.
"""
        
        return review
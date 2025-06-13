"""
Review analysis and filtering for hackathon review system.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

from src.infrastructure.config import CORE_DOMAINS
from src.infrastructure.llm_interface import analyze_review_sentiment, generate_artificial_review
from src.infrastructure.logging_utils import logger
from src.infrastructure.config import LLM_CONFIG, LLM_PROMPTS

class ReviewAnalyzer:
    """Class for analyzing and processing project reviews."""
    
    def __init__(self, ontology, reviewer_profiler):
        """
        Initialize the review analyzer.
        
        Args:
            ontology: Ontology object
            reviewer_profiler: ReviewerProfile object for reviewer classification
        """
        self.ontology = ontology
        self.reviewer_profiler = reviewer_profiler
    
    def analyze_project_reviews(self, project) -> None:
        """
        Analyze and process all reviews for a project.
        
        Args:
            project: Project object
        """
        # Step 1: Filter reviews based on relevance and expertise
        self.reviewer_profiler.filter_reviews(project)
        
        # Step 2: Analyze sentiment and extract scores from reviews
        self._analyze_review_sentiments(project)
        
        # Step 3: Check for missing domains and generate artificial reviews if needed
        self._generate_missing_domain_reviews(project)
        
        # Step 4: Calculate final scores across dimensions
        feedback_scores = self._calculate_feedback_scores(project)
        project.set_feedback_scores(feedback_scores)
        
        # Step 5: Generate final textual feedback
        final_review = self._generate_final_review(project)
        project.set_final_review(final_review)
    
    def _analyze_review_sentiments(self, project) -> None:
        """
        Analyze sentiments and extract scores from reviews.
        
        Args:
            project: Project object
        """
        for review in project.reviews:
            if not review.get("sentiment_scores") and review.get("is_accepted", False):
                review_text = review.get("text_review", "")
                sentiment_scores = analyze_review_sentiment(review_text)
                review["sentiment_scores"] = sentiment_scores
    
    def _generate_missing_domain_reviews(self, project) -> None:
        """
        Generate artificial reviews for missing domains.
        
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
        
        # Check for missing core domains
        missing_domains = []
        for domain in CORE_DOMAINS:
            if domain not in covered_domains:
                # Check if domain is relevant to the project
                relevance = self.reviewer_profiler.check_domain_relevance(
                    project.get_full_description(), domain
                )
                
                # Only generate reviews for somewhat relevant domains
                if relevance >= 0.2:
                    missing_domains.append(domain)
        
        # Generate artificial reviews for missing domains
        for domain in missing_domains:
            artificial_review = generate_artificial_review(
                project.get_full_description(), 
                domain,
                self.ontology
            )
            
            # Add sentiment scores to the artificial review
            sentiment_scores = analyze_review_sentiment(artificial_review.get("text_review", ""))
            artificial_review["sentiment_scores"] = sentiment_scores
            artificial_review["is_accepted"] = True
            artificial_review["relevance_score"] = self.reviewer_profiler.check_domain_relevance(
                project.get_full_description(), domain
            )
            
            # Add to project reviews
            project.add_artificial_review(artificial_review)
    
    def _calculate_feedback_scores(self, project) -> Dict[str, float]:
        """
        Calculate aggregate feedback scores across dimensions.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary of dimension names to aggregated scores
        """
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
                if expertise_level == "expert":
                    weight = 3.0
                elif expertise_level == "seasoned":
                    weight = 2.5
                elif expertise_level == "talented":
                    weight = 2.0
                elif expertise_level == "skilled":
                    weight = 1.5
                else:  # beginner
                    weight = 1.0
                
                # Adjust weight for artificial reviews
                if review.get("is_artificial", False):
                    weight *= 0.7
                
                # Get relevant dimensions for this domain
                relevant_dimensions = self.ontology.get_relevant_dimensions_for_domain(domain)
                
                # Add scores for each dimension
                for dimension, score in sentiment_scores.items():
                    if dimension != "overall_sentiment":
                        # Higher weight for dimensions relevant to the domain
                        dimension_weight = weight
                        if dimension in relevant_dimensions:
                            dimension_weight *= 1.5
                        
                        dimension_scores[dimension].append(score)
                        dimension_weights[dimension].append(dimension_weight)
        
        # Calculate weighted average for each dimension
        feedback_scores = {}
        for dimension, scores in dimension_scores.items():
            weights = dimension_weights[dimension]
            if scores and weights:
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                total_weight = sum(weights)
                feedback_scores[dimension] = round(weighted_sum / total_weight, 1)
            else:
                feedback_scores[dimension] = 3.0  # Default score
        
        return feedback_scores
    
    def _generate_final_review(self, project) -> str:
        """Generate a final textual review based on all accepted reviews."""
        
        # Get project name and description
        project_name = project.project_data.get("name", "")
        project_description = project.project_data.get("description", "")
        
        # Get feedback scores
        feedback_scores = project.feedback_scores
        
        # Group reviews by domain
        reviews_by_domain = defaultdict(list)
        for review in project.reviews:
            if review.get("is_accepted", False):
                domain = review.get("domain", "unknown")
                reviews_by_domain[domain].append(review)
        
        # Format dimension scores for prompt
        dimension_scores_text = ""
        for dimension, score in feedback_scores.items():
            if dimension != "overall_sentiment":
                dimension_name = dimension.replace("_", " ").title()
                dimension_scores_text += f"- {dimension_name}: {score}\n"
        
        # Format domain insights for prompt
        domain_insights_text = ""
        for domain, reviews in reviews_by_domain.items():
            domain_name = domain.capitalize()
            domain_insights_text += f"\n{domain_name} perspective:\n"
            
            for review in reviews:
                review_type = "AI-generated" if review.get("is_artificial", False) else "Human"
                expertise = review.get("expertise_level", "").capitalize()
                # Extract a snippet of the review text
                review_snippet = review.get('text_review', '')[:100].replace('\n', ' ').strip()
                domain_insights_text += f"- {review_type} {expertise} Reviewer: {review_snippet}...\n"
        
        # Get prompt template from config
        prompt_template = LLM_PROMPTS.get("generate_final_review")
        
        # Format the prompt
        prompt = prompt_template.format(
            project_name=project_name,
            project_description=project_description,
            dimension_scores=dimension_scores_text,
            domain_insights=domain_insights_text
        )
        
        logger.debug(f"Generating final review with prompt: {prompt[:200]}...")
        
        # Call LLM to generate the review
        from llm_interface import generate_llm_response
        
        max_retries = LLM_CONFIG.get("max_retries", 3)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                final_review = generate_llm_response(prompt)
                return final_review
            except Exception as e:
                retry_count += 1
                retry_delay = LLM_CONFIG.get("retry_delay", 2)
                logger.warning(f"Error generating final review (attempt {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error("Failed to generate final review after maximum retries.")
                    raise Exception("Failed to generate final review after maximum retries")
                
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
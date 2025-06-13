"""
Background processing for project review analysis
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

from src.infrastructure.database import get_db_context
from src.api.models import Project, Review, ProcessingJob, FeedbackReport
from src.core.ontology import Ontology
from src.core.reviewer import ReviewerProfile
from src.core.review import ReviewAnalyzer
from src.core.feedback import FeedbackGenerator
from src.infrastructure.llm_interface import analyze_review_sentiment, generate_artificial_review, generate_llm_response
from src.infrastructure.logging_utils import logger
from src.infrastructure.config import LLM_PROMPTS

# Processing steps
PROCESSING_STEPS = [
    "loading_project",
    "analyzing_reviews", 
    "classifying_reviewers",
    "generating_artificial_reviews",
    "calculating_scores",
    "generating_feedback"
]

def update_job_progress(job_id: str, step: str, completed: int, errors: List[str] = None):
    """Update processing job progress in database"""
    with get_db_context() as db:
        job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        if job:
            job.progress = {
                "current_step": step,
                "steps_completed": completed,
                "total_steps": len(PROCESSING_STEPS)
            }
            if errors:
                job.errors = errors
            if step == "completed":
                job.status = "completed"
                job.completed_at = datetime.utcnow()
            elif step == "failed":
                job.status = "failed"
                job.completed_at = datetime.utcnow()
            else:
                job.status = "processing"
            db.commit()

def process_project_reviews(project_id: str, job_id: str, options: Dict[str, Any]):
    """
    Process reviews for a project using the ontology-driven analysis system.
    This runs as a background task.
    """
    errors = []
    
    try:
        # Step 1: Load project and update status
        update_job_progress(job_id, "loading_project", 0)
        
        # Get project info
        project_info = {}
        with get_db_context() as db:
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Store project info for later use
            project_info = {
                "name": project.name,
                "description": project.description,
                "work_done": project.work_done
            }
            
            # Update project processing status
            project.processing_status = "processing"
            db.commit()
        
        # Step 2: Initialize analysis components
        ontology = Ontology(load_existing=True)
        reviewer_profiler = ReviewerProfile(ontology)
        review_analyzer = ReviewAnalyzer(ontology, reviewer_profiler)
        feedback_generator = FeedbackGenerator(ontology)
        
        # Step 3: Analyze and classify reviews
        update_job_progress(job_id, "analyzing_reviews", 1)
        
        # Process reviews one by one to avoid session issues
        with get_db_context() as db:
            reviews = db.query(Review).filter(Review.project_id == project_id).all()
            
            for review in reviews:
                try:
                    # Skip if already processed (unless force reprocess)
                    if review.domain and not options.get("force_reprocess", False):
                        continue
                    
                    # Extract review data while in session
                    review_data = {
                        "review_id": review.review_id,
                        "reviewer_name": review.reviewer_name,
                        "text_review": review.text_review,
                        "confidence_score": review.confidence_score,
                        "links": review.links or {},
                        "is_artificial": review.is_artificial
                    }
                    
                    # Classify reviewer
                    reviewer_profile = reviewer_profiler.classify_reviewer(
                        review_data["reviewer_name"],
                        review_data["text_review"],
                        review_data["confidence_score"],
                        review_data["links"]
                    )
                    
                    # Check domain relevance
                    project_description = f"{project_info['name']}\n{project_info['description']}\n{project_info['work_done']}"
                    relevance_score = reviewer_profiler.check_domain_relevance(
                        project_description,
                        reviewer_profile.get("domain")
                    )
                    
                    # Determine if review should be accepted
                    is_accepted = reviewer_profiler.should_accept_review(
                        {
                            "domain": reviewer_profile.get("domain"),
                            "confidence_score": review_data["confidence_score"],
                            "is_artificial": review_data["is_artificial"]
                        },
                        project_description
                    )
                    
                    # Analyze sentiment
                    sentiment_scores = analyze_review_sentiment(review_data["text_review"])
                    
                    # Update review in database
                    review.domain = reviewer_profile.get("domain")
                    review.expertise_level = reviewer_profile.get("expertise_level")
                    review.relevance_score = relevance_score
                    review.sentiment_scores = sentiment_scores
                    review.status = "accepted" if is_accepted else "rejected"
                    review.processed_at = datetime.utcnow()
                
                except Exception as e:
                    logger.error(f"Error processing review {review.review_id}: {str(e)}")
                    errors.append(f"Review {review.review_id}: {str(e)}")
            
            # Commit all review updates
            db.commit()
        
        # Step 4: Generate artificial reviews if needed
        if options.get("generate_artificial_reviews", True):
            update_job_progress(job_id, "generating_artificial_reviews", 2)
            
            # Get accepted reviews and their domains
            with get_db_context() as db:
                accepted_reviews = db.query(Review).filter(
                    Review.project_id == project_id,
                    Review.status == "accepted"
                ).all()
                
                covered_domains = set(r.domain for r in accepted_reviews if r.domain)
                
                # Check for missing core domains
                missing_domains = []
                project_description = f"{project_info['name']}\n{project_info['description']}\n{project_info['work_done']}"
                
                for domain in ["technical", "clinical", "administrative", "business", "design", "user_experience"]:
                    if domain not in covered_domains:
                        relevance = reviewer_profiler.check_domain_relevance(
                            project_description,
                            domain
                        )
                        if relevance >= 0.2:
                            missing_domains.append(domain)
                
                # Generate artificial reviews
                for domain in missing_domains:
                    try:
                        artificial_review_data = generate_artificial_review(
                            project_description,
                            domain,
                            ontology
                        )
                        
                        # Analyze sentiment
                        sentiment_scores = analyze_review_sentiment(artificial_review_data.get("text_review", ""))
                        
                        # Create review in database
                        review_id = f"rev_{uuid.uuid4().hex[:8]}"
                        artificial_review = Review(
                            review_id=review_id,
                            project_id=project_id,
                            reviewer_name=artificial_review_data.get("reviewer_name", f"AI {domain.capitalize()} Expert"),
                            text_review=artificial_review_data.get("text_review", ""),
                            confidence_score=artificial_review_data.get("confidence_score", 90),
                            domain=domain,
                            expertise_level="expert",
                            relevance_score=reviewer_profiler.check_domain_relevance(
                                project_description,
                                domain
                            ),
                            sentiment_scores=sentiment_scores,
                            is_artificial=True,
                            status="accepted",
                            submitted_at=datetime.utcnow(),
                            processed_at=datetime.utcnow()
                        )
                        
                        db.add(artificial_review)
                        db.commit()
                        
                    except Exception as e:
                        logger.error(f"Error generating artificial review for domain {domain}: {str(e)}")
                        errors.append(f"Artificial review {domain}: {str(e)}")
        
        # Step 5: Calculate feedback scores
        update_job_progress(job_id, "calculating_scores", 3)
        
        # Get all accepted reviews with their data
        accepted_reviews_data = []
        with get_db_context() as db:
            accepted_reviews = db.query(Review).filter(
                Review.project_id == project_id,
                Review.status == "accepted"
            ).all()
            
            # Extract data while in session
            for review in accepted_reviews:
                accepted_reviews_data.append({
                    "domain": review.domain,
                    "expertise_level": review.expertise_level,
                    "confidence_score": review.confidence_score,
                    "sentiment_scores": review.sentiment_scores,
                    "is_artificial": review.is_artificial,
                    "text_review": review.text_review,
                    "reviewer_name": review.reviewer_name
                })
        
        # Use updated function names
        feedback_scores = _calculate_feedback_scores_from_data(accepted_reviews_data, ontology)
        overall_score = sum(feedback_scores.values()) / len(feedback_scores) if feedback_scores else 0.0
        
        # Step 6: Generate final feedback
        update_job_progress(job_id, "generating_feedback", 4)
        
        # Generate final review text
        final_review = _generate_final_review_from_data(project_info, accepted_reviews_data, feedback_scores)
        
        # Generate domain insights
        domain_insights = _generate_domain_insights_from_data(accepted_reviews_data)
        
        # Generate recommendations
        recommendations = _generate_recommendations(feedback_scores, domain_insights)
        
        # Save feedback report and update project status
        with get_db_context() as db:
            # Get the job for timing info
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
            processing_time = (datetime.utcnow() - job.started_at).total_seconds() if job else 0
            
            # Get counts for metadata
            total_reviews = db.query(Review).filter(Review.project_id == project_id).count()
            human_reviews = len([r for r in accepted_reviews_data if not r["is_artificial"]])
            artificial_reviews = len([r for r in accepted_reviews_data if r["is_artificial"]])
            
            report_id = f"rep_{uuid.uuid4().hex[:8]}"
            feedback_report = FeedbackReport(
                report_id=report_id,
                project_id=project_id,
                feedback_scores=feedback_scores,
                overall_score=round(overall_score, 1),
                final_review=final_review,
                domain_insights=domain_insights,
                recommendations=recommendations,
                meta_data={
                    "total_reviews": total_reviews,
                    "accepted_reviews": len(accepted_reviews_data),
                    "human_reviews": human_reviews,
                    "artificial_reviews": artificial_reviews,
                    "processing_time_seconds": processing_time
                }
            )
            
            db.add(feedback_report)
            
            # Update project status
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if project:
                project.processing_status = "completed"
            
            db.commit()
        
        # Mark job as completed
        update_job_progress(job_id, "completed", len(PROCESSING_STEPS), errors)
        
    except Exception as e:
        logger.error(f"Fatal error processing project {project_id}: {str(e)}")
        errors.append(f"Fatal error: {str(e)}")
        update_job_progress(job_id, "failed", 0, errors)
        
        # Update project status
        with get_db_context() as db:
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if project:
                project.processing_status = "failed"
                db.commit()

def _calculate_feedback_scores_from_data(reviews_data: List[Dict[str, Any]], ontology: Ontology) -> Dict[str, float]:
    """Calculate aggregate feedback scores from review data"""
    from collections import defaultdict
    
    dimension_scores = defaultdict(list)
    dimension_weights = defaultdict(list)
    
    for review in reviews_data:
        if review.get("sentiment_scores"):
            # Get weight based on expertise and confidence
            weight = 1.0
            expertise_level = review.get("expertise_level", "beginner")
            if expertise_level == "expert":
                weight = 3.0
            elif expertise_level == "seasoned":
                weight = 2.5
            elif expertise_level == "talented":
                weight = 2.0
            elif expertise_level == "skilled":
                weight = 1.5
            
            # Reduce weight for artificial reviews
            if review.get("is_artificial", False):
                weight *= 0.7
            
            # Get relevant dimensions for this domain
            domain = review.get("domain", "")
            relevant_dimensions = ontology.get_relevant_dimensions_for_domain(domain) if domain else []
            
            # Add scores
            for dimension, score in review["sentiment_scores"].items():
                if dimension != "overall_sentiment":
                    dimension_weight = weight
                    if dimension in relevant_dimensions:
                        dimension_weight *= 1.5
                    
                    dimension_scores[dimension].append(score)
                    dimension_weights[dimension].append(dimension_weight)
    
    # Calculate weighted averages
    feedback_scores = {}
    for dimension, scores in dimension_scores.items():
        weights = dimension_weights[dimension]
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            feedback_scores[dimension] = round(weighted_sum / total_weight, 1)
        else:
            feedback_scores[dimension] = 3.0  # Default
    
    return feedback_scores

def _generate_final_review_from_data(project_info: Dict[str, Any], reviews_data: List[Dict[str, Any]], scores: Dict[str, float]) -> str:
    """Generate final review text based on extracted review data"""
    from llm_interface import generate_llm_response
    from config import LLM_PROMPTS
    
    # Group reviews by domain
    reviews_by_domain = {}
    for review in reviews_data:
        domain = review.get("domain", "unknown")
        if domain not in reviews_by_domain:
            reviews_by_domain[domain] = []
        reviews_by_domain[domain].append(review)
    
    # Format dimension scores
    dimension_scores_text = ""
    for dimension, score in scores.items():
        if dimension != "overall_sentiment":
            dimension_name = dimension.replace("_", " ").title()
            dimension_scores_text += f"- {dimension_name}: {score}\n"
    
    # Format domain insights
    domain_insights_text = ""
    for domain, domain_reviews in reviews_by_domain.items():
        domain_name = domain.capitalize()
        domain_insights_text += f"\n{domain_name} perspective:\n"
        
        for review in domain_reviews:
            review_type = "AI-generated" if review.get("is_artificial", False) else "Human"
            expertise = review.get("expertise_level", "").capitalize() if review.get("expertise_level") else ""
            review_snippet = review.get("text_review", "")[:100].replace('\n', ' ').strip()
            domain_insights_text += f"- {review_type} {expertise} Reviewer: {review_snippet}...\n"
    
    # Get prompt template and generate
    prompt_template = LLM_PROMPTS.get("generate_final_review")
    prompt = prompt_template.format(
        project_name=project_info.get("name", ""),
        project_description=f"{project_info.get('description', '')}\n\nWork done: {project_info.get('work_done', '')}",
        dimension_scores=dimension_scores_text,
        domain_insights=domain_insights_text
    )
    
    return generate_llm_response(prompt)

def _generate_domain_insights_from_data(reviews_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate insights grouped by domain from review data"""
    insights = {}
    
    # Group reviews by domain
    reviews_by_domain = {}
    for review in reviews_data:
        domain = review.get("domain", "unknown")
        if domain not in reviews_by_domain:
            reviews_by_domain[domain] = []
        reviews_by_domain[domain].append(review)
    
    # Generate insights for each domain
    for domain, domain_reviews in reviews_by_domain.items():
        # Extract key themes from reviews
        positive_points = []
        concerns = []
        
        for review in domain_reviews:
            sentiment_scores = review.get("sentiment_scores", {})
            # High scoring dimensions
            for dim, score in sentiment_scores.items():
                if score >= 4.0 and dim != "overall_sentiment":
                    positive_points.append(dim.replace("_", " ").title())
                elif score <= 2.5 and dim != "overall_sentiment":
                    concerns.append(dim.replace("_", " ").title())
        
        insights[domain] = {
            "summary": f"Perspective from {len(domain_reviews)} {domain} reviewer(s)",
            "key_points": list(set(positive_points))[:3],
            "concerns": list(set(concerns))[:3]
        }
    
    return insights

def _generate_recommendations(scores: Dict[str, float], insights: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on scores and insights"""
    recommendations = []
    
    # Low scoring dimensions
    for dimension, score in scores.items():
        if score < 3.0:
            dim_name = dimension.replace("_", " ").title()
            if dimension == "technical_feasibility":
                recommendations.append(f"Address technical challenges to improve {dim_name}")
            elif dimension == "implementation_complexity":
                recommendations.append("Simplify implementation approach for easier adoption")
            elif dimension == "scalability":
                recommendations.append("Develop a clear scaling strategy")
            elif dimension == "return_on_investment":
                recommendations.append("Clarify value proposition and ROI metrics")
    
    # Domain-specific recommendations
    for domain, insight in insights.items():
        if insight.get("concerns"):
            recommendations.append(f"Address {domain} concerns: {', '.join(insight['concerns'][:2])}")
    
    # General recommendations based on patterns
    if scores.get("innovation", 0) > 4.0 and scores.get("technical_feasibility", 0) < 3.0:
        recommendations.append("Consider simplifying innovative features for better feasibility")
    
    if scores.get("impact", 0) > 4.0:
        recommendations.append("Leverage high impact potential with clear implementation roadmap")
    
    return recommendations[:5]  # Return top 5 recommendations
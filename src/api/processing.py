import uuid
from datetime import datetime
from typing import Dict, Any, List

from src.infrastructure.database import get_db_context
from src.api.models import Project, Review, ProcessingJob, FeedbackReport
from src.core.ontology import Ontology
from src.core.reviewer import ReviewerProfile
from src.core.review import ReviewAnalyzer
from src.core.feedback import FeedbackGenerator
from src.infrastructure.llm_interface import (
    analyze_review_sentiment, 
    generate_artificial_review, 
    generate_final_review_from_ontology
)
from src.infrastructure.logging_utils import logger

# Processing steps
PROCESSING_STEPS = [
    "loading_project",
    "initializing_ontology",
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
    Process reviews for a project using the RDF ontology-driven analysis system.
    This runs as a background task.
    """
    errors = []
    ontology = None
    
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
        
        # Step 2: Initialize RDF ontology and analysis components
        update_job_progress(job_id, "initializing_ontology", 1)
        
        try:
            # Load ontology with RDF backend
            ontology = Ontology(load_existing=True)
            logger.info(f"Loaded RDF ontology with {len(ontology.get_domains())} domains")
            
            # Log ontology stats for debugging
            ontology_stats = ontology.rdf_ontology._get_ontology_stats() if hasattr(ontology.rdf_ontology, '_get_ontology_stats') else {}
            logger.info(f"Ontology stats: {ontology_stats}")
            
        except Exception as e:
            logger.error(f"Failed to load RDF ontology: {str(e)}")
            errors.append(f"Ontology loading error: {str(e)}")
            raise
        
        # Initialize analysis components
        reviewer_profiler = ReviewerProfile(ontology)
        review_analyzer = ReviewAnalyzer(ontology, reviewer_profiler)
        feedback_generator = FeedbackGenerator(ontology)
        
        # Step 3: Analyze and classify reviews
        update_job_progress(job_id, "analyzing_reviews", 2)
        
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
                    
                    # Classify reviewer using dynamic prompts from ontology
                    reviewer_profile = reviewer_profiler.classify_reviewer(
                        review_data["reviewer_name"],
                        review_data["text_review"],
                        review_data["confidence_score"],
                        review_data["links"]
                    )
                    
                    # Check domain relevance using dynamic calculation
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
                    
                    # Analyze sentiment using dynamic prompts from ontology
                    sentiment_scores = analyze_review_sentiment(review_data["text_review"], ontology)
                    
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
        
        # Step 4: Generate artificial reviews if needed using dynamic prompts
        if options.get("generate_artificial_reviews", True):
            update_job_progress(job_id, "generating_artificial_reviews", 3)
            
            # Get accepted reviews and their domains
            with get_db_context() as db:
                accepted_reviews = db.query(Review).filter(
                    Review.project_id == project_id,
                    Review.status == "accepted"
                ).all()
                
                covered_domains = set(r.domain for r in accepted_reviews if r.domain)
                
                # Get all available domains from ontology dynamically
                available_domains = ontology.get_domains()
                logger.info(f"Available domains from ontology: {available_domains}")
                logger.info(f"Covered domains: {covered_domains}")
                
                # Check for missing domains
                missing_domains = []
                project_description = f"{project_info['name']}\n{project_info['description']}\n{project_info['work_done']}"
                
                for domain in available_domains:
                    if domain not in covered_domains:
                        relevance = reviewer_profiler.check_domain_relevance(
                            project_description,
                            domain
                        )
                        logger.info(f"Domain {domain} relevance: {relevance}")
                        if relevance >= 0.2:
                            missing_domains.append(domain)
                
                logger.info(f"Generating artificial reviews for missing domains: {missing_domains}")
                
                # Generate artificial reviews using dynamic prompts from ontology
                for domain in missing_domains:
                    try:
                        artificial_review_data = generate_artificial_review(
                            project_description,
                            domain,
                            ontology  # Pass ontology for dynamic prompt generation
                        )
                        
                        # Analyze sentiment using dynamic prompts
                        sentiment_scores = analyze_review_sentiment(
                            artificial_review_data.get("text_review", ""), 
                            ontology
                        )
                        
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
                        
                        logger.info(f"Generated artificial review for domain: {domain}")
                        
                    except Exception as e:
                        logger.error(f"Error generating artificial review for domain {domain}: {str(e)}")
                        errors.append(f"Artificial review {domain}: {str(e)}")
        
        # Step 5: Calculate feedback scores using dynamic dimensions from ontology
        update_job_progress(job_id, "calculating_scores", 4)
        
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
        
        # Calculate feedback scores using dynamic dimensions from ontology
        feedback_scores = _calculate_feedback_scores_from_data_dynamic(accepted_reviews_data, ontology)
        overall_score = sum(feedback_scores.values()) / len(feedback_scores) if feedback_scores else 0.0
        
        # Step 6: Generate final feedback using dynamic prompts from ontology
        update_job_progress(job_id, "generating_feedback", 5)
        
        # Generate final review text using dynamic prompts
        final_review = generate_final_review_from_ontology(project_info, accepted_reviews_data, feedback_scores, ontology)
        
        # Generate domain insights using ontology information
        domain_insights = _generate_domain_insights_from_data_dynamic(accepted_reviews_data, ontology)
        
        # Generate recommendations using dynamic analysis
        recommendations = _generate_recommendations_dynamic(feedback_scores, domain_insights, ontology)
        
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
                    "processing_time_seconds": processing_time,
                    "ontology_stats": {
                        "domains_used": len(set(r["domain"] for r in accepted_reviews_data if r["domain"])),
                        "total_domains_available": len(ontology.get_domains()),
                        "dimensions_evaluated": len(feedback_scores)
                    }
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
        
        logger.info(f"Successfully processed project {project_id} using RDF ontology")
        
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

def _calculate_feedback_scores_from_data_dynamic(reviews_data: List[Dict[str, Any]], ontology: Ontology) -> Dict[str, float]:
    """Calculate aggregate feedback scores from review data using dynamic dimensions from ontology"""
    from collections import defaultdict
    
    # Get available dimensions dynamically from ontology
    available_dimensions = ontology.rdf_ontology.get_impact_dimensions()
    dimension_ids = [dim["id"] for dim in available_dimensions]
    
    logger.info(f"Calculating scores for dynamic dimensions: {dimension_ids}")
    
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
            
            # Get relevant dimensions for this domain from ontology
            domain = review.get("domain", "")
            relevant_dimensions = ontology.get_relevant_dimensions_for_domain(domain) if domain else []
            
            # Add scores
            for dimension, score in review["sentiment_scores"].items():
                if dimension != "overall_sentiment" and dimension in dimension_ids:
                    dimension_weight = weight
                    if dimension in relevant_dimensions:
                        dimension_weight *= 1.5
                    
                    dimension_scores[dimension].append(score)
                    dimension_weights[dimension].append(dimension_weight)
    
    # Calculate weighted averages
    feedback_scores = {}
    for dimension_id in dimension_ids:
        scores = dimension_scores.get(dimension_id, [])
        weights = dimension_weights.get(dimension_id, [])
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            feedback_scores[dimension_id] = round(weighted_sum / total_weight, 1)
        else:
            feedback_scores[dimension_id] = 3.0  # Default
    
    logger.info(f"Calculated dynamic feedback scores: {feedback_scores}")
    return feedback_scores

def _generate_domain_insights_from_data_dynamic(reviews_data: List[Dict[str, Any]], ontology: Ontology) -> Dict[str, Any]:
    """Generate insights grouped by domain from review data using ontology information"""
    insights = {}
    
    # Get domain information from ontology
    domains_info = {domain["id"]: domain for domain in ontology.rdf_ontology.get_domains()}
    
    # Group reviews by domain
    reviews_by_domain = {}
    for review in reviews_data:
        domain = review.get("domain", "unknown")
        if domain not in reviews_by_domain:
            reviews_by_domain[domain] = []
        reviews_by_domain[domain].append(review)
    
    # Generate insights for each domain
    for domain, domain_reviews in reviews_by_domain.items():
        # Get domain information from ontology
        domain_info = domains_info.get(domain, {})
        domain_name = domain_info.get("name", domain.capitalize())
        domain_desc = domain_info.get("description", "")
        
        # Extract key themes from reviews
        positive_points = []
        concerns = []
        
        for review in domain_reviews:
            sentiment_scores = review.get("sentiment_scores", {})
            # High scoring dimensions
            for dim, score in sentiment_scores.items():
                if score >= 4.0 and dim != "overall_sentiment":
                    # Get dimension name from ontology
                    dim_info = ontology.rdf_ontology.get_dimension_by_id(dim)
                    dim_name = dim_info["name"] if dim_info else dim.replace("_", " ").title()
                    positive_points.append(dim_name)
                elif score <= 2.5 and dim != "overall_sentiment":
                    # Get dimension name from ontology
                    dim_info = ontology.rdf_ontology.get_dimension_by_id(dim)
                    dim_name = dim_info["name"] if dim_info else dim.replace("_", " ").title()
                    concerns.append(dim_name)
        
        insights[domain] = {
            "domain_name": domain_name,
            "domain_description": domain_desc,
            "summary": f"Perspective from {len(domain_reviews)} {domain_name} reviewer(s)",
            "key_points": list(set(positive_points))[:3],
            "concerns": list(set(concerns))[:3],
            "review_count": len(domain_reviews),
            "artificial_count": len([r for r in domain_reviews if r.get("is_artificial", False)])
        }
    
    return insights

def _generate_recommendations_dynamic(scores: Dict[str, float], insights: Dict[str, Any], ontology: Ontology) -> List[str]:
    """Generate actionable recommendations based on scores and insights using ontology information"""
    recommendations = []
    
    # Get dimension information from ontology for better recommendations
    dimensions_info = {dim["id"]: dim for dim in ontology.rdf_ontology.get_impact_dimensions()}
    
    # Low scoring dimensions
    for dimension_id, score in scores.items():
        if score < 3.0:
            dim_info = dimensions_info.get(dimension_id, {})
            dim_name = dim_info.get("name", dimension_id.replace("_", " ").title())
            dim_desc = dim_info.get("description", "")
            
            # Generate specific recommendations based on dimension
            if dimension_id == "technical_feasibility":
                recommendations.append(f"Address technical challenges to improve {dim_name}")
            elif dimension_id == "implementation_complexity":
                recommendations.append("Simplify implementation approach for easier adoption")
            elif dimension_id == "scalability":
                recommendations.append("Develop a clear scaling strategy")
            elif dimension_id == "return_on_investment":
                recommendations.append("Clarify value proposition and ROI metrics")
            elif dimension_id == "innovation":
                recommendations.append("Enhance innovative aspects or differentiation")
            elif dimension_id == "impact":
                recommendations.append("Strengthen the potential impact and benefits")
            else:
                recommendations.append(f"Focus on improving {dim_name}: {dim_desc}")
    
    # Domain-specific recommendations
    for domain, insight in insights.items():
        if insight.get("concerns"):
            domain_name = insight.get("domain_name", domain.capitalize())
            recommendations.append(f"Address {domain_name} concerns: {', '.join(insight['concerns'][:2])}")
    
    # General recommendations based on patterns
    if scores.get("innovation", 0) > 4.0 and scores.get("technical_feasibility", 0) < 3.0:
        recommendations.append("Consider simplifying innovative features for better feasibility")
    
    if scores.get("impact", 0) > 4.0:
        recommendations.append("Leverage high impact potential with clear implementation roadmap")
    
    # Ensure we have at least one recommendation
    if not recommendations:
        recommendations.append("Continue development with focus on identified strengths")
    
    return recommendations[:5]  # Return top 5 recommendations
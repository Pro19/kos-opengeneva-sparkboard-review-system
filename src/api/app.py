"""
Updated REST API implementation with RDF ontology management capabilities.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import asyncio
from enum import Enum
from sqlalchemy.orm import Session

from src.infrastructure.database import init_db, get_db
from src.api.models import (
    Project, Review, ProcessingJob, FeedbackReport,
    ProjectCreate, ProjectUpdate, ReviewCreate,
    ProcessOptions, ProjectResponse, ReviewResponse,
    ProcessingStatusResponse, FeedbackResponse, VisualizationData
)
from src.api.processing import process_project_reviews
from src.api.scalar_fastapi import get_scalar_api_reference
from src.core.ontology import Ontology  # Updated ontology with RDF backend
from src.infrastructure.logging_utils import logger

# Global ontology instance
global_ontology = None

# Initialize database and ontology on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global global_ontology
    init_db()
    
    # Initialize ontology
    try:
        global_ontology = Ontology(load_existing=True)
        logger.info("RDF ontology loaded successfully for API")
    except Exception as e:
        logger.error(f"Failed to load RDF ontology: {str(e)}")
        # Continue without ontology but log the error
        global_ontology = None
    
    yield
    # Shutdown (if needed)

# Create FastAPI app
app = FastAPI(
    title="Ontology-Driven Hackathon Review API",
    description="AI-powered multi-perspective peer review system using RDF ontology",
    version="2.0.0",  # Updated version for RDF integration
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for ontology management
class DomainCreate(BaseModel):
    id: str = Field(..., description="Unique domain identifier")
    name: str = Field(..., description="Human-readable domain name")
    description: str = Field(..., description="Domain description")
    keywords: List[str] = Field(..., description="Domain keywords")
    relevant_dimensions: Optional[List[str]] = Field([], description="Relevant evaluation dimensions")

class DimensionCreate(BaseModel):
    id: str = Field(..., description="Unique dimension identifier")
    name: str = Field(..., description="Human-readable dimension name")
    description: str = Field(..., description="Dimension description")
    scale: Dict[str, str] = Field(..., description="Scale descriptions (1-5)")

class DomainResponse(BaseModel):
    id: str
    name: str
    description: str
    keywords: List[str]
    subdomains: Dict[str, Any] = {}

class DimensionResponse(BaseModel):
    id: str
    name: str
    description: str
    scale: Dict[str, str]

class ExpertiseLevelResponse(BaseModel):
    id: str
    name: str
    description: str
    confidence_range: List[int]

class OntologyStatsResponse(BaseModel):
    total_domains: int
    total_dimensions: int
    total_expertise_levels: int
    total_project_types: int
    domains: List[str]
    dimensions: List[str]

# API Documentation endpoints
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API documentation links"""
    return {
        "message": "Ontology-Driven Hackathon Review API v2.0",
        "features": [
            "RDF/TTL ontology backend",
            "Dynamic prompt generation",
            "Multi-perspective AI reviews",
            "Ontology management APIs"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc", 
            "scalar": "/scalar",
            "openapi": "/openapi.json"
        }
    }

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Scalar API documentation"""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

# Ontology Management APIs

@app.get("/api/v1/ontology/stats", response_model=OntologyStatsResponse)
async def get_ontology_stats():
    """Get statistics about the current ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        domains = global_ontology.rdf_ontology.get_domains()
        dimensions = global_ontology.rdf_ontology.get_impact_dimensions()
        levels = global_ontology.rdf_ontology.get_expertise_levels()
        project_types = global_ontology.rdf_ontology.get_project_types()
        
        return OntologyStatsResponse(
            total_domains=len(domains),
            total_dimensions=len(dimensions),
            total_expertise_levels=len(levels),
            total_project_types=len(project_types),
            domains=[d["name"] for d in domains],
            dimensions=[d["name"] for d in dimensions]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ontology stats: {str(e)}")

@app.get("/api/v1/ontology/domains", response_model=List[DomainResponse])
async def get_domains():
    """Get all available domains from the ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        domains = global_ontology.rdf_ontology.get_domains()
        return [DomainResponse(**domain) for domain in domains]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting domains: {str(e)}")

@app.get("/api/v1/ontology/domains/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: str):
    """Get a specific domain by ID."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        domain = global_ontology.rdf_ontology.get_domain_by_id(domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain {domain_id} not found")
        return DomainResponse(**domain)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting domain: {str(e)}")

@app.post("/api/v1/ontology/domains", response_model=DomainResponse, status_code=201)
async def create_domain(domain: DomainCreate):
    """Add a new domain to the ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        # Check if domain already exists
        existing = global_ontology.rdf_ontology.get_domain_by_id(domain.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Domain {domain.id} already exists")
        
        # Add domain to ontology
        global_ontology.add_domain(
            domain_id=domain.id,
            name=domain.name,
            description=domain.description,
            keywords=domain.keywords,
            relevant_dimensions=domain.relevant_dimensions
        )
        
        # Save changes
        global_ontology.save_ontology()
        
        # Return the created domain
        created_domain = global_ontology.rdf_ontology.get_domain_by_id(domain.id)
        return DomainResponse(**created_domain)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating domain: {str(e)}")

@app.get("/api/v1/ontology/dimensions", response_model=List[DimensionResponse])
async def get_dimensions():
    """Get all available evaluation dimensions from the ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        dimensions = global_ontology.rdf_ontology.get_impact_dimensions()
        return [DimensionResponse(**dim) for dim in dimensions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dimensions: {str(e)}")

@app.get("/api/v1/ontology/dimensions/{dimension_id}", response_model=DimensionResponse)
async def get_dimension(dimension_id: str):
    """Get a specific dimension by ID."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        dimension = global_ontology.rdf_ontology.get_dimension_by_id(dimension_id)
        if not dimension:
            raise HTTPException(status_code=404, detail=f"Dimension {dimension_id} not found")
        return DimensionResponse(**dimension)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dimension: {str(e)}")

@app.post("/api/v1/ontology/dimensions", response_model=DimensionResponse, status_code=201)
async def create_dimension(dimension: DimensionCreate):
    """Add a new evaluation dimension to the ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        # Check if dimension already exists
        existing = global_ontology.rdf_ontology.get_dimension_by_id(dimension.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Dimension {dimension.id} already exists")
        
        # Add dimension to ontology
        global_ontology.add_impact_dimension(
            dimension_id=dimension.id,
            name=dimension.name,
            description=dimension.description,
            scale=dimension.scale
        )
        
        # Save changes
        global_ontology.save_ontology()
        
        # Return the created dimension
        created_dimension = global_ontology.rdf_ontology.get_dimension_by_id(dimension.id)
        return DimensionResponse(**created_dimension)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating dimension: {str(e)}")

@app.get("/api/v1/ontology/expertise-levels", response_model=List[ExpertiseLevelResponse])
async def get_expertise_levels():
    """Get all expertise levels from the ontology."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        levels = global_ontology.rdf_ontology.get_expertise_levels()
        return [ExpertiseLevelResponse(**level) for level in levels]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting expertise levels: {str(e)}")

@app.get("/api/v1/ontology/domains/{domain_id}/relevant-dimensions")
async def get_domain_relevant_dimensions(domain_id: str):
    """Get evaluation dimensions relevant to a specific domain."""
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available")
    
    try:
        # Check if domain exists
        domain = global_ontology.rdf_ontology.get_domain_by_id(domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain {domain_id} not found")
        
        relevant_dims = global_ontology.get_relevant_dimensions_for_domain(domain_id)
        
        # Get full dimension information
        dimensions_info = []
        for dim_id in relevant_dims:
            dim = global_ontology.rdf_ontology.get_dimension_by_id(dim_id)
            if dim:
                dimensions_info.append(DimensionResponse(**dim))
        
        return {
            "domain_id": domain_id,
            "domain_name": domain["name"],
            "relevant_dimensions": dimensions_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting relevant dimensions: {str(e)}")

@app.post("/api/v1/ontology/reload")
async def reload_ontology():
    """Reload the ontology from the TTL file."""
    global global_ontology
    
    try:
        global_ontology = Ontology(load_existing=True)
        logger.info("Ontology reloaded successfully")
        return {"message": "Ontology reloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to reload ontology: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reloading ontology: {str(e)}")

# Project Management APIs (existing, but updated to work with ontology)

@app.post("/api/v1/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project for review.
    
    - **hackathon_id**: Unique identifier for the hackathon
    - **name**: Project name
    - **description**: Detailed project description
    - **work_done**: Description of work completed so far
    - **metadata**: Optional additional metadata
    """
    try:
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        # If ontology is available, classify project type
        project_type = None
        if global_ontology:
            try:
                project_description = f"{project.name}\n{project.description}\n{project.work_done}"
                project_type = global_ontology.classify_project_type(project_description)
            except Exception as e:
                logger.warning(f"Could not classify project type: {str(e)}")
        
        # Add project type to metadata
        meta_data = project.meta_data or {}
        if project_type:
            meta_data["classified_project_type"] = project_type
        
        db_project = Project(
            project_id=project_id,
            hackathon_id=project.hackathon_id,
            name=project.name,
            description=project.description,
            work_done=project.work_done,
            meta_data=meta_data,
            status="active",
            processing_status="pending",
            review_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        return ProjectResponse.from_orm(db_project)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific project."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.from_orm(project)

@app.put("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project's information."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields if provided
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.from_orm(project)

# Review Management APIs (existing)

@app.post("/api/v1/projects/{project_id}/reviews", response_model=ReviewResponse, status_code=201)
async def submit_review(project_id: str, review: ReviewCreate, db: Session = Depends(get_db)):
    """
    Submit a review for a project.
    
    - **reviewer_name**: Name of the reviewer
    - **text_review**: Full text of the review
    - **confidence_score**: Reviewer's confidence in their assessment (0-100)
    - **links**: Optional external profile links
    - **metadata**: Optional additional metadata
    """
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        review_id = f"rev_{uuid.uuid4().hex[:8]}"
        
        db_review = Review(
            review_id=review_id,
            project_id=project_id,
            reviewer_name=review.reviewer_name,
            text_review=review.text_review,
            confidence_score=review.confidence_score,
            links=review.links,
            meta_data=review.meta_data,
            status="submitted",
            processing_status="pending",
            submitted_at=datetime.utcnow()
        )
        
        db.add(db_review)
        
        # Update project review count
        project.review_count += 1
        project.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_review)
        
        return ReviewResponse.from_orm(db_review)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/reviews")
async def get_project_reviews(
    project_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query("all", regex="^(all|submitted|accepted|rejected)$"),
    db: Session = Depends(get_db)
):
    """Get all reviews for a project with pagination."""
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Build query
    query = db.query(Review).filter(Review.project_id == project_id)
    
    if status != "all":
        query = query.filter(Review.status == status)
    
    # Get total count
    total_count = query.count()
    
    # Get reviews with pagination
    reviews = query.offset(offset).limit(limit).all()
    
    # Count accepted and artificial reviews
    accepted_count = db.query(Review).filter(
        Review.project_id == project_id, 
        Review.status == "accepted"
    ).count()
    
    artificial_count = db.query(Review).filter(
        Review.project_id == project_id,
        Review.is_artificial == True
    ).count()
    
    return {
        "reviews": [ReviewResponse.from_orm(r) for r in reviews],
        "total_count": total_count,
        "accepted_count": accepted_count,
        "artificial_count": artificial_count,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
    }

@app.get("/api/v1/projects/{project_id}/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(project_id: str, review_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific review."""
    review = db.query(Review).filter(
        Review.project_id == project_id,
        Review.review_id == review_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return ReviewResponse.from_orm(review)

# Processing APIs (existing, but now uses RDF ontology)

@app.post("/api/v1/projects/{project_id}/process", status_code=202)
async def start_processing(
    project_id: str, 
    options: ProcessOptions,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start or restart the review analysis process for a project using RDF ontology.
    
    This endpoint is idempotent - calling it multiple times will not create duplicate jobs
    unless force_reprocess is set to true.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if ontology is available
    if not global_ontology:
        raise HTTPException(status_code=503, detail="Ontology not available - cannot process reviews")
    
    # Check if already processing (idempotency)
    existing_job = db.query(ProcessingJob).filter(
        ProcessingJob.project_id == project_id,
        ProcessingJob.status.in_(["pending", "processing"])
    ).first()
    
    if existing_job and not options.force_reprocess:
        return ProcessingStatusResponse.from_orm(existing_job)
    
    # Create new processing job
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    processing_job = ProcessingJob(
        job_id=job_id,
        project_id=project_id,
        status="pending",
        started_at=datetime.utcnow(),
        progress={
            "current_step": "starting",
            "steps_completed": 0,
            "total_steps": 7  # Updated for RDF ontology steps
        },
        options=options.dict()
    )
    
    db.add(processing_job)
    db.commit()
    db.refresh(processing_job)
    
    # Start background processing
    background_tasks.add_task(process_project_reviews, project_id, job_id, options.dict())
    
    # Return the processing status response immediately
    return ProcessingStatusResponse.from_orm(processing_job)

@app.get("/api/v1/projects/{project_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(project_id: str, db: Session = Depends(get_db)):
    """Get the current processing status for a project."""
    # Get the most recent processing job
    job = db.query(ProcessingJob).filter(
        ProcessingJob.project_id == project_id
    ).order_by(ProcessingJob.started_at.desc()).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found for this project")
    
    # Add statistics if completed
    if job.status == "completed":
        project = db.query(Project).filter(Project.project_id == project_id).first()
        accepted_reviews = db.query(Review).filter(
            Review.project_id == project_id,
            Review.status == "accepted"
        ).count()
        
        artificial_reviews = db.query(Review).filter(
            Review.project_id == project_id,
            Review.is_artificial == True
        ).count()
        
        response = ProcessingStatusResponse.from_orm(job)
        response.statistics = {
            "total_reviews": project.review_count,
            "accepted_reviews": accepted_reviews,
            "artificial_reviews": artificial_reviews
        }
        return response
    else:
        return ProcessingStatusResponse.from_orm(job)

# Results APIs (existing, but enhanced with ontology information)

@app.get("/api/v1/projects/{project_id}/feedback", response_model=FeedbackResponse)
async def get_feedback_report(project_id: str, db: Session = Depends(get_db)):
    """Get the generated feedback report for a project."""
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the latest feedback report
    report = db.query(FeedbackReport).filter(
        FeedbackReport.project_id == project_id
    ).order_by(FeedbackReport.generated_at.desc()).first()
    
    if not report:
        raise HTTPException(
            status_code=404, 
            detail="No feedback report available. Please process the project reviews first."
        )
    
    # Build proper response
    return FeedbackResponse(
        project_id=report.project_id,
        project_name=project.name,
        generated_at=report.generated_at,
        feedback_scores=report.feedback_scores,
        overall_score=report.overall_score,
        final_review=report.final_review,
        domain_insights=report.domain_insights or {},
        recommendations=report.recommendations or [],
        meta_data=report.meta_data or {}
    )

@app.get("/api/v1/projects/{project_id}/feedback/visualization", response_model=VisualizationData)
async def get_visualization_data(project_id: str, db: Session = Depends(get_db)):
    """Get visualization data for the project feedback."""
    # Get the latest feedback report
    report = db.query(FeedbackReport).filter(
        FeedbackReport.project_id == project_id
    ).order_by(FeedbackReport.generated_at.desc()).first()
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No feedback report available. Please process the project reviews first."
        )
    
    # Get reviews for domain breakdown
    reviews = db.query(Review).filter(
        Review.project_id == project_id,
        Review.status == "accepted"
    ).all()
    
    # Get dimension names from ontology if available
    dimension_names = {}
    if global_ontology:
        try:
            dimensions = global_ontology.rdf_ontology.get_impact_dimensions()
            dimension_names = {dim["id"]: dim["name"] for dim in dimensions}
        except Exception as e:
            logger.warning(f"Could not get dimension names from ontology: {str(e)}")
    
    # Build visualization data
    viz_data = VisualizationData(
        radar_chart={
            "dimensions": [dimension_names.get(dim_id, dim_id.replace("_", " ").title()) 
                          for dim_id in report.feedback_scores.keys()],
            "scores": list(report.feedback_scores.values())
        },
        domain_breakdown=[],
        score_distribution={}
    )
    
    # Domain breakdown with ontology enhancement
    domain_stats = {}
    domain_names = {}
    if global_ontology:
        try:
            domains = global_ontology.rdf_ontology.get_domains()
            domain_names = {domain["id"]: domain["name"] for domain in domains}
        except Exception as e:
            logger.warning(f"Could not get domain names from ontology: {str(e)}")
    
    for review in reviews:
        if review.domain:
            domain_name = domain_names.get(review.domain, review.domain.capitalize())
            
            if review.domain not in domain_stats:
                domain_stats[review.domain] = {
                    "domain": domain_name,
                    "review_count": 0,
                    "artificial_count": 0,
                    "average_scores": {}
                }
            
            domain_stats[review.domain]["review_count"] += 1
            if review.is_artificial:
                domain_stats[review.domain]["artificial_count"] += 1
            
            # Add sentiment scores
            if review.sentiment_scores:
                for dim_id, score in review.sentiment_scores.items():
                    dim_name = dimension_names.get(dim_id, dim_id.replace("_", " ").title())
                    if dim_name not in domain_stats[review.domain]["average_scores"]:
                        domain_stats[review.domain]["average_scores"][dim_name] = []
                    domain_stats[review.domain]["average_scores"][dim_name].append(score)
    
    # Calculate averages
    for domain, stats in domain_stats.items():
        avg_scores = {}
        for dim, scores in stats["average_scores"].items():
            if scores:
                avg_scores[dim] = sum(scores) / len(scores)
        stats["average_scores"] = avg_scores
        viz_data.domain_breakdown.append(stats)
    
    # Score distribution
    score_ranges = {"1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0}
    for score in report.feedback_scores.values():
        if 1 <= score < 2:
            score_ranges["1-2"] += 1
        elif 2 <= score < 3:
            score_ranges["2-3"] += 1
        elif 3 <= score < 4:
            score_ranges["3-4"] += 1
        elif 4 <= score <= 5:
            score_ranges["4-5"] += 1
    
    viz_data.score_distribution = score_ranges
    
    return viz_data

@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    """Serve the web-based UI for the hackathon review system"""
    
    # The HTML content from the artifact above
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenGeneva Sparkboard - Ontology-Driven Review System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            color: #4A5568;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 700;
        }

        .header p {
            text-align: center;
            color: #666;
            font-size: 1.1em;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            color: #4A5568;
            margin-bottom: 10px;
            font-size: 1.8em;
        }

        .stat-card p {
            color: #666;
            font-size: 0.9em;
        }

        .tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            color: #666;
        }

        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .tab-content {
            display: none;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4A5568;
        }

        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #E2E8F0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: linear-gradient(135deg, #718096 0%, #4A5568 100%);
        }

        .btn-danger {
            background: linear-gradient(135deg, #FC8181 0%, #E53E3E 100%);
        }

        .project-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .project-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .project-title {
            font-size: 1.3em;
            font-weight: 700;
            color: #4A5568;
            margin-bottom: 5px;
        }

        .project-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-active {
            background: #C6F6D5;
            color: #22543D;
        }

        .status-processing {
            background: #FEFCBF;
            color: #744210;
        }

        .status-completed {
            background: #BEE3F8;
            color: #2A4365;
        }

        .processing-status {
            background: #F7FAFC;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #E2E8F0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }

        .radar-chart-container {
            display: flex;
            justify-content: center;
            margin: 20px 0;
            padding: 20px;
            background: #F7FAFC;
            border-radius: 12px;
        }

        .feedback-section {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .domain-insights {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .domain-card {
            background: #F7FAFC;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background: #FED7D7;
            color: #C53030;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .success {
            background: #C6F6D5;
            color: #22543D;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .warning {
            background: #FEFCBF;
            color: #744210;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 1000;
        }

        .connection-online {
            background: #C6F6D5;
            color: #22543D;
        }

        .connection-offline {
            background: #FED7D7;
            color: #C53030;
        }

        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">🔍 Checking connection...</div>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>OpenGeneva Sparkboard: Ontology-Driven AI for Multi-Perspective Peer Review in Hackathons</h1>
        </div>

        <!-- Ontology Statistics -->
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card">
                <h3 id="domains-count">-</h3>
                <p>Knowledge Domains</p>
            </div>
            <div class="stat-card">
                <h3 id="dimensions-count">-</h3>
                <p>Evaluation Dimensions</p>
            </div>
            <div class="stat-card">
                <h3 id="levels-count">-</h3>
                <p>Expertise Levels</p>
            </div>
            <div class="stat-card">
                <h3 id="project-types-count">-</h3>
                <p>Project Types</p>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('projects')">📁 Projects</button>
            <button class="tab" onclick="showTab('reviews')">📝 Reviews</button>
            <button class="tab" onclick="showTab('ontology')">🧠 Ontology</button>
            <button class="tab" onclick="showTab('results')">📊 Results</button>
        </div>

        <!-- Projects Tab -->
        <div id="projects-tab" class="tab-content active">
            <div class="grid-2">
                <div>
                    <h2>📁 Create New Project</h2>
                    <form id="project-form">
                        <div class="form-group">
                            <label for="hackathon-id">Hackathon ID</label>
                            <input type="text" id="hackathon-id" placeholder="e.g., MedTech2025" required>
                        </div>
                        <div class="form-group">
                            <label for="project-name">Project Name</label>
                            <input type="text" id="project-name" placeholder="Enter project name" required>
                        </div>
                        <div class="form-group">
                            <label for="project-description">Project Description</label>
                            <textarea id="project-description" placeholder="Describe your project (min 50 characters)" required minlength="50"></textarea>
                            <small>Character count: <span id="description-count">0</span>/50 minimum</small>
                        </div>
                        <div class="form-group">
                            <label for="work-done">Work Done So Far</label>
                            <textarea id="work-done" placeholder="Describe what you've accomplished (min 50 characters)" required minlength="50"></textarea>
                            <small>Character count: <span id="work-done-count">0</span>/50 minimum</small>
                        </div>
                        <button type="submit" class="btn">🚀 Create Project</button>
                    </form>
                </div>
                <div>
                    <h2>📋 Your Projects</h2>
                    <button onclick="refreshProjects()" class="btn btn-secondary" style="margin-bottom: 15px;">🔄 Refresh Projects</button>
                    <div id="projects-list">
                        <div class="loading"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reviews Tab -->
        <div id="reviews-tab" class="tab-content">
            <div class="grid-2">
                <div>
                    <h2>📝 Submit Review</h2>
                    <form id="review-form">
                        <div class="form-group">
                            <label for="review-project">Select Project</label>
                            <select id="review-project" required>
                                <option value="">Select a project...</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="reviewer-name">Reviewer Name</label>
                            <input type="text" id="reviewer-name" placeholder="Your name" required>
                        </div>
                        <div class="form-group">
                            <label for="review-text">Review Text</label>
                            <textarea id="review-text" placeholder="Provide detailed feedback (min 50 characters)" required minlength="50"></textarea>
                            <small>Character count: <span id="review-text-count">0</span>/50 minimum</small>
                        </div>
                        <div class="form-group">
                            <label for="confidence-score">Confidence Score (0-100)</label>
                            <input type="number" id="confidence-score" min="0" max="100" placeholder="85" required>
                            <small>How confident are you in your expertise for this project?</small>
                        </div>
                        <div class="form-group">
                            <label for="linkedin-link">LinkedIn Profile (Optional)</label>
                            <input type="url" id="linkedin-link" placeholder="https://linkedin.com/in/yourprofile">
                        </div>
                        <button type="submit" class="btn">📝 Submit Review</button>
                    </form>
                </div>
                <div>
                    <h2>🔄 Process Reviews</h2>
                    <div class="form-group">
                        <label for="process-project">Select Project</label>
                        <select id="process-project">
                            <option value="">Select a project...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="generate-artificial" checked>
                            Generate AI reviews for missing domains
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="force-reprocess">
                            Force reprocess (overwrite existing results)
                        </label>
                    </div>
                    <button onclick="startProcessing()" class="btn">🤖 Start AI Analysis</button>
                    
                    <div id="processing-status" style="display:none;" class="processing-status">
                        <h3>Processing Status</h3>
                        <div id="status-text">Initializing...</div>
                        <div class="progress-bar">
                            <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div id="status-details"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Ontology Tab -->
        <div id="ontology-tab" class="tab-content">
            <div class="grid-2">
                <div>
                    <h2>🧠 Add New Domain</h2>
                    <form id="domain-form">
                        <div class="form-group">
                            <label for="domain-id">Domain ID</label>
                            <input type="text" id="domain-id" placeholder="e.g., sustainability" required pattern="[a-z_]+">
                            <small>Use lowercase letters and underscores only</small>
                        </div>
                        <div class="form-group">
                            <label for="domain-name">Domain Name</label>
                            <input type="text" id="domain-name" placeholder="Environmental Sustainability" required>
                        </div>
                        <div class="form-group">
                            <label for="domain-description">Description</label>
                            <textarea id="domain-description" placeholder="Describe the domain expertise" required minlength="20"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="domain-keywords">Keywords (comma-separated)</label>
                            <input type="text" id="domain-keywords" placeholder="sustainability, green, eco-friendly" required>
                            <small>Separate keywords with commas</small>
                        </div>
                        <button type="submit" class="btn">➕ Add Domain</button>
                    </form>
                </div>
                <div>
                    <h2>📊 Current Domains</h2>
                    <button onclick="loadDomains()" class="btn btn-secondary" style="margin-bottom: 15px;">🔄 Refresh Domains</button>
                    <div id="domains-list">
                        <div class="loading"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Results Tab -->
        <div id="results-tab" class="tab-content">
            <div>
                <h2>📊 Project Results</h2>
                <div class="form-group">
                    <label for="results-project">Select Project</label>
                    <select id="results-project" onchange="loadResults()">
                        <option value="">Select a project...</option>
                    </select>
                </div>
                <div id="results-content">
                    <p>Select a project to view its feedback report and analysis results.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const API_BASE_URL = window.location.origin; // Use same origin as the web page
        const POLLING_INTERVAL = 3000; // 3 seconds
        const MAX_POLLING_ATTEMPTS = 100; // 5 minutes maximum

        // Global variables
        let projects = [];
        let domains = [];
        let currentProcessingJob = null;
        let pollingAttempts = 0;
        let connectionStatus = 'checking';

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            setupCharacterCounters();
            checkAPIConnection();
            loadOntologyStats();
            loadAllProjects();
            loadDomains();

            // Form event listeners
            document.getElementById('project-form').addEventListener('submit', createProject);
            document.getElementById('review-form').addEventListener('submit', submitReview);
            document.getElementById('domain-form').addEventListener('submit', addDomain);

            // Auto-save form data
            setupFormAutoSave();
        });

        // Check API connection
        async function checkAPIConnection() {
            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                if (response.ok) {
                    setConnectionStatus('online');
                } else {
                    setConnectionStatus('offline');
                }
            } catch (error) {
                setConnectionStatus('offline');
            }
        }

        // Set connection status
        function setConnectionStatus(status) {
            connectionStatus = status;
            const statusElement = document.getElementById('connection-status');
            
            if (status === 'online') {
                statusElement.textContent = '🟢 Connected';
                statusElement.className = 'connection-status connection-online';
            } else {
                statusElement.textContent = '🔴 Disconnected';
                statusElement.className = 'connection-status connection-offline';
            }
            
            // Auto-hide after 3 seconds if online
            if (status === 'online') {
                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 3000);
            }
        }

        // Setup character counters
        function setupCharacterCounters() {
            const textareas = [
                { id: 'project-description', counterId: 'description-count' },
                { id: 'work-done', counterId: 'work-done-count' },
                { id: 'review-text', counterId: 'review-text-count' }
            ];

            textareas.forEach(({ id, counterId }) => {
                const textarea = document.getElementById(id);
                const counter = document.getElementById(counterId);
                
                textarea.addEventListener('input', () => {
                    const count = textarea.value.length;
                    counter.textContent = count;
                    counter.style.color = count >= 50 ? '#22543D' : '#C53030';
                });
            });
        }

        // Setup form auto-save
        function setupFormAutoSave() {
            const forms = ['project-form', 'review-form', 'domain-form'];
            
            forms.forEach(formId => {
                const form = document.getElementById(formId);
                const inputs = form.querySelectorAll('input, textarea, select');
                
                inputs.forEach(input => {
                    // Load saved data
                    const savedValue = localStorage.getItem(`${formId}-${input.id}`);
                    if (savedValue && input.type !== 'password') {
                        input.value = savedValue;
                    }
                    
                    // Save on change
                    input.addEventListener('input', () => {
                        localStorage.setItem(`${formId}-${input.id}`, input.value);
                    });
                });
            });
        }

        // Clear form auto-save data
        function clearFormAutoSave(formId) {
            const form = document.getElementById(formId);
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                localStorage.removeItem(`${formId}-${input.id}`);
            });
        }

        // API request helper
        async function apiRequest(endpoint, options = {}) {
            try {
                const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });

                if (!response.ok) {
                    const error = await response.json().catch(() => ({ detail: 'Network error' }));
                    throw new Error(formatErrorMessage(error, response.status));
                }

                return await response.json();
            } catch (error) {
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    setConnectionStatus('offline');
                    throw new Error('Cannot connect to API server. Please check if the server is running.');
                }
                throw error;
            }
        }

        // Format error messages
        function formatErrorMessage(error, status) {
            if (status === 422 && Array.isArray(error.detail)) {
                const validationErrors = error.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                return `Validation error: ${validationErrors}`;
            }
            return error.detail || error.message || 'Unknown error';
        }

        // Tab Management
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');

            // Load data when switching tabs
            if (tabName === 'projects') {
                loadAllProjects(); // Refresh projects to show updated review counts
            } else if (tabName === 'reviews') {
                populateProjectSelects();
            } else if (tabName === 'results') {
                populateResultsProjectSelect();
            } else if (tabName === 'ontology') {
                loadDomains(); // Refresh domains when switching to ontology tab
            }
        }

        // Load ontology statistics
        async function loadOntologyStats() {
            try {
                const stats = await apiRequest('/api/v1/ontology/stats');
                
                document.getElementById('domains-count').textContent = stats.total_domains;
                document.getElementById('dimensions-count').textContent = stats.total_dimensions;
                document.getElementById('levels-count').textContent = stats.total_expertise_levels;
                document.getElementById('project-types-count').textContent = stats.total_project_types;
            } catch (error) {
                console.error('Error loading ontology stats:', error);
                showMessage('Failed to load ontology statistics: ' + error.message, 'error');
            }
        }

        // Load all projects (mock implementation since endpoint doesn't exist)
        async function loadAllProjects() {
            const projectsList = document.getElementById('projects-list');
            
            // For now, show stored projects from localStorage
            const storedProjects = JSON.parse(localStorage.getItem('created_projects') || '[]');
            projects = storedProjects;
            
            if (projects.length === 0) {
                projectsList.innerHTML = '<p>No projects found. Create a new project to get started.</p>';
            } else {
                projectsList.innerHTML = '';
                
                // Try to fetch updated data for each project from API
                await updateProjectsFromAPI();
                
                projects.forEach(project => {
                    addProjectToList(project, false);
                });
            }
        }

        // Update projects data from API
        async function updateProjectsFromAPI() {
            const updatePromises = projects.map(async (project) => {
                try {
                    const updatedProject = await apiRequest(`/api/v1/projects/${project.project_id}`);
                    // Update the project data with latest from API
                    Object.assign(project, updatedProject);
                } catch (error) {
                    // If we can't fetch the project, keep the local data
                    console.warn(`Could not update project ${project.project_id}:`, error.message);
                }
            });
            
            try {
                await Promise.all(updatePromises);
                // Save updated projects back to localStorage
                localStorage.setItem('created_projects', JSON.stringify(projects));
            } catch (error) {
                console.warn('Some projects could not be updated from API');
            }
        }

        // Load domains
        async function loadDomains() {
            try {
                domains = await apiRequest('/api/v1/ontology/domains');
                
                const domainsList = document.getElementById('domains-list');
                domainsList.innerHTML = '';
                
                domains.forEach(domain => {
                    const domainCard = document.createElement('div');
                    domainCard.className = 'domain-card';
                    domainCard.innerHTML = `
                        <h3>${domain.name}</h3>
                        <p><strong>ID:</strong> ${domain.id}</p>
                        <p><strong>Description:</strong> ${domain.description}</p>
                        <p><strong>Keywords:</strong> ${domain.keywords.join(', ')}</p>
                    `;
                    domainsList.appendChild(domainCard);
                });
            } catch (error) {
                console.error('Error loading domains:', error);
                showMessage('Failed to load domains: ' + error.message, 'error');
            }
        }

        // Create project
        async function createProject(event) {
            event.preventDefault();
            
            const submitBtn = event.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Creating...';
            
            try {
                const projectData = {
                    hackathon_id: document.getElementById('hackathon-id').value,
                    name: document.getElementById('project-name').value,
                    description: document.getElementById('project-description').value,
                    work_done: document.getElementById('work-done').value,
                    meta_data: {}
                };

                const project = await apiRequest('/api/v1/projects', {
                    method: 'POST',
                    body: JSON.stringify(projectData)
                });

                showMessage('Project created successfully!', 'success');
                
                // Add to projects list
                addProjectToList(project, true);
                
                // Reset form and clear auto-save
                event.target.reset();
                clearFormAutoSave('project-form');
                
                // Update character counters
                document.getElementById('description-count').textContent = '0';
                document.getElementById('work-done-count').textContent = '0';
                
            } catch (error) {
                showMessage('Error creating project: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 Create Project';
            }
        }

        // Refresh projects with loading state
        async function refreshProjects() {
            const projectsList = document.getElementById('projects-list');
            const refreshBtn = document.querySelector('button[onclick="refreshProjects()"]');
            
            // Show loading state
            projectsList.innerHTML = '<div class="loading"></div>';
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="loading"></span> Refreshing...';
            
            try {
                await loadAllProjects();
                showMessage('Projects refreshed successfully!', 'success');
            } catch (error) {
                showMessage('Error refreshing projects: ' + error.message, 'error');
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 Refresh Projects';
            }
        }

        // Update project review count locally
        function updateProjectReviewCount(projectId) {
            // Find and update the project in the projects array
            const projectIndex = projects.findIndex(p => p.project_id === projectId);
            if (projectIndex !== -1) {
                projects[projectIndex].review_count += 1;
                projects[projectIndex].updated_at = new Date().toISOString();
                
                // Update localStorage
                localStorage.setItem('created_projects', JSON.stringify(projects));
                
                // Update the specific project card in the UI
                updateProjectCardInUI(projects[projectIndex]);
                
                // Also refresh the project selects in other tabs
                populateProjectSelects();
                populateResultsProjectSelect();
            }
        }

        // Update a specific project card in the UI
        function updateProjectCardInUI(project) {
            const projectCard = document.querySelector(`[data-project-id="${project.project_id}"]`);
            if (projectCard) {
                // Update the review count
                const reviewCountElement = projectCard.querySelector('.review-count');
                if (reviewCountElement) {
                    reviewCountElement.textContent = project.review_count;
                    
                    // Add a visual highlight to show it was updated
                    reviewCountElement.style.backgroundColor = '#C6F6D5';
                    reviewCountElement.style.padding = '2px 6px';
                    reviewCountElement.style.borderRadius = '4px';
                    reviewCountElement.style.fontWeight = 'bold';
                    
                    // Remove the highlight after 3 seconds
                    setTimeout(() => {
                        reviewCountElement.style.backgroundColor = '';
                        reviewCountElement.style.padding = '';
                        reviewCountElement.style.borderRadius = '';
                        reviewCountElement.style.fontWeight = '';
                    }, 3000);
                }
                
                // Add updated indicator
                const projectHeader = projectCard.querySelector('.project-header div');
                const existingIndicator = projectHeader.querySelector('.updated-indicator');
                if (!existingIndicator) {
                    const updatedIndicator = document.createElement('span');
                    updatedIndicator.className = 'updated-indicator';
                    updatedIndicator.style.cssText = 'color: #22543D; font-size: 0.8em; margin-left: 10px;';
                    updatedIndicator.textContent = '✨ Updated';
                    projectHeader.appendChild(updatedIndicator);
                    
                    // Remove the indicator after 10 seconds
                    setTimeout(() => {
                        if (updatedIndicator.parentNode) {
                            updatedIndicator.parentNode.removeChild(updatedIndicator);
                        }
                    }, 10000);
                }
            }
        }

        // Add project to list
        function addProjectToList(project, isNew = false) {
            const projectsList = document.getElementById('projects-list');
            
            // Clear "no projects" message if it exists
            if (projectsList.innerHTML.includes('No projects found')) {
                projectsList.innerHTML = '';
            }
            
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card';
            projectCard.setAttribute('data-project-id', project.project_id);
            
            // Check if this project was recently updated (within last 10 seconds)
            const isRecentlyUpdated = project.updated_at && 
                new Date(project.updated_at) > new Date(Date.now() - 10000);
            
            projectCard.innerHTML = `
                <div class="project-header">
                    <div>
                        <div class="project-title">${project.name}</div>
                        <span class="project-status status-${project.status}">${project.status}</span>
                        ${isRecentlyUpdated ? '<span style="color: #22543D; font-size: 0.8em;">✨ Updated</span>' : ''}
                    </div>
                </div>
                <p><strong>Hackathon:</strong> ${project.hackathon_id}</p>
                <p><strong>Created:</strong> ${new Date(project.created_at).toLocaleDateString()}</p>
                <p><strong>Reviews:</strong> <span class="review-count">${project.review_count}</span></p>
                <p><strong>Description:</strong> ${project.description.substring(0, 100)}...</p>
            `;
            
            if (isNew) {
                projectsList.insertBefore(projectCard, projectsList.firstChild);
            } else {
                projectsList.appendChild(projectCard);
            }
            
            // Add to projects array if not already there
            if (!projects.find(p => p.project_id === project.project_id)) {
                projects.push(project);
                
                // Store in localStorage
                localStorage.setItem('created_projects', JSON.stringify(projects));
            }
        }

        // Populate project select dropdowns
        function populateProjectSelects() {
            const reviewProjectSelect = document.getElementById('review-project');
            const processProjectSelect = document.getElementById('process-project');
            
            [reviewProjectSelect, processProjectSelect].forEach(select => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Select a project...</option>';
                
                projects.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.project_id;
                    option.textContent = project.name;
                    select.appendChild(option);
                });
                
                // Restore previous selection
                if (currentValue) {
                    select.value = currentValue;
                }
            });
        }

        // Populate results project select
        function populateResultsProjectSelect() {
            const resultsProjectSelect = document.getElementById('results-project');
            const currentValue = resultsProjectSelect.value;
            
            resultsProjectSelect.innerHTML = '<option value="">Select a project...</option>';
            
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.project_id;
                option.textContent = project.name;
                resultsProjectSelect.appendChild(option);
            });
            
            // Restore previous selection
            if (currentValue) {
                resultsProjectSelect.value = currentValue;
            }
        }

        // Submit review
        async function submitReview(event) {
            event.preventDefault();
            
            const submitBtn = event.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Submitting...';
            
            try {
                const projectId = document.getElementById('review-project').value;
                const reviewData = {
                    reviewer_name: document.getElementById('reviewer-name').value,
                    text_review: document.getElementById('review-text').value,
                    confidence_score: parseInt(document.getElementById('confidence-score').value),
                    links: {},
                    meta_data: {}
                };

                const linkedinLink = document.getElementById('linkedin-link').value;
                if (linkedinLink) {
                    reviewData.links.linkedin = linkedinLink;
                }

                await apiRequest(`/api/v1/projects/${projectId}/reviews`, {
                    method: 'POST',
                    body: JSON.stringify(reviewData)
                });

                // Update the project's review count locally
                updateProjectReviewCount(projectId);

                showMessage('Review submitted successfully!', 'success');
                event.target.reset();
                clearFormAutoSave('review-form');
                document.getElementById('review-text-count').textContent = '0';
                
            } catch (error) {
                showMessage('Error submitting review: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '📝 Submit Review';
            }
        }

        // Start processing
        async function startProcessing() {
            const projectId = document.getElementById('process-project').value;
            if (!projectId) {
                showMessage('Please select a project', 'error');
                return;
            }

            const options = {
                generate_artificial_reviews: document.getElementById('generate-artificial').checked,
                force_reprocess: document.getElementById('force-reprocess').checked
            };

            try {
                const job = await apiRequest(`/api/v1/projects/${projectId}/process`, {
                    method: 'POST',
                    body: JSON.stringify(options)
                });

                currentProcessingJob = job;
                pollingAttempts = 0;
                
                document.getElementById('processing-status').style.display = 'block';
                showMessage('Processing started!', 'success');
                
                // Start polling for status
                pollProcessingStatus(projectId);
            } catch (error) {
                showMessage('Error starting processing: ' + error.message, 'error');
            }
        }

        // Poll processing status
        async function pollProcessingStatus(projectId) {
            if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
                showMessage('Processing timeout - stopped monitoring. Please check status manually.', 'warning');
                return;
            }

            pollingAttempts++;

            try {
                const status = await apiRequest(`/api/v1/projects/${projectId}/status`);
                
                updateProcessingUI(status);
                
                if (status.status === 'processing' || status.status === 'pending') {
                    setTimeout(() => pollProcessingStatus(projectId), POLLING_INTERVAL);
                } else {
                    // Processing completed or failed
                    if (status.status === 'completed') {
                        showMessage('Processing completed successfully!', 'success');
                    } else {
                        showMessage('Processing failed: ' + (status.errors.join(', ') || 'Unknown error'), 'error');
                    }
                    pollingAttempts = 0;
                }
            } catch (error) {
                console.error('Error polling status:', error);
                showMessage('Error checking processing status: ' + error.message, 'error');
            }
        }

        // Update processing UI
        function updateProcessingUI(status) {
            const statusText = document.getElementById('status-text');
            const progressFill = document.getElementById('progress-fill');
            const statusDetails = document.getElementById('status-details');
            
            statusText.textContent = `Status: ${status.status} - ${status.progress.current_step}`;
            
            const progress = (status.progress.steps_completed / status.progress.total_steps) * 100;
            progressFill.style.width = progress + '%';
            
            statusDetails.innerHTML = `
                <p><strong>Steps:</strong> ${status.progress.steps_completed}/${status.progress.total_steps}</p>
                <p><strong>Polling attempt:</strong> ${pollingAttempts}/${MAX_POLLING_ATTEMPTS}</p>
                ${status.statistics ? `
                    <p><strong>Total Reviews:</strong> ${status.statistics.total_reviews}</p>
                    <p><strong>Accepted Reviews:</strong> ${status.statistics.accepted_reviews}</p>
                    <p><strong>AI Reviews:</strong> ${status.statistics.artificial_reviews}</p>
                ` : ''}
                ${status.errors.length > 0 ? `<p class="error">Errors: ${status.errors.join(', ')}</p>` : ''}
            `;
        }

        // Add domain
        async function addDomain(event) {
            event.preventDefault();
            
            const submitBtn = event.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Adding...';
            
            try {
                const domainData = {
                    id: document.getElementById('domain-id').value,
                    name: document.getElementById('domain-name').value,
                    description: document.getElementById('domain-description').value,
                    keywords: document.getElementById('domain-keywords').value.split(',').map(k => k.trim()).filter(k => k),
                    relevant_dimensions: []
                };

                await apiRequest('/api/v1/ontology/domains', {
                    method: 'POST',
                    body: JSON.stringify(domainData)
                });

                showMessage('Domain added successfully!', 'success');
                event.target.reset();
                clearFormAutoSave('domain-form');
                loadDomains();
                loadOntologyStats();
            } catch (error) {
                showMessage('Error adding domain: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '➕ Add Domain';
            }
        }

        // Load results
        async function loadResults() {
            const projectId = document.getElementById('results-project').value;
            const resultsContent = document.getElementById('results-content');
            
            if (!projectId) {
                resultsContent.innerHTML = '<p>Select a project to view its feedback report and analysis results.</p>';
                return;
            }

            resultsContent.innerHTML = '<div class="loading"></div>';

            try {
                const feedback = await apiRequest(`/api/v1/projects/${projectId}/feedback`);
                displayResults(feedback);
            } catch (error) {
                if (error.message.includes('404')) {
                    resultsContent.innerHTML = '<p class="warning">No feedback report available. Please process the project reviews first.</p>';
                } else {
                    resultsContent.innerHTML = `<p class="error">Error loading results: ${error.message}</p>`;
                }
            }
        }

        // Display results
        function displayResults(feedback) {
            const resultsContent = document.getElementById('results-content');
            
            // Create scores HTML
            const scoresHtml = Object.entries(feedback.feedback_scores)
                .map(([dim, score]) => `
                    <div class="domain-card">
                        <h4>${dim.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                        <div style="font-size: 1.5em; font-weight: bold; color: ${getScoreColor(score)}">${score}/5.0</div>
                    </div>
                `).join('');

            // Create domain insights HTML
            const domainsHtml = Object.entries(feedback.domain_insights)
                .map(([domainId, insight]) => `
                    <div class="domain-card">
                        <h4>${insight.domain_name}</h4>
                        <p><strong>Reviews:</strong> ${insight.review_count} (${insight.artificial_count} AI)</p>
                        ${insight.key_points.length > 0 ? `<p><strong>Strengths:</strong> ${insight.key_points.join(', ')}</p>` : ''}
                        ${insight.concerns.length > 0 ? `<p><strong>Concerns:</strong> ${insight.concerns.join(', ')}</p>` : ''}
                    </div>
                `).join('');

            resultsContent.innerHTML = `
                <div class="feedback-section">
                    <h3>📊 Overall Score: ${feedback.overall_score}/5.0</h3>
                    <p><strong>Generated:</strong> ${new Date(feedback.generated_at).toLocaleString()}</p>
                    
                    <h4>Dimension Scores</h4>
                    <div class="domain-insights">
                        ${scoresHtml}
                    </div>
                    
                    <h4>Domain Insights</h4>
                    <div class="domain-insights">
                        ${domainsHtml}
                    </div>
                    
                    <h4>📝 Synthesized Review</h4>
                    <div class="feedback-section">
                        <div style="white-space: pre-line; line-height: 1.6;">${feedback.final_review}</div>
                    </div>
                    
                    <h4>💡 Recommendations</h4>
                    <ul>
                        ${feedback.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                    
                    <h4>📈 Processing Statistics</h4>
                    <div class="domain-insights">
                        <div class="domain-card">
                            <p><strong>Total Reviews:</strong> ${feedback.meta_data.total_reviews}</p>
                            <p><strong>Human Reviews:</strong> ${feedback.meta_data.human_reviews}</p>
                            <p><strong>AI Reviews:</strong> ${feedback.meta_data.artificial_reviews}</p>
                            <p><strong>Processing Time:</strong> ${feedback.meta_data.processing_time_seconds}s</p>
                        </div>
                        <div class="domain-card">
                            <p><strong>Domains Used:</strong> ${feedback.meta_data.ontology_stats.domains_used}</p>
                            <p><strong>Available Domains:</strong> ${feedback.meta_data.ontology_stats.total_domains_available}</p>
                            <p><strong>Dimensions Evaluated:</strong> ${feedback.meta_data.ontology_stats.dimensions_evaluated}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // Get color based on score
        function getScoreColor(score) {
            if (score >= 4.0) return '#22543D';
            if (score >= 3.0) return '#744210';
            return '#C53030';
        }

        // Show message
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            
            // Insert at the top of the current tab
            const activeTab = document.querySelector('.tab-content.active');
            activeTab.insertBefore(messageDiv, activeTab.firstChild);
            
            // Remove after 5 seconds
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 5000);
        }

        // Utility function to debounce API calls
        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    </script>
</body>
</html>
    '''
    
    return HTMLResponse(content=html_content)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with ontology status"""
    ontology_status = "available" if global_ontology else "unavailable"
    ontology_info = {}
    
    if global_ontology:
        try:
            stats = global_ontology.rdf_ontology._get_ontology_stats() if hasattr(global_ontology.rdf_ontology, '_get_ontology_stats') else {}
            ontology_info = {
                "domains": len(global_ontology.get_domains()),
                "provider": "RDF/TTL",
                "backend": "rdflib"
            }
        except Exception as e:
            ontology_status = "error"
            ontology_info = {"error": str(e)}
    
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "ontology_status": ontology_status,
        "ontology_info": ontology_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
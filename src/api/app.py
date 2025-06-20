"""
Updated REST API implementation with RDF ontology management capabilities.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
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
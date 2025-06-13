"""
REST API implementation for the Ontology-Driven Hackathon Review System
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

from database import init_db, get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from models import (
    Project, Review, ProcessingJob, FeedbackReport,
    ProjectCreate, ProjectUpdate, ReviewCreate,
    ProcessOptions, ProjectResponse, ReviewResponse,
    ProcessingStatusResponse, FeedbackResponse, VisualizationData
)
from processing import process_project_reviews
from scalar_fastapi import get_scalar_api_reference

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

# Create FastAPI app
app = FastAPI(
    title="Ontology-Driven Hackathon Review API",
    description="AI-powered multi-perspective peer review system for hackathon projects",
    version="1.0.0",
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

# API Documentation endpoints
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API documentation links"""
    return {
        "message": "Ontology-Driven Hackathon Review API",
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

# Project Management APIs

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
        
        db_project = Project(
            project_id=project_id,
            hackathon_id=project.hackathon_id,
            name=project.name,
            description=project.description,
            work_done=project.work_done,
            meta_data=project.meta_data,
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

# Review Management APIs

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

# Processing APIs

@app.post("/api/v1/projects/{project_id}/process", status_code=202)
async def start_processing(
    project_id: str, 
    options: ProcessOptions,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start or restart the review analysis process for a project.
    
    This endpoint is idempotent - calling it multiple times will not create duplicate jobs
    unless force_reprocess is set to true.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
            "total_steps": 6
        },
        options=options.dict()
    )
    
    db.add(processing_job)
    db.commit()
    db.refresh(processing_job)
    
    # Start background processing
    background_tasks.add_task(process_project_reviews, project_id, job_id, options.dict())
    
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
    response = ProcessingStatusResponse.from_orm(job)
    
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
        
        response.statistics = {
            "total_reviews": project.review_count,
            "accepted_reviews": accepted_reviews,
            "artificial_reviews": artificial_reviews
        }
    
    return response

# Results APIs

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
    
    # Build visualization data
    viz_data = VisualizationData(
        radar_chart={
            "dimensions": list(report.feedback_scores.keys()),
            "scores": list(report.feedback_scores.values())
        },
        domain_breakdown=[],
        score_distribution={}
    )
    
    # Domain breakdown
    domain_stats = {}
    for review in reviews:
        if review.domain:
            if review.domain not in domain_stats:
                domain_stats[review.domain] = {
                    "domain": review.domain.capitalize(),
                    "review_count": 0,
                    "artificial_count": 0,
                    "average_scores": {}
                }
            
            domain_stats[review.domain]["review_count"] += 1
            if review.is_artificial:
                domain_stats[review.domain]["artificial_count"] += 1
            
            # Add sentiment scores
            if review.sentiment_scores:
                for dim, score in review.sentiment_scores.items():
                    if dim not in domain_stats[review.domain]["average_scores"]:
                        domain_stats[review.domain]["average_scores"][dim] = []
                    domain_stats[review.domain]["average_scores"][dim].append(score)
    
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
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
SQLAlchemy models and Pydantic schemas for the API
"""

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# SQLAlchemy Models

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String, primary_key=True, index=True)
    hackathon_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    work_done = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    status = Column(String, default="active")  # active, archived
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="project")
    processing_jobs = relationship("ProcessingJob", back_populates="project")
    feedback_reports = relationship("FeedbackReport", back_populates="project")

class Review(Base):
    __tablename__ = "reviews"
    
    review_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    reviewer_name = Column(String, nullable=False)
    text_review = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    links = Column(JSON, default={})
    meta_data = Column(JSON, default={})
    status = Column(String, default="submitted")  # submitted, accepted, rejected
    processing_status = Column(String, default="pending")
    submitted_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Analysis results
    domain = Column(String, nullable=True)
    expertise_level = Column(String, nullable=True)
    relevance_score = Column(Float, nullable=True)
    sentiment_scores = Column(JSON, nullable=True)
    is_artificial = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="reviews")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    progress = Column(JSON, default={})
    options = Column(JSON, default={})
    errors = Column(JSON, default=[])
    
    # Relationships
    project = relationship("Project", back_populates="processing_jobs")

class FeedbackReport(Base):
    __tablename__ = "feedback_reports"
    
    report_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    generated_at = Column(DateTime, server_default=func.now())
    feedback_scores = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)
    final_review = Column(Text, nullable=False)
    domain_insights = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    meta_data = Column(JSON, default={})
    
    # Relationships
    project = relationship("Project", back_populates="feedback_reports")

# Pydantic Schemas

class ProjectCreate(BaseModel):
    hackathon_id: str
    name: str
    description: str = Field(..., min_length=50, max_length=2000)
    work_done: str = Field(..., min_length=50, max_length=2000)
    meta_data: Optional[Dict[str, Any]] = {}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    work_done: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    project_id: str
    hackathon_id: str
    name: str
    description: str
    work_done: str
    status: str
    created_at: datetime
    updated_at: datetime
    review_count: int
    processing_status: str
    meta_data: Dict[str, Any]

class ReviewCreate(BaseModel):
    reviewer_name: str
    text_review: str = Field(..., min_length=50, max_length=2000)
    confidence_score: int = Field(..., ge=0, le=100)
    links: Optional[Dict[str, str]] = {}
    meta_data: Optional[Dict[str, Any]] = {}

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    review_id: str
    project_id: str
    reviewer_name: str
    confidence_score: int
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    domain: Optional[str] = None
    expertise_level: Optional[str] = None
    relevance_score: Optional[float] = None
    sentiment_scores: Optional[Dict[str, float]] = None
    is_artificial: bool
    text_review: Optional[str] = None  # Include in detailed view
    links: Optional[Dict[str, str]] = None

class ProcessOptions(BaseModel):
    generate_artificial_reviews: bool = True
    force_reprocess: bool = False

class ProcessingStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    project_id: str
    processing_job_id: str = Field(alias="job_id")
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any]
    statistics: Optional[Dict[str, int]] = None
    errors: List[str] = []

class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    project_id: str
    project_name: str
    generated_at: datetime
    feedback_scores: Dict[str, float]
    overall_score: float
    final_review: str
    domain_insights: Dict[str, Any]
    recommendations: List[str]
    meta_data: Dict[str, Any]

class VisualizationData(BaseModel):
    radar_chart: Dict[str, List[Any]]
    domain_breakdown: List[Dict[str, Any]]
    score_distribution: Dict[str, int]
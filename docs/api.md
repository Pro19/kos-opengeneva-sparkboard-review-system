# REST APIs

## Project Management APIs

### Create Project
```json
POST /api/v1/projects
Content-Type: application/json

{
  "hackathon_id": "MedTech2025",
  "name": "AI-Powered Health Assistant",
  "description": "Our AI-Powered Health Assistant aims to revolutionize chronic disease management...",
  "work_done": "We have developed a functional prototype that includes...",
  "metadata": {
    "team_size": 4,
    "category": "healthcare",
    "tags": ["AI", "healthcare", "chronic-disease"]
  }
}

Response: 201 Created
{
  "project_id": "proj_abc123",
  "hackathon_id": "MedTech2025",
  "name": "AI-Powered Health Assistant",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z",
  "review_count": 0,
  "processing_status": "pending"
}
```

### Get Project Details
```json
GET /api/v1/projects/{project_id}

Response: 200 OK
{
  "project_id": "proj_abc123",
  "hackathon_id": "MedTech2025",
  "name": "AI-Powered Health Assistant",
  "description": "...",
  "work_done": "...",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:22:00Z",
  "review_count": 3,
  "processing_status": "completed",
  "metadata": {...}
}
```

### Update Project
```json
PUT /api/v1/projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description...",
  "work_done": "Updated work done..."
}
```

## Review Management APIs

### Submit Review
```json
POST /api/v1/projects/{project_id}/reviews
Content-Type: application/json

{
  "reviewer_name": "Dr. Sarah Johnson",
  "text_review": "As an endocrinologist specializing in diabetes care...",
  "confidence_score": 95,
  "links": {
    "linkedin": "https://linkedin.com/in/sarahjohnson",
    "google_scholar": "https://scholar.google.com/...",
    "github": "https://github.com/sarahjohnson"
  },
  "metadata": {
    "expertise_areas": ["endocrinology", "diabetes", "clinical-research"]
  }
}

Response: 201 Created
{
  "review_id": "rev_xyz789",
  "project_id": "proj_abc123",
  "reviewer_name": "Dr. Sarah Johnson",
  "confidence_score": 95,
  "status": "submitted",
  "submitted_at": "2025-01-15T11:45:00Z",
  "processing_status": "pending"
}
```

### Get Project Reviews
```json
GET /api/v1/projects/{project_id}/reviews?limit=10&offset=0&status=all

Response: 200 OK
{
  "reviews": [
    {
      "review_id": "rev_xyz789",
      "reviewer_name": "Dr. Sarah Johnson",
      "confidence_score": 95,
      "status": "accepted",
      "submitted_at": "2025-01-15T11:45:00Z",
      "domain": "clinical",
      "expertise_level": "expert",
      "relevance_score": 0.95,
      "is_artificial": false
    }
  ],
  "total_count": 5,
  "accepted_count": 4,
  "artificial_count": 1,
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

### Get Specific Review
```json
GET /api/v1/projects/{project_id}/reviews/{review_id}

Response: 200 OK
{
  "review_id": "rev_xyz789",
  "project_id": "proj_abc123",
  "reviewer_name": "Dr. Sarah Johnson",
  "text_review": "As an endocrinologist specializing in diabetes care...",
  "confidence_score": 95,
  "links": {...},
  "status": "accepted",
  "submitted_at": "2025-01-15T11:45:00Z",
  "processed_at": "2025-01-15T12:30:00Z",
  "domain": "clinical",
  "expertise_level": "expert",
  "relevance_score": 0.95,
  "sentiment_scores": {
    "technical_feasibility": 4.2,
    "innovation": 4.5,
    "impact": 4.8,
    "implementation_complexity": 3.5,
    "scalability": 4.0,
    "return_on_investment": 4.3
  },
  "is_artificial": false
}
```

## Processing APIs

### Start Review Analysis (Idempotent)
```json
POST /api/v1/projects/{project_id}/process
Content-Type: application/json

{
  "options": {
    "generate_artificial_reviews": true,
    "force_reprocess": false
  }
}

Response: 202 Accepted
{
  "project_id": "proj_abc123",
  "processing_job_id": "job_def456",
  "status": "processing",
  "started_at": "2025-01-15T13:00:00Z",
  "progress": {
    "current_step": "analyzing_reviews",
    "steps_completed": 2,
    "total_steps": 6
  }
}
```

### Get Processing Status
```json
GET /api/v1/projects/{project_id}/status

Response: 200 OK
{
  "project_id": "proj_abc123",
  "processing_job_id": "job_def456",
  "status": "completed", // pending, processing, completed, failed
  "started_at": "2025-01-15T13:00:00Z",
  "completed_at": "2025-01-15T13:04:32Z",
  "progress": {
    "current_step": "completed",
    "steps_completed": 6,
    "total_steps": 6
  },
  "statistics": {
    "total_reviews": 5,
    "accepted_reviews": 4,
    "artificial_reviews": 1
  },
  "errors": []
}
```

## Results APIs

### Get Feedback Report
```json
GET /api/v1/projects/{project_id}/feedback

Response: 200 OK
{
  "project_id": "proj_abc123",
  "project_name": "AI-Powered Health Assistant",
  "generated_at": "2025-01-15T13:04:32Z",
  "feedback_scores": {
    "technical_feasibility": 4.1,
    "innovation": 4.3,
    "impact": 4.6,
    "implementation_complexity": 3.2,
    "scalability": 3.8,
    "return_on_investment": 4.0
  },
  "overall_score": 4.0,
  "final_review": "This AI-Powered Health Assistant presents impressive technical foundations...",
  "domain_insights": {
    "clinical": {
      "summary": "Strong clinical relevance with proper attention to medical workflows",
      "key_points": ["Addresses real clinical needs", "Proper medical validation"],
      "concerns": ["Integration complexity", "Regulatory considerations"]
    },
    "technical": {
      "summary": "Solid technical architecture with room for improvement",
      "key_points": ["Good use of AI/ML", "Scalable architecture"],
      "concerns": ["Performance optimization needed", "Security considerations"]
    }
  },
  "recommendations": [
    "Focus on regulatory compliance early",
    "Implement robust security measures",
    "Conduct larger-scale pilot studies"
  ],
  "metadata": {
    "total_reviews": 5,
    "artificial_reviews": 1,
    "processing_time_seconds": 272
  }
}
```

### Get Visualization Data
```json
GET /api/v1/projects/{project_id}/feedback/visualization

Response: 200 OK
{
  "radar_chart": {
    "dimensions": ["Technical Feasibility", "Innovation", "Impact", ...],
    "scores": [4.1, 4.3, 4.6, ...]
  },
  "domain_breakdown": [
    {
      "domain": "Clinical",
      "review_count": 2,
      "artificial_count": 0,
      "average_scores": {
        "impact": 4.8,
        "technical_feasibility": 4.2
      }
    }
  ],
  "score_distribution": {
    "1-2": 0,
    "2-3": 1,
    "3-4": 2,
    "4-5": 3
  }
}
```
# REST API Documentation

## Base URL
```
http://localhost:8000
```

## API Documentation Interfaces
- **Scalar UI (Recommended)**: `/scalar`
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

---

## Ontology Management APIs

### Get Ontology Statistics
Get comprehensive statistics about the current RDF ontology.

```http
GET /api/v1/ontology/stats
```

**Response: 200 OK**
```json
{
  "total_domains": 6,
  "total_dimensions": 6,
  "total_expertise_levels": 5,
  "total_project_types": 5,
  "domains": [
    "Technical",
    "Clinical", 
    "Administrative",
    "Business",
    "Design",
    "User Experience"
  ],
  "dimensions": [
    "Technical Feasibility",
    "Innovation",
    "Impact",
    "Implementation Complexity",
    "Scalability",
    "Return on Investment"
  ]
}
```

### List All Domains
Get all available domains from the RDF ontology.

```http
GET /api/v1/ontology/domains
```

**Response: 200 OK**
```json
[
  {
    "id": "clinical",
    "name": "Clinical",
    "description": "Medical or healthcare expertise related to patient care, diagnosis, or treatment",
    "keywords": [
      "medical",
      "healthcare", 
      "clinical",
      "patient",
      "diagnosis",
      "treatment"
    ],
    "subdomains": {
      "primary_care": {
        "name": "Primary Care",
        "keywords": ["general practice", "family medicine"]
      }
    }
  }
]
```

### Get Specific Domain
Retrieve detailed information about a specific domain.

```http
GET /api/v1/ontology/domains/{domain_id}
```

**Response: 200 OK**
```json
{
  "id": "technical",
  "name": "Technical",
  "description": "Expertise in programming, software engineering, hardware development, or technical implementation",
  "keywords": [
    "programming",
    "software",
    "hardware",
    "development",
    "engineering",
    "technical",
    "code"
  ],
  "subdomains": {
    "frontend": {
      "name": "Frontend Development",
      "keywords": ["UI", "UX", "web", "mobile", "frontend"]
    },
    "backend": {
      "name": "Backend Development", 
      "keywords": ["server", "database", "API", "backend"]
    }
  }
}
```

### Create New Domain
Add a new domain to the RDF ontology.

```http
POST /api/v1/ontology/domains
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "sustainability",
  "name": "Environmental Sustainability",
  "description": "Expertise in environmental sustainability, climate impact, and ecological considerations for technology projects",
  "keywords": [
    "sustainability",
    "climate",
    "ecology",
    "carbon footprint",
    "renewable",
    "green technology",
    "environmental"
  ],
  "relevant_dimensions": [
    "impact",
    "scalability", 
    "return_on_investment"
  ]
}
```

**Response: 201 Created**
```json
{
  "id": "sustainability",
  "name": "Environmental Sustainability",
  "description": "Expertise in environmental sustainability, climate impact, and ecological considerations for technology projects",
  "keywords": [
    "sustainability",
    "climate",
    "ecology",
    "carbon footprint",
    "renewable",
    "green technology",
    "environmental"
  ],
  "subdomains": {}
}
```

### List All Evaluation Dimensions
Get all available evaluation dimensions from the ontology.

```http
GET /api/v1/ontology/dimensions
```

**Response: 200 OK**
```json
[
  {
    "id": "technical_feasibility",
    "name": "Technical Feasibility",
    "description": "How technically feasible is the project to implement",
    "scale": {
      "1": "Extremely difficult or impossible with current technology",
      "2": "Substantial technical challenges", 
      "3": "Moderate technical challenges",
      "4": "Few technical challenges",
      "5": "Easily implementable with existing technology"
    }
  },
  {
    "id": "innovation",
    "name": "Innovation",
    "description": "How innovative or novel is the approach",
    "scale": {
      "1": "Not innovative, duplicates existing solutions",
      "2": "Minor improvements to existing approaches",
      "3": "Moderate innovation with some novel aspects", 
      "4": "Significantly innovative approach",
      "5": "Groundbreaking, completely novel approach"
    }
  }
]
```

### Create New Evaluation Dimension
Add a new evaluation dimension to the ontology.

```http
POST /api/v1/ontology/dimensions
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "environmental_impact",
  "name": "Environmental Impact",
  "description": "Measures the environmental impact and sustainability aspects of the solution",
  "scale": {
    "1": "Significant negative environmental impact",
    "2": "Some negative environmental impact with few mitigation measures",
    "3": "Neutral environmental impact with basic considerations", 
    "4": "Positive environmental contribution with sustainability features",
    "5": "Exceptional environmental benefits and comprehensive sustainability approach"
  }
}
```

**Response: 201 Created**
```json
{
  "id": "environmental_impact",
  "name": "Environmental Impact", 
  "description": "Measures the environmental impact and sustainability aspects of the solution",
  "scale": {
    "1": "Significant negative environmental impact",
    "2": "Some negative environmental impact with few mitigation measures",
    "3": "Neutral environmental impact with basic considerations",
    "4": "Positive environmental contribution with sustainability features", 
    "5": "Exceptional environmental benefits and comprehensive sustainability approach"
  }
}
```

### Get Expertise Levels
List all expertise levels defined in the ontology.

```http
GET /api/v1/ontology/expertise-levels
```

**Response: 200 OK**
```json
[
  {
    "id": "beginner",
    "name": "Beginner",
    "description": "Basic understanding of the domain",
    "confidence_range": [0, 40]
  },
  {
    "id": "expert", 
    "name": "Expert",
    "description": "Top-level expertise with mastery of the domain",
    "confidence_range": [96, 100]
  }
]
```

### Get Domain-Relevant Dimensions
Get evaluation dimensions that are relevant to a specific domain.

```http
GET /api/v1/ontology/domains/{domain_id}/relevant-dimensions
```

**Response: 200 OK**
```json
{
  "domain_id": "technical",
  "domain_name": "Technical",
  "relevant_dimensions": [
    {
      "id": "technical_feasibility",
      "name": "Technical Feasibility",
      "description": "How technically feasible is the project to implement",
      "scale": {
        "1": "Extremely difficult or impossible with current technology",
        "5": "Easily implementable with existing technology"
      }
    },
    {
      "id": "implementation_complexity", 
      "name": "Implementation Complexity",
      "description": "Complexity of implementing the solution in practice",
      "scale": {
        "1": "Extremely complex implementation",
        "5": "Very straightforward implementation"
      }
    }
  ]
}
```

### Reload Ontology
Reload the ontology from the TTL file (useful after manual ontology edits).

```http
POST /api/v1/ontology/reload
```

**Response: 200 OK**
```json
{
  "message": "Ontology reloaded successfully"
}
```

---

## Project Management APIs

### Create Project
Create a new project for review analysis.

```http
POST /api/v1/projects
Content-Type: application/json
```

**Request Body:**
```json
{
  "hackathon_id": "MedTech2025",
  "name": "AI-Powered Health Assistant",
  "description": "Our AI-Powered Health Assistant aims to revolutionize chronic disease management by creating a personalized, intelligent companion for patients with conditions like diabetes, hypertension, and heart disease. The system combines natural language processing, machine learning, and medical knowledge graphs to provide continuous monitoring, personalized guidance, and timely interventions.",
  "work_done": "We have developed a functional prototype that includes: 1) A core AI engine capable of processing natural language queries related to diabetes management, 2) Integration with Bluetooth-enabled glucose monitors and smart watches, 3) Basic anomaly detection algorithms for blood glucose level fluctuations, 4) A secure cloud infrastructure for data storage and processing, 5) A mobile app interface with medication tracking and basic visualization of health trends.",
  "meta_data": {
    "team_size": 4,
    "category": "healthcare",
    "tags": ["AI", "healthcare", "chronic-disease"]
  }
}
```

**Response: 201 Created**
```json
{
  "project_id": "proj_abc123",
  "hackathon_id": "MedTech2025", 
  "name": "AI-Powered Health Assistant",
  "description": "Our AI-Powered Health Assistant aims to revolutionize chronic disease management...",
  "work_done": "We have developed a functional prototype that includes...",
  "status": "active",
  "processing_status": "pending",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "review_count": 0,
  "meta_data": {
    "team_size": 4,
    "category": "healthcare", 
    "tags": ["AI", "healthcare", "chronic-disease"],
    "classified_project_type": "software"
  }
}
```

### Get Project Details
Retrieve detailed information about a specific project.

```http
GET /api/v1/projects/{project_id}
```

**Response: 200 OK**
```json
{
  "project_id": "proj_abc123",
  "hackathon_id": "MedTech2025",
  "name": "AI-Powered Health Assistant",
  "description": "Our AI-Powered Health Assistant aims to revolutionize chronic disease management...",
  "work_done": "We have developed a functional prototype that includes...",
  "status": "active",
  "processing_status": "completed",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:22:00Z",
  "review_count": 5,
  "meta_data": {
    "team_size": 4,
    "category": "healthcare",
    "classified_project_type": "software"
  }
}
```

### Update Project
Update an existing project's information.

```http
PUT /api/v1/projects/{project_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description...",
  "work_done": "Updated work done...",
  "meta_data": {
    "updated_field": "new_value"
  }
}
```

**Response: 200 OK**
```json
{
  "project_id": "proj_abc123",
  "name": "Updated Project Name",
  "description": "Updated description...",
  "work_done": "Updated work done...",
  "status": "active",
  "updated_at": "2025-01-15T15:30:00Z",
  "meta_data": {
    "updated_field": "new_value"
  }
}
```

---

## Review Management APIs

### Submit Review
Submit a review for a project.

```http
POST /api/v1/projects/{project_id}/reviews
Content-Type: application/json
```

**Request Body:**
```json
{
  "reviewer_name": "Dr. Sarah Johnson",
  "text_review": "As an endocrinologist specializing in diabetes care, I find this AI Health Assistant concept promising and addressing several critical gaps in chronic disease management. The integration of continuous monitoring with personalized guidance represents a significant advancement over traditional episodic care models. The project's approach to medication adherence tracking is particularly valuable, as non-adherence remains one of our biggest challenges in diabetes management.",
  "confidence_score": 95,
  "links": {
    "linkedin": "https://linkedin.com/in/sarahjohnson",
    "google_scholar": "https://scholar.google.com/citations?user=xyz",
    "github": "https://github.com/sarahjohnson"
  },
  "meta_data": {
    "expertise_areas": ["endocrinology", "diabetes", "clinical-research"],
    "review_context": "clinical_perspective"
  }
}
```

**Response: 201 Created**
```json
{
  "review_id": "rev_xyz789",
  "project_id": "proj_abc123",
  "reviewer_name": "Dr. Sarah Johnson",
  "confidence_score": 95,
  "status": "submitted",
  "processing_status": "pending",
  "submitted_at": "2025-01-15T11:45:00Z",
  "processed_at": null,
  "domain": null,
  "expertise_level": null,
  "relevance_score": null,
  "sentiment_scores": null,
  "is_artificial": false
}
```

### Get Project Reviews
Get all reviews for a project with filtering and pagination.

```http
GET /api/v1/projects/{project_id}/reviews?limit=10&offset=0&status=all
```

**Query Parameters:**
- `limit` (int, 1-100): Number of reviews to return (default: 10)
- `offset` (int, ≥0): Number of reviews to skip (default: 0)
- `status` (string): Filter by status - "all", "submitted", "accepted", "rejected" (default: "all")

**Response: 200 OK**
```json
{
  "reviews": [
    {
      "review_id": "rev_xyz789",
      "project_id": "proj_abc123",
      "reviewer_name": "Dr. Sarah Johnson",
      "confidence_score": 95,
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
        "return_on_investment": 4.3,
        "overall_sentiment": 4.3
      },
      "is_artificial": false
    },
    {
      "review_id": "rev_ai001",
      "project_id": "proj_abc123",
      "reviewer_name": "AI Business Expert",
      "confidence_score": 90,
      "status": "accepted",
      "submitted_at": "2025-01-15T13:15:00Z",
      "processed_at": "2025-01-15T13:15:00Z",
      "domain": "business",
      "expertise_level": "expert",
      "relevance_score": 0.87,
      "sentiment_scores": {
        "technical_feasibility": 3.8,
        "innovation": 4.0,
        "impact": 4.2,
        "return_on_investment": 4.5,
        "scalability": 3.9,
        "overall_sentiment": 4.1
      },
      "is_artificial": true
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
Get detailed information about a specific review.

```http
GET /api/v1/projects/{project_id}/reviews/{review_id}
```

**Response: 200 OK**
```json
{
  "review_id": "rev_xyz789",
  "project_id": "proj_abc123",
  "reviewer_name": "Dr. Sarah Johnson",
  "text_review": "As an endocrinologist specializing in diabetes care, I find this AI Health Assistant concept promising and addressing several critical gaps in chronic disease management...",
  "confidence_score": 95,
  "links": {
    "linkedin": "https://linkedin.com/in/sarahjohnson",
    "google_scholar": "https://scholar.google.com/citations?user=xyz"
  },
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
    "return_on_investment": 4.3,
    "overall_sentiment": 4.3
  },
  "is_artificial": false
}
```

---

## Processing APIs

### Start Review Analysis
Start or restart the RDF ontology-driven review analysis process for a project.

```http
POST /api/v1/projects/{project_id}/process
Content-Type: application/json
```

**Request Body:**
```json
{
  "generate_artificial_reviews": true,
  "force_reprocess": false
}
```

**Response: 202 Accepted**
```json
{
  "project_id": "proj_abc123",
  "processing_job_id": "job_def456", 
  "status": "processing",
  "started_at": "2025-01-15T13:00:00Z",
  "completed_at": null,
  "progress": {
    "current_step": "analyzing_reviews",
    "steps_completed": 2,
    "total_steps": 7
  },
  "statistics": null,
  "errors": []
}
```

### Get Processing Status
Get the current processing status for a project.

```http
GET /api/v1/projects/{project_id}/status
```

**Response: 200 OK**
```json
{
  "project_id": "proj_abc123",
  "processing_job_id": "job_def456",
  "status": "completed",
  "started_at": "2025-01-15T13:00:00Z", 
  "completed_at": "2025-01-15T13:04:32Z",
  "progress": {
    "current_step": "completed",
    "steps_completed": 7,
    "total_steps": 7
  },
  "statistics": {
    "total_reviews": 5,
    "accepted_reviews": 4,
    "artificial_reviews": 1
  },
  "errors": []
}
```

**Processing Steps:**
1. `loading_project` - Loading project data
2. `initializing_ontology` - Loading RDF ontology 
3. `analyzing_reviews` - Analyzing and classifying reviews
4. `classifying_reviewers` - Classifying reviewer domains
5. `generating_artificial_reviews` - Generating AI reviews for missing domains
6. `calculating_scores` - Calculating dimension scores
7. `generating_feedback` - Generating final feedback report

---

## Results APIs

### Get Feedback Report
Get the comprehensive feedback report generated by the ontology-driven analysis.

```http
GET /api/v1/projects/{project_id}/feedback
```

**Response: 200 OK**
```json
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
  "final_review": "This AI-Powered Health Assistant presents impressive technical foundations and addresses a critical need in chronic disease management. The integration of continuous monitoring with personalized guidance represents a significant advancement over traditional episodic care models.\n\n**Strengths:**\n- Strong clinical relevance with proper attention to medical workflows\n- Solid technical architecture using modern AI/ML approaches\n- Clear value proposition for both patients and healthcare providers\n- Comprehensive approach to medication adherence tracking\n\n**Areas for Improvement:**\n- Integration complexity with existing healthcare systems needs attention\n- Regulatory compliance pathway should be addressed early\n- Scalability considerations require further development\n\n**Recommendations:**\n- Focus on regulatory compliance early in development\n- Implement robust security measures for health data\n- Conduct larger-scale pilot studies to validate effectiveness\n- Develop clear implementation roadmap for healthcare organizations\n\nOverall, this project demonstrates strong potential for improving chronic disease management outcomes through innovative technology application.",
  "domain_insights": {
    "clinical": {
      "domain_name": "Clinical",
      "domain_description": "Medical or healthcare expertise related to patient care, diagnosis, or treatment",
      "summary": "Perspective from 2 Clinical reviewer(s)",
      "key_points": [
        "Impact",
        "Technical Feasibility",
        "Innovation"
      ],
      "concerns": [
        "Implementation Complexity"
      ],
      "review_count": 2,
      "artificial_count": 0
    },
    "technical": {
      "domain_name": "Technical", 
      "domain_description": "Expertise in programming, software engineering, hardware development, or technical implementation",
      "summary": "Perspective from 1 Technical reviewer(s)",
      "key_points": [
        "Innovation",
        "Technical Feasibility"
      ],
      "concerns": [
        "Scalability",
        "Implementation Complexity"
      ],
      "review_count": 1,
      "artificial_count": 0
    },
    "business": {
      "domain_name": "Business",
      "domain_description": "Expertise in business models, market analysis, and commercialization",
      "summary": "Perspective from 1 Business reviewer(s)",
      "key_points": [
        "Return on Investment",
        "Impact"
      ],
      "concerns": [
        "Scalability"
      ],
      "review_count": 1,
      "artificial_count": 1
    }
  },
  "recommendations": [
    "Focus on regulatory compliance early in development",
    "Implement robust security measures for health data", 
    "Conduct larger-scale pilot studies to validate effectiveness",
    "Address Technical concerns: Scalability, Implementation Complexity",
    "Leverage high impact potential with clear implementation roadmap"
  ],
  "meta_data": {
    "total_reviews": 5,
    "accepted_reviews": 4,
    "human_reviews": 3,
    "artificial_reviews": 1,
    "processing_time_seconds": 272,
    "ontology_stats": {
      "domains_used": 3,
      "total_domains_available": 6,
      "dimensions_evaluated": 6
    }
  }
}
```

### Get Visualization Data
Get data formatted for creating visualizations of the feedback.

```http
GET /api/v1/projects/{project_id}/feedback/visualization
```

**Response: 200 OK**
```json
{
  "radar_chart": {
    "dimensions": [
      "Technical Feasibility",
      "Innovation", 
      "Impact",
      "Implementation Complexity",
      "Scalability",
      "Return on Investment"
    ],
    "scores": [4.1, 4.3, 4.6, 3.2, 3.8, 4.0]
  },
  "domain_breakdown": [
    {
      "domain": "Clinical",
      "review_count": 2,
      "artificial_count": 0,
      "average_scores": {
        "Impact": 4.8,
        "Technical Feasibility": 4.2,
        "Innovation": 4.5
      }
    },
    {
      "domain": "Technical",
      "review_count": 1, 
      "artificial_count": 0,
      "average_scores": {
        "Technical Feasibility": 4.0,
        "Innovation": 4.1,
        "Scalability": 3.5
      }
    },
    {
      "domain": "Business",
      "review_count": 1,
      "artificial_count": 1,
      "average_scores": {
        "Return on Investment": 4.5,
        "Impact": 4.2,
        "Scalability": 3.9
      }
    }
  ],
  "score_distribution": {
    "1-2": 0,
    "2-3": 0,
    "3-4": 3,
    "4-5": 3
  }
}
```

---

## Health Check

### API Health Status
Check the health and status of the API and ontology system.

```http
GET /health
```

**Response: 200 OK**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T14:30:00Z",
  "ontology_status": "available",
  "ontology_info": {
    "domains": 6,
    "provider": "RDF/TTL",
    "backend": "rdflib"
  }
}
```

---

## Error Responses

All endpoints return standard HTTP status codes with detailed error messages:

### 400 Bad Request
```json
{
  "detail": "Validation error: field 'confidence_score' must be between 0 and 100"
}
```

### 404 Not Found
```json
{
  "detail": "Project proj_invalid not found"
}
```

### 409 Conflict
```json
{
  "detail": "Domain 'sustainability' already exists"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "confidence_score"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error processing reviews: LLM provider unavailable"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Ontology not available - cannot process reviews"
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **60 requests per minute** per IP address
- **Burst size**: 10 requests
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Request limit per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Window reset time

---

## Authentication

Currently, the API does not require authentication. In production deployments, consider implementing:

- API key authentication
- OAuth 2.0 integration
- Role-based access control for ontology management endpoints

---

## Examples

### Complete Workflow Example

```bash
# 1. Check ontology status
curl http://localhost:8000/api/v1/ontology/stats

# 2. Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "hackathon_id": "TestHack2025",
    "name": "AI Health App",
    "description": "An AI application for health management...",
    "work_done": "We built a prototype with user registration..."
  }'

# 3. Submit a review
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_name": "Dr. Test Reviewer",
    "text_review": "This is a promising healthcare application...",
    "confidence_score": 85
  }'

# 4. Start processing
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123/process \
  -H "Content-Type: application/json" \
  -d '{
    "generate_artificial_reviews": true,
    "force_reprocess": false
  }'

# 5. Check processing status
curl http://localhost:8000/api/v1/projects/proj_abc123/status

# 6. Get feedback report
curl http://localhost:8000/api/v1/projects/proj_abc123/feedback
```

### Ontology Management Example

```bash
# Add new domain for sustainability
curl -X POST http://localhost:8000/api/v1/ontology/domains \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sustainability",
    "name": "Environmental Sustainability", 
    "description": "Green technology and environmental impact",
    "keywords": ["sustainability", "green", "eco-friendly"],
    "relevant_dimensions": ["impact", "scalability"]
  }'

# Add new evaluation dimension
curl -X POST http://localhost:8000/api/v1/ontology/dimensions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "environmental_impact",
    "name": "Environmental Impact",
    "description": "Measures environmental sustainability",
    "scale": {
      "1": "Harmful to environment",
      "5": "Highly beneficial to environment"
    }
  }'

# Reload ontology to apply changes
curl -X POST http://localhost:8000/api/v1/ontology/reload
```

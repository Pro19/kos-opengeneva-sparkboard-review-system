# REST API for Ontology-Driven Hackathon Review System

This document describes the REST API implementation for the hackathon review system. The API replaces the file-based input system with a modern REST interface.

## Features

- **RESTful API** with comprehensive endpoints for project and review management
- **SQLite database** for persistent storage
- **Asynchronous processing** for review analysis
- **Multiple API documentation formats**:
  - Swagger UI
  - ReDoc
  - Scalar (modern, interactive documentation)
  - OpenAPI JSON specification
- **Background task processing** for long-running analysis
- **Idempotent operations** where appropriate

## Installation

1. Install the additional API dependencies:
   ```bash
   pip install -r requirements_api.txt
   ```

2. Run the API server:
   ```bash
   python run_api.py
   ```

   Or with custom settings:
   ```bash
   API_HOST=0.0.0.0 API_PORT=8080 python run_api.py
   ```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Scalar**: http://localhost:8000/scalar (recommended - modern UI)
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Quick Start Guide

### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "hackathon_id": "MedTech2025",
    "name": "AI Health Assistant",
    "description": "An AI-powered health assistant for chronic disease management...",
    "work_done": "We have developed a functional prototype..."
  }'
```

### 2. Submit Reviews

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/reviews" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_name": "Dr. Sarah Johnson",
    "text_review": "This project shows great promise...",
    "confidence_score": 95,
    "links": {
      "linkedin": "https://linkedin.com/in/sarahjohnson"
    }
  }'
```

### 3. Process Reviews

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/process" \
  -H "Content-Type: application/json" \
  -d '{
    "generate_artificial_reviews": true,
    "force_reprocess": false
  }'
```

### 4. Check Processing Status

```bash
curl "http://localhost:8000/api/v1/projects/{project_id}/status"
```

### 5. Get Feedback Report

```bash
curl "http://localhost:8000/api/v1/projects/{project_id}/feedback"
```

## API Endpoints

### Project Management

- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects/{project_id}` - Get project details
- `PUT /api/v1/projects/{project_id}` - Update project information

### Review Management

- `POST /api/v1/projects/{project_id}/reviews` - Submit a review
- `GET /api/v1/projects/{project_id}/reviews` - List reviews with pagination
- `GET /api/v1/projects/{project_id}/reviews/{review_id}` - Get specific review

### Processing

- `POST /api/v1/projects/{project_id}/process` - Start review analysis (idempotent)
- `GET /api/v1/projects/{project_id}/status` - Get processing status

### Results

- `GET /api/v1/projects/{project_id}/feedback` - Get feedback report
- `GET /api/v1/projects/{project_id}/feedback/visualization` - Get visualization data

## Database Schema

The API uses SQLite with the following main tables:

- **projects**: Stores project information
- **reviews**: Stores submitted reviews
- **processing_jobs**: Tracks background processing jobs
- **feedback_reports**: Stores generated feedback reports

## Processing Workflow

1. **Submit Project**: Create a project via the API
2. **Submit Reviews**: Multiple reviewers submit their reviews
3. **Start Processing**: Trigger the analysis process
4. **Background Processing**:
   - Reviews are analyzed and classified
   - Reviewer expertise is determined
   - Artificial reviews are generated for missing domains
   - Feedback scores are calculated
   - Final report is generated
5. **Retrieve Results**: Get the feedback report and visualization data

## Configuration

The system uses the existing configuration in `config.py`. Key settings:

- **LLM Provider**: Configure which LLM to use (Ollama, Claude, ChatGPT, Grok)
- **Review Thresholds**: Minimum confidence scores and relevance thresholds
- **Core Domains**: Domains to ensure coverage in reviews

## Error Handling

The API provides detailed error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `202`: Accepted (for async operations)
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Async Processing

Long-running tasks (like review analysis) are processed asynchronously:

1. The `/process` endpoint returns immediately with a `202 Accepted` status
2. Check the status using the `/status` endpoint
3. Once completed, retrieve results from `/feedback`

## Development

For development with auto-reload:
```bash
API_RELOAD=true python run_api.py
```

## Testing

Example test script:
```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Create project
        response = await client.post(
            "http://localhost:8000/api/v1/projects",
            json={
                "hackathon_id": "Test2025",
                "name": "Test Project",
                "description": "A test project description...",
                "work_done": "Initial prototype completed..."
            }
        )
        project = response.json()
        print(f"Created project: {project['project_id']}")
        
        # Submit review
        response = await client.post(
            f"http://localhost:8000/api/v1/projects/{project['project_id']}/reviews",
            json={
                "reviewer_name": "Test Reviewer",
                "text_review": "This is a test review...",
                "confidence_score": 85
            }
        )
        print(f"Submitted review: {response.json()['review_id']}")

asyncio.run(test_api())
```

## Migration from File-Based System

To migrate existing projects from the file-based system:

1. Use the existing `load_all_projects()` function to read projects
2. Submit them via the API
3. Submit their reviews via the API
4. Trigger processing

The processing engine remains the same - only the input/output mechanism has changed.
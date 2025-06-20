# Usage Instructions

Interface Options:

1. **CLI Version** - Command-line interface for automation purposes
2. **REST API Version** - REST API server for remote automation purposes
3. **Desktop Version** - Qt based interactive user interface
4. **Browser Version** - An interactive browser based user interface

---

## CLI Version

### Local

> _Make sure the virtual environment is active!_

```bash
# process all projects in the projects/ directory
python -m src.cli.main

# process a specific project
python -m src.cli.main --project <project_id>

# create new ontology
python -m src.cli.main --new-ontology

# custom output directory
python -m src.cli.main --output custom_output/

# analyze ontology structure
python -m src.cli.main --analyze-ontology

# validate ontology consistency
python -m src.cli.main --validate-ontology

# create ontology backup
python -m src.cli.main --backup-ontology
```

For CLI usage, organize projects as:

```
projects/
├── project1/
│   ├── description.md
│   ├── review1.md
│   └── review2.md
└── project2/
    ├── description.md
    └── review1.md
```

### Containerized

```bash
# process all projects in the projects/ directory
docker run -v $(pwd)/projects:/app/projects -v $(pwd)/output:/app/output hackathon-review-system

# process a specific project
docker run -v $(pwd)/projects:/app/projects -v $(pwd)/output:/app/output hackathon-review-system --project ai-health-assistant

# create new ontology
docker run -v $(pwd)/projects:/app/projects -v $(pwd)/output:/app/output hackathon-review-system --new-ontology

# custom output directory with volume mapping
docker run -v $(pwd)/projects:/app/projects -v $(pwd)/custom_output:/app/output hackathon-review-system --output /app/output

# analyze ontology structure
docker run hackathon-review-system --analyze-ontology

# validate ontology consistency
docker run hackathon-review-system --validate-ontology
```

## Desktop Version

> _Make sure the virtual environment is active!_

**Note:** The GUI version requires a local installation with PyQt6. Docker containers do not support GUI applications without additional X11 forwarding configuration.

```bash
# start the desktop ui
python -m src.api.desktop
```

## REST API Version

### Local

> _Make sure the virtual environment is active!_

```bash
# start the API server
python scripts/run_api.py

# or directly with uvicorn
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

API Documentation will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Scalar: http://localhost:8000/scalar (prefer this)
- OpenAPI JSON: http://localhost:8000/openapi.json

**Key API Endpoints**

```bash
# Ontology Management
GET /api/v1/ontology/stats              # Get ontology statistics
GET/POST /api/v1/ontology/domains       # Manage domains
GET/POST /api/v1/ontology/dimensions    # Manage evaluation dimensions
POST /api/v1/ontology/reload            # Reload ontology from TTL file

# Project Management
POST /api/v1/projects                   # Create new project
GET /api/v1/projects/{id}               # Get project details
POST /api/v1/projects/{id}/reviews      # Submit review
POST /api/v1/projects/{id}/process      # Start review analysis

# Results & Feedback
GET /api/v1/projects/{id}/feedback      # Get comprehensive feedback report
GET /api/v1/projects/{id}/status        # Get processing status
```

### Containerized

```bash
# start the API server in a container
docker run -p 8000:8000 hackathon-review-system python scripts/run_api.py
# or
podman run -p 8000:8000 hackathon-review-system python scripts/run_api.py

# or with docker-compose (if available)
docker-compose up
```

## Browser Version

After running the API server _(see instructions above)_, open web ui in the browser at: http://localhost:8000/ui

---

## Ontology Management Examples

**Add new domain via API:**

```bash
curl -X POST http://localhost:8000/api/v1/ontology/domains \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sustainability",
    "name": "Environmental Sustainability",
    "description": "Green technology and environmental impact expertise",
    "keywords": ["sustainability", "green", "eco-friendly", "carbon"],
    "relevant_dimensions": ["impact", "scalability"]
  }'
```

**Query ontology with SPARQL:**

```python
from src.core.ontology_rdf import RDFOntology

ontology = RDFOntology()
query = """
PREFIX hr: <http://example.org/hackathon-review/>
SELECT ?domain ?keyword
WHERE {
    ?domain a hr:Domain ;
            hr:hasKeyword ?keyword .
    FILTER(CONTAINS(?keyword, "health"))
}
"""
results = ontology.graph.query(query)
```

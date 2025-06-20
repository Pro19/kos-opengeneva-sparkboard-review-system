# Usage Instructions

The Ontology-Driven Hackathon Review System provides three different interfaces:

1. **CLI Version** - Command-line interface for batch processing and automation
2. **GUI Version** - Graphical user interface for interactive analysis (PyQt6-based)
3. **REST API Version** - Web-based API with browser interface for remote access

Choose the interface that best fits your workflow and requirements.

## CLI Version:

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

## GUI Version:

```bash
# start the graphical user interface
python gui.py

# or using the module path
python -m src.gui.main
```

The GUI provides an intuitive interface with the following tabs:

### Projects Tab

- Browse and select project directories
- View project information and review counts
- Select multiple projects for batch analysis
- Refresh project list as needed

### Configuration Tab

- Configure LLM provider settings (Ollama, Claude, ChatGPT, Groq)
- Set API keys and model parameters
- Adjust general settings like ontology updates and chart generation
- Save configuration for the current session

### Analysis Tab

- Monitor analysis progress in real-time
- View detailed logs of the analysis process
- Start/stop analysis operations
- Clear log output when needed

### Results Tab

- Browse completed analysis results
- View feedback scores and final reviews
- Export results for further processing
- Visualize project evaluation data

The GUI automatically organizes projects in the same structure as the CLI version and provides visual feedback throughout the analysis process.

## REST API Version:

```bash
# start the API server
python scripts/run_api.py

# or directly with uvicorn
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Open web ui in the browser at: http://localhost:8000/ui

API Documentation will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Scalar: http://localhost:8000/scalar (prefer this)
- OpenAPI JSON: http://localhost:8000/openapi.json

### Key API Endpoints

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

# OpenGeneva Sparkboard: Ontology-Driven AI for Multi-Perspective Peer Review in Hackathons

## Team Information

**Course:** D400006 – Knowledge Organization Systems, Université de Genève

**Team Members:**

- Eisha Tir Raazia
- Mahidhar Reddy Vaka
- Oussama Rattazi
- Pranshu Mishra

---

## Project Description

### Overview

The OpenGeneva Sparkboard is an innovative ontology-driven AI system designed to enhance the depth and utility of peer review systems in hackathon environments. Rather than relying on simplistic ranking scales, our approach leverages structured knowledge representation to capture both reviewer characteristics and feedback dimensions, enabling comprehensive multi-perspective analysis of hackathon projects.

### State-of-the-Art & Problem Statement

Traditional hackathon peer reviews suffer from several limitations:

- Lack of structure in review processes
- Poor expertise matching between reviewers and projects
- Insufficient perspective coverage across different domains
- Inconsistent evaluation criteria across reviewers

### Key Features

- **Ontological Knowledge Representation:** Structured classification of domains, expertise levels, and evaluation dimensions
- **Reviewer Expertise Profiling:** Automatic classification of reviewers based on confidence scores and review content
- **Domain Relevance Scoring:** Intelligent matching between reviewer expertise and project domains
- **Artificial Review Generation:** AI-generated reviews to fill gaps in domain coverage
- **Multi-dimensional Evaluation:** Comprehensive scoring across technical feasibility, innovation, impact, scalability, and ROI
- **Hybrid Human-AI Pipeline:** Combines human expertise with AI augmentation for comprehensive analysis

### Ontology & AI Methods Used

- **Knowledge Graph Structure:** RDF/TTL-based ontology defining domains, subdomains, expertise levels, and evaluation dimensions
- **Natural Language Processing:** LLM-based sentiment analysis and review classification
- **Machine Learning:** Domain classification and relevance scoring using text similarity measures
- **Multi-Provider LLM Integration:** Support for Claude, ChatGPT, Ollama, and Groq APIs
- **Confidence-Based Filtering:** Review acceptance based on expertise level and domain relevance thresholds

---

## Installation & Setup

### Prerequisites

- Python 3.13.3 or latest
- Git
- LLM Provider Access (at least one of the following):
  - Ollama (local) - _recommended for development_
  - Anthropic Claude
  - OpenAI ChatGPT
  - Groq

### Setup Instructions

**1. Clone the repository**

```bash
git clone https://github.com/Pro19/kos-opengeneva-sparkboard-review-system

cd kos-opengeneva-sparkboard-review-system
```

**2. Create virtual environment**

```bash
python -m venv .venv        # linux
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure LLM Provider**

```bash
# Install Ollama (if not already installed)
./scripts/install-ollama.bash   # linux

# Pull a model (e.g., DeepSeek R1)
ollama pull deepseek-r1:1.5b
```

Edit `src/infrastructure/config.py` to configure your preferred LLM provider:

**Example provider: Ollama (Local, Free)**

Install Ollama using the provided script:

```bash
# linux only
chmod +x scripts/install-ollama.bash
./scripts/install-ollama.bash

# pull a model
ollama pull deepseek-r1:1.5b
# or
ollama pull llama3

ollama serve  # usually runs on localhost:11434
```

Update config (default):

```python
LLM_CONFIG = {
    "provider": "ollama",

    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1:1.5b"
    }
}
```

**Test LLM configuration**

```bash
# python -m src.cli.llm_cli test <provider_name>

python -m src.cli.llm_cli test ollama
```

---

## Ontology & Data Structure

### Ontology Design

Our ontology is structured around five core components:

**1. Domains (`hr:Domain`)**

- _Technical_: Programming, software engineering, hardware development
- _Clinical_: Medical/healthcare expertise, patient care, diagnosis
- _Administrative_: Healthcare administration, policy, management
- _Business_: Market analysis, commercialization, entrepreneurship
- _Design_: UI/UX design, visual design, interaction design
- _User Experience_: User research, accessibility, behavior analysis

**2. Expertise Levels (`hr:ExpertiseLevel`)**

Based on confidence scores (0-100):

- _Beginner (0-40)_: Basic understanding
- _Skilled (41-70)_: Practical experience
- _Talented (71-85)_: Deep understanding
- _Seasoned (86-95)_: Extensive experience
- _Expert (96-100)_: Top-level mastery

**3. Impact Dimensions (`hr:ImpactDimension`)**

- _Technical Feasibility_: Implementation difficulty with current technology
- _Innovation_: Novelty and uniqueness of approach
- _Impact_: Potential effect on target problem/domain
- _Implementation Complexity_: Practical deployment difficulty
- _Scalability_: Ability to scale to wider implementation
- _Return on Investment_: Expected benefits vs. costs

**4. Project Types (`hr:ProjectType`)**

Software, Hardware, Data, Process, Service

**5. Review Dimensions Mapping**

Each domain has relevant dimensions for focused evaluation:

- _Technical_: Technical Feasibility, Implementation Complexity, Scalability, Innovation
- _Clinical_: Impact, Implementation Complexity, Technical Feasibility
- _Business_: ROI, Scalability, Impact

### Data Schema

The system uses both file-based storage (for CLI) and SQLite database (for API):

```sql
Projects: project_id, name, description, work_done, status
Reviews: review_id, project_id, reviewer_name, text_review, confidence_score
ProcessingJobs: job_id, project_id, status, progress
FeedbackReports: report_id, project_id, feedback_scores, final_review
```

## File Structure

```
kos-opengeneva-sparkboard-review-system/
├── README.md                         # This comprehensive documentation
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
│
├── scripts/                          # Installation and utility scripts
│   ├── install-ollama.bash           # Ollama installation script (Linux)
│   └── run_api.py                    # API server startup script
│
├── src/                              # Main source code
│   ├── api/                          # REST API implementation
│   │   ├── __init__.py
│   │   ├── app.py                    # FastAPI application
│   │   ├── models.py                 # SQLAlchemy & Pydantic models
│   │   ├── processing.py             # Background processing tasks
│   │   └── scalar_fastapi.py         # API documentation integration
│   │
│   ├── cli/                          # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py                   # CLI entry point
│   │   └── llm_cli.py                # LLM provider management
│   │
│   ├── core/                         # Core logic
│   │   ├── __init__.py
│   │   ├── ontology.py               # Ontology management
│   │   ├── project.py                # Project data structures
│   │   ├── reviewer.py               # Reviewer profiling
│   │   ├── review.py                 # Review analysis
│   │   └── feedback.py               # Feedback generation
│   │
│   └── infrastructure/               # Infrastructure & utilities
│       ├── __init__.py
│       ├── config.py                 # Configuration settings
│       ├── database.py               # Database setup
│       ├── llm_interface.py          # LLM provider interface
│       ├── logging_utils.py          # Logging configuration
│       └── utils.py                  # Utility functions
│
├── data/                             # Ontology and reference data
│   ├── ontology.json                 # JSON ontology definition
│   └── ontology.ttl                  # RDF/TTL ontology format
│
├── docs/                             # Documentation
│   ├── api.md                        # REST API documentation
│   └── uninstall-ollama.md           # Ollama uninstallation guide
│
├── projects/                         # Sample project data (CLI mode)
│   └── [project_directories]/        # Individual project folders
```

- **Core Logic (`src/core/`):** Domain-specific business logic for ontology, reviews, and feedback
- **API Layer (`src/api/`):** REST API with OpenAPI documentation
- **CLI Interface (`src/cli/`):** Command-line tools for batch processing
- **Infrastructure (`src/infrastructure/`):** Project wide features like logging, database, LLM integration
- **Ontology Data (`data/`):** Structured knowledge representation in JSON and RDF formats
- **Documentation (`docs/`):** Technical documentation and guides

---

## Usage Instructions

### CLI Version:

```bash
# process all projects in the projects/ directory
python -m src.cli.main

# process a specific project
python -m src.cli.main --project <project_id>

# create new ontology
python -m src.cli.main --new-ontology

# custom output directory
python -m src.cli.main --output custom_output/
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

### GUI Version:

A simple GUI application is included to analyze the project and visualize the ontology + project reviews:

```bash
python gui.py
```

### Docker Version:

#### build the Docker image

```bash

docker build -t hackathon-review-system .
```

#### run the Docker container

docker run hackathon-review-system --project ai-health-assistant

````

### REST API Version:

```bash
# start the API server
python scripts/run_api.py

# or directly with uvicorn
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
````

API Documentation will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Scalar: http://localhost:8000/scalar (prefer this)
- OpenAPI JSON: http://localhost:8000/openapi.json

## References & Acknowledgments

### Academic References

### Acknowledgments

Special thanks to:

- Professor and TA of D400006 for guidance on knowledge organization systems (Thomas and Tibaut)
- Maintainer of OpenGeneva Sparkboard (Matt)
- Our team members for collaborative development

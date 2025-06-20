# OpenGeneva Sparkboard: Ontology-Driven AI for Multi-Perspective Peer Review in Hackathons

## Team Information

**Course:** D400006 – Knowledge Organization Systems, Université de Genève

**Team Members:**
- Eisha Tir Raazia - Eisha.Raazia@etu.unige.ch
- Mahidhar Reddy Vaka - Mahidhar.Vaka@etu.unige.ch
- Oussama Rattazi - Oussama.Rattazi@etu.unige.ch
- Pranshu Mishra - Pranshu.Mishra@etu.unige.ch

---

## Project Description

### Overview

This project is an innovative *RDF/TTL ontology-driven** AI system designed to enhance the depth and utility of peer review systems in hackathon environments. Rather than relying on simplistic ranking scales, our approach leverages structured knowledge representation to capture both reviewer characteristics and feedback dimensions, enabling comprehensive multi-perspective analysis of hackathon projects.

### State-of-the-Art & Problem Statement

Traditional hackathon peer reviews suffer from several limitations:
- **Static review frameworks** that cannot adapt to new domains or evaluation criteria
- **Poor expertise matching** between reviewers and projects
- **Insufficient perspective coverage** across different stakeholder domains
- **Inconsistent evaluation criteria** that vary between reviewers and events
- **Lack of semantic understanding** of domain relationships and expertise levels

### Our Approach: Dynamic RDF Ontology Based Review System

Our solution transforms static review systems into **adaptive, knowledge-driven platforms** that:
- **Generate prompts dynamically** from RDF ontology definitions
- **Adapt behavior in real-time** based on ontological knowledge updates
- **Understand semantic relationships** between domains and evaluation dimensions
- **Scale automatically** to new domains without code modifications

### Key Features

#### **🧠 RDF Ontology-Driven Intelligence**
- **Dynamic Knowledge Representation:** RDF/TTL ontology with semantic relationships
- **Runtime Ontology Management:** Add domains/dimensions without code changes
- **Semantic Relationship Modeling:** Explicit domain-dimension associations

#### **🔄 Dynamic AI Prompt Generation**
- **Context-Aware Prompts:** Generated from ontological domain definitions
- **Adaptive Review Criteria:** Evaluation dimensions loaded dynamically from ontology
- **Semantic Personalization:** Prompts include relevant keywords and relationships
- **Multi-Domain Coverage:** Automatic prompt generation for missing expertise areas

#### **👥 Intelligent Reviewer Profiling**
- **Semantic Classification:** Domain assignment using ontological definitions
- **Expertise Level Mapping:** Confidence-based expertise determination
- **Relevance Scoring:** Semantic matching between reviewer expertise and projects
- ~~**External Profile Integration:** LinkedIn, GitHub, Google Scholar analysis~~

#### **📊 Multi-Dimensional Evaluation Framework**
- **Dynamic Scoring Dimensions:** Loaded from RDF ontology definitions
- **Weighted Domain Analysis:** Scoring based on domain-dimension relevance
- **Comprehensive Impact Assessment:** Technical, clinical, business, and design perspectives
- **Adaptive Scale Definitions:** Evaluation criteria defined semantically in ontology

#### **🤖 Hybrid Human-AI Pipeline**
- **Intelligent Review Augmentation:** AI fills gaps in domain coverage
- **Quality-Based Filtering:** Confidence and relevance threshold management
- **Multi-Perspective Synthesis:** Combines human expertise with AI-generated insights
- **Contextual Recommendation Engine:** Actionable suggestions based on ontological analysis

### Ontology & AI Methods Used

- **RDF/TTL Semantic Web:** Knowledge representation using W3C standards
- **SPARQL Query Engine:** Dynamic knowledge extraction from triple store
- **Natural Language Processing:** LLM-based sentiment analysis and classification
- **Graph-Based Reasoning:** Domain relevance scoring using semantic relationships
- **Multi-Provider LLM Integration:** Support for Claude, ChatGPT, Ollama, and Groq
- **Confidence-Based Filtering:** Review acceptance based on expertise and relevance

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
python -m venv .venv

source .venv/bin/activate   # activate the virtual environment
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure LLM Provider**

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

### REST API Version:
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


## References & Acknowledgments

### Academic References

### Acknowledgments

Special thanks to:

- Professor and TA of D400006 for guidance
    - Thomas Maillart - Thomas.Maillart@unige.ch
    - Thibaut Chataing - Thibaut.Chataing@unige.ch
- Maintainer of OpenGeneva Sparkboard hackathon platform
    -Matthew Hubert - matt@opengeneva.org
- Our team members

### Future Possibilities
- Import External Ontologies: Load domain-specific ontologies from research
- Reasoning: Add RDFS/OWL reasoning for inferred relationships
- Linked Data: Connect to external knowledge graphs
- Multi-Language Support: Internationalize domain/dimension descriptions
- Advanced Querying: Complex SPARQL queries for deep analysis
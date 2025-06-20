# File Structure

```
kos-opengeneva-sparkboard-review-system/
├── README.md                         # Comprehensive project documentation
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
│
├── scripts/                          # Installation and utility scripts
│   ├── install-ollama.bash           # Ollama installation script (Linux)
│   ├── run_api.py                    # API server startup script
│   └── example_api.py                # API usage examples
│
├── src/                              # Main source code
│   ├── api/                          # API & Interface implementations
│   │   ├── app.py                    # FastAPI application with ontology APIs
│   │   ├── models.py                 # SQLAlchemy & Pydantic models
│   │   ├── processing.py             # Background processing with RDF ontology
│   │   ├── scalar_fastapi.py         # API documentation integration
│   │   └── desktop.py                # PyQt6 Desktop GUI application
│   │
│   ├── cli/                          # Command-line interface
│   │   ├── main.py                   # Enhanced CLI with ontology features
│   │   └── llm_cli.py                # LLM provider management
│   │
│   ├── core/                         # Core logic
│   │   ├── ontology.py               # RDF ontology wrapper with compatibility
│   │   ├── ontology_rdf.py           # Core RDF/TTL ontology management
│   │   ├── dynamic_prompts.py        # Dynamic prompt generation from ontology
│   │   ├── project.py                # Project data structures
│   │   ├── reviewer.py               # Reviewer profiling with ontology
│   │   ├── review.py                 # Review analysis with dynamic dimensions
│   │   └── feedback.py               # Feedback generation with ontology context
│   │
│   └── infrastructure/               # Infrastructure & utilities
│       ├── config.py                 # Configuration for RDF system
│       ├── database.py               # Database setup and management
│       ├── llm_interface.py          # Multi-provider LLM interface
│       ├── logging_utils.py          # Logging configuration
│       └── utils.py                  # Utility functions
│
├── data/                             # Ontology and reference data
│   ├── ontology.ttl                  # RDF/TTL ontology definition (primary)
│   └── ontology.json                 # JSON ontology (backward compatibility)
│
├── docs/                             # Documentation
│   ├── api.md                        # REST API documentation
│   ├── file-structure.md             # This file structure documentation
│   ├── ontology-data-structure.md    # Ontology design and data schema
│   ├── installation-setup.md         # Installation and setup instructions
│   ├── usage-instructions.md         # Usage instructions for all interfaces
│   ├── evaluation-results.md         # Evaluation methodology and results
│   ├── screenshots.md                # Screenshots of different interfaces
│   ├── dev/                          # Developer documentation
│   │   ├── api_docs.md               # API development documentation
│   │   └── uninstall-ollama.md       # Ollama uninstallation guide
│   └── (additional documentation files)
│
├── projects/                         # Sample project data (CLI mode)
│   ├── ai-health-assistant/          # AI health assistant project
│   │   ├── description.md
│   │   └── review*.md
│   └── eco-tracker/                  # Carbon footprint tracker project
│       ├── description.md
│       └── review*.md
│
├── output/                           # Generated reports and visualizations
│   ├── feedback_reports/
│   ├── visualizations/
│   └── ontology_backups/
│
└── logs/                             # Application logs
    └── hackathon_review.log
```

## Key files/modules:
- **Core Logic (`src/core/`):** Main logic for ontology, reviews, and feedback
- **API Layer (`src/api/`):** REST API with OpenAPI documentation
- **CLI Interface (`src/cli/`):** Command-line tools with ontology analysis features
- **Infrastructure (`src/infrastructure/`):** Project wide features like logging, database, LLM integration
- **Ontology Data (`data/`):** Structured knowledge representation in RDF/TTL format
- **Documentation (`docs/`):** Technical documentation and guides
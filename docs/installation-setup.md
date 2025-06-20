# Installation & Setup

## Prerequisites

- Python 3.13.3 or latest
- Git
- LLM Provider Access (at least one of the following):
    - Ollama (local) - _recommended for development_
    - Anthropic Claude
    - OpenAI ChatGPT
    - Groq

## Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/Pro19/kos-opengeneva-sparkboard-review-system

cd kos-opengeneva-sparkboard-review-system
```
**2. Create virtual environment**
```bash
python -m venv .venv

source .venv/bin/activate   # activate the virtual environment (linux)
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

Key dependencies include:
- `rdflib` - RDF/TTL ontology management
- `scikit-learn` - Machine learning and text similarity
- `fastapi` - REST API framework
- `matplotlib` - Visualization generation
- `requests` - HTTP client for LLM APIs

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

**5. Test LLM configuration**
```bash
# python -m src.cli.llm_cli test <provider_name>

python -m src.cli.llm_cli test ollama
```

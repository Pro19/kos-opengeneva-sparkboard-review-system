# Ontology-Driven AI for Multi-Perspective Peer Review

This repository contains an implementation of an ontology-driven AI system for analyzing hackathon project reviews from multiple perspectives, with flexible LLM provider support.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/your-username/hackathon-review-system.git
   cd hackathon-review-system
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install required dependencies:

   ```bash
   pip install scikit-learn numpy requests
   ```

4. (Optional) Install Ollama for local LLM inference:
   - Visit [Ollama's website](https://ollama.ai/) to download and install
   - Pull a model: `ollama pull llama3` or `ollama pull mistral`

## GUI Application

A simple GUI application is included to analyze the project and visualize the ontology + project reviews:

```bash
python gui.py
```

## LLM Provider Support

The system now supports multiple LLM providers:

1. **Ollama** (default): Run open-source LLMs locally
2. **Claude**: Use Anthropic's Claude models via API
3. **ChatGPT**: Use OpenAI's GPT models via API

### Configuring LLM Providers

You can configure which LLM provider to use in `config.py`:

```python
LLM_CONFIG = {
    "provider": "ollama",  # Choose between "claude", "chatgpt", or "ollama"

    "ollama": {
        "base_url": "http://localhost:11434",  # Default Ollama API URL
        "model": "llama3",  # Choose your available model
        "max_tokens": 1000
    },

    "claude": {
        "api_key": "YOUR_ANTHROPIC_API_KEY",
        "model": "claude-3-opus-20240229",
        "max_tokens": 1000
    },

    "chatgpt": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "model": "gpt-4-turbo",
        "max_tokens": 1000
    },

    "groq": {
        "api_key": "YOUR_GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai",
        "model": "llama3-70b-8192",
        "max_tokens": 1000
    }
}
```

### LLM Provider CLI Utility

A command-line utility is included to manage and test different LLM providers:

```bash
# Show current configuration
python llm_cli.py config

# Set default provider
python llm_cli.py set ollama

# Test a provider
python llm_cli.py test ollama
```

## Running the System

### Testing with Sample Projects

To run the system with the included test projects:

```bash
python run_test.py
```

This script will:

1. Set up the test environment with sample projects
2. Update the configuration to use the test projects directory
3. Run the main program and generate feedback reports in the `output` directory

### Regular Usage

For regular usage with your own projects:

```bash
python main.py
```

Additional options:

- `--project PROJECT_ID`: Process a specific project
- `--output OUTPUT_DIR`: Specify output directory
- `--new-ontology`: Create a new ontology instead of loading existing one

Example:

```bash
python main.py --project ai-health-assistant --output results
```

## Advanced Usage: LLM Factory

For more advanced control over LLM interactions, you can use the `LLMFactory` class:

```python
from llm_factory import LLMFactory

# Create an LLM factory
llm = LLMFactory()

# Get a response using the default provider
response = llm.get_response("What is ontology in computer science?")

# Get a response from a specific provider
response = llm.get_response(
    "Explain machine learning",
    provider="ollama",
    model="llama3",
    max_tokens=500
)

# Switch the default provider
llm.set_default_provider("claude")
```

## System Features

- **Flexible LLM backend**: Use local models via Ollama or cloud APIs
- **Ontology-driven analysis**: Structured representation of domains, expertise, and feedback dimensions
- **Reviewer classification**: Identification of reviewer domain expertise and relevance
- **Multi-perspective feedback**: Analysis of projects from diverse stakeholder viewpoints
- **Artificial review generation**: AI-generated reviews for missing domain perspectives
- **Comprehensive reports**: Detailed feedback with multi-dimensional scoring

## Notes

- When using Ollama, ensure the Ollama service is running locally
- API keys for Claude and ChatGPT should be stored securely (not hardcoded in the config file)
- The system assumes all reviews follow the specified format

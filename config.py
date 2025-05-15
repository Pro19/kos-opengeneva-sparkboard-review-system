"""
Configuration settings for the hackathon review system.
"""

# LLM API configuration
LLM_CONFIG = {
    "provider": "ollama",  # Choose between "claude", "chatgpt", or "ollama"
    
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
    
    "ollama": {
        "base_url": "http://localhost:11434",  # Default Ollama API URL
        "model": "deepseek-r1:8b",  # Choose your available model (llama3, mistral, etc.)
        "max_tokens": 1000
    }
}

# Review filtering thresholds
REVIEW_THRESHOLDS = {
    "min_confidence_score": 40,  # Minimum confidence score to consider review
    "min_domain_relevance": 0.3,  # Minimum domain relevance score (0-1)
    "expert_confidence_threshold": 80  # Threshold to consider a reviewer an expert
}

# Feedback generation settings
FEEDBACK_SETTINGS = {
    "dimensions": [
        "technical_feasibility",
        "innovation",
        "impact",
        "implementation_complexity",
        "scalability",
        "return_on_investment"
    ]
}

# File paths and directories
PATHS = {
    "projects_dir": "projects/",
    "ontology_file": "ontology.json"
}

# List of domains to ensure coverage in reviews
CORE_DOMAINS = [
    "technical",
    "clinical",
    "administrative",
    "business",
    "design",
    "user_experience"
]
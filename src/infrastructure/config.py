# General settings
SETTINGS = {
    "update_ontology": False,   # Enable ontology updates with LLM
    "generate_charts": True,   # Whether to generate visualization charts
    "artificial_reviews": True, # Whether to generate artificial reviews for missing domains
    "use_rdf_ontology": True,  # Use RDF/TTL backend instead of JSON
}

# Logging configuration
LOGGING_CONFIG = {
    "default_level": "INFO",
    "log_file": "logs/hackathon_review.log",
    "console_logging": True
}

# LLM API configuration
LLM_CONFIG = {
    "provider": "ollama",  # Switched to Groq as mentioned in presentation
    "max_retries": 3,
    "retry_delay": 2,
    
    "claude": {
        "api_key": "YOUR_ANTHROPIC_API_KEY",
        "model": "claude-3-opus-20240229",
        "max_tokens": 2000  # Increased for dynamic prompts
    },
    
    "chatgpt": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "model": "gpt-4-turbo",
        "max_tokens": 2000
    },
    
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1:1.5b",
        "max_tokens": 2000
    },

    "groq": {
        "api_key": "YOUR_GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1/",
        "model": "llama3-70b-8192",
        "max_tokens": 2000
    }
}

# Review filtering thresholds
REVIEW_THRESHOLDS = {
    "min_confidence_score": 40,
    "min_domain_relevance": 0.3,
    "expert_confidence_threshold": 80,
    "domain_relevance_threshold": 0.2
}

# Feedback generation settings - now dynamic from ontology
FEEDBACK_SETTINGS = {
    "chart": {
        "type": "radar",
        "width": 10,
        "height": 8,
        "dpi": 300
    },
    # Note: dimensions are now loaded dynamically from ontology
    "use_dynamic_dimensions": True
}

# File paths and directories
PATHS = {
    "projects_dir": "projects/",
    "ontology_file": "data/ontology.json",      # Kept for backward compatibility
    "ontology_ttl": "data/ontology.ttl",        # Primary ontology file (RDF/TTL)
    "output_dir": "output/",
    "visualizations_dir": "output/visualizations/",
    "logs_dir": "logs/",
    "data_dir": "data/"
}

# Core domains - loaded from ontology but kept for initial validation
CORE_DOMAINS = [
    "technical",
    "clinical", 
    "administrative",
    "business",
    "design",
    "user_experience"
]

# Default values for sentiment analysis - is dynamic but kept as fallback
DEFAULT_SENTIMENT_SCORES = {
    "technical_feasibility": 3.0,
    "innovation": 3.0,
    "impact": 3.0,
    "implementation_complexity": 3.0,
    "scalability": 3.0,
    "return_on_investment": 3.0,
    "overall_sentiment": 3.0
}

# RDF/SPARQL Configuration
RDF_CONFIG = {
    "namespaces": {
        "hr": "http://example.org/hackathon-review/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    },
    "query_timeout": 30,  # seconds
    "cache_queries": True
}

# Dynamic prompt configuration
PROMPT_CONFIG = {
    "max_prompt_length": 4000,  # characters
    "include_examples": True,
    "context_window": 2000,     # characters for context in prompts
    "temperature": 0.7,         # for LLM generation
}

# API Configuration
API_CONFIG = {
    "title": "Ontology-Driven Hackathon Review API",
    "description": "AI-powered multi-perspective peer review system using RDF ontology",
    "version": "2.0.0",
    "cors_origins": ["*"],
    "rate_limit": {
        "requests_per_minute": 60,
        "burst_size": 10
    }
}
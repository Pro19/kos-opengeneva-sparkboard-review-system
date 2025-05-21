"""
Configuration settings for the hackathon review system.
"""

# General settings
SETTINGS = {
    "update_ontology": False,  # Whether to update ontology with LLM
    "generate_charts": True,   # Whether to generate visualization charts
    "artificial_reviews": True, # Whether to generate artificial reviews for missing domains
}

# Logging configuration
LOGGING_CONFIG = {
    "default_level": "INFO",
    "log_file": "logs/hackathon_review.log",
    "console_logging": True
}


# LLM API configuration
LLM_CONFIG = {
    "provider": "ollama",  # Choose between "claude", "chatgpt", or "ollama"
    "max_retries": 3,      # Number of retries for API calls
    "retry_delay": 2,      # Delay between retries in seconds
    
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
    },

    "grok": {
        "api_key": "YOUR_GROK_API_KEY",
        "base_url": "https://api.grok.ai/v1",  # Grok API URL
        "model": "grok-2",  # Default Grok model
        "max_tokens": 1000
    }
}

# Review filtering thresholds
REVIEW_THRESHOLDS = {
    "min_confidence_score": 40,  # Minimum confidence score to consider review
    "min_domain_relevance": 0.3,  # Minimum domain relevance score (0-1)
    "expert_confidence_threshold": 80,  # Threshold to consider a reviewer an expert
    "domain_relevance_threshold": 0.2  # For generating artificial reviews
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
    ],
    "chart": {
        "type": "radar",
        "width": 8,
        "height": 6,
        "dpi": 300
    }
}

# File paths and directories
PATHS = {
    "projects_dir": "projects/",
    "ontology_file": "ontology.json",
    "output_dir": "output/",
    "visualizations_dir": "output/visualizations/",
    "logs_dir": "logs/"
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

# Default values for sentiment analysis
DEFAULT_SENTIMENT_SCORES = {
    "technical_feasibility": 3.0,
    "innovation": 3.0,
    "impact": 3.0,
    "implementation_complexity": 3.0,
    "scalability": 3.0,
    "return_on_investment": 3.0,
    "overall_sentiment": 3.0
}

# LLM prompts templates
LLM_PROMPTS = {
    "generate_final_review": """
    You are an expert reviewer synthesizing multiple perspectives on a hackathon project.
    
    Project: {project_name}
    Description: {project_description}
    
    Based on reviewer feedback, the project has received the following scores (on a scale of 1-5):
    {dimension_scores}
    
    Domain-specific insights:
    {domain_insights}
    
    Please synthesize these perspectives into a comprehensive final review of the project.
    The review should:
    1. Highlight the project's strengths and weaknesses
    2. Discuss different perspectives from various domains
    3. Provide constructive suggestions for improvement
    4. Summarize the overall assessment
    
    Keep the review balanced, constructive, and actionable. Length should be about 400-500 words.
    """,
    
    # Add other prompts here...
}
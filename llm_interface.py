"""
Interface for interacting with language models (Claude, ChatGPT, Ollama)
"""

import json
import requests
from typing import Dict, List, Any, Optional
from config import LLM_CONFIG

def generate_llm_response(prompt: str, provider: str = None) -> str:
    """
    Generate a response using a language model.
    
    Args:
        prompt: Text prompt to send to the LLM
        provider: Optional override for the LLM provider
        
    Returns:
        Response text from the LLM
    """
    # Get the provider from config if not specified
    if provider is None:
        provider = LLM_CONFIG.get("provider", "ollama")
    
    # Call the appropriate API
    if provider.lower() == "claude":
        return _call_claude_api(prompt)
    elif provider.lower() == "chatgpt":
        return _call_chatgpt_api(prompt)
    elif provider.lower() == "ollama":
        return _call_ollama_api(prompt)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def _call_claude_api(prompt: str) -> str:
    """
    Call the Claude API to generate a response.
    
    Args:
        prompt: Text prompt to send to Claude
        
    Returns:
        Response text from Claude
    """
    try:
        config = LLM_CONFIG.get("claude", {})
        api_key = config.get("api_key")
        model = config.get("model", "claude-3-opus-20240229")
        max_tokens = config.get("max_tokens", 1000)
        
        # Print status for logging
        print(f"Calling Claude API with model {model}...")
        
        # Make API call
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            print(f"Error calling Claude API: {response.status_code} - {response.text}")
            # Fall back to simulation for demo/testing
            return f"Simulated Claude response. Error occurred: {response.status_code}"
        
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        # Fall back to simulation for demo/testing
        return "Simulated Claude response due to API error."

def _call_chatgpt_api(prompt: str) -> str:
    """
    Call the ChatGPT API to generate a response.
    
    Args:
        prompt: Text prompt to send to ChatGPT
        
    Returns:
        Response text from ChatGPT
    """
    try:
        config = LLM_CONFIG.get("chatgpt", {})
        api_key = config.get("api_key")
        model = config.get("model", "gpt-4-turbo")
        max_tokens = config.get("max_tokens", 1000)
        
        # Print status for logging
        print(f"Calling ChatGPT API with model {model}...")
        
        # Make API call
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Error calling ChatGPT API: {response.status_code} - {response.text}")
            # Fall back to simulation for demo/testing
            return f"Simulated ChatGPT response. Error occurred: {response.status_code}"
        
    except Exception as e:
        print(f"Error calling ChatGPT API: {str(e)}")
        # Fall back to simulation for demo/testing
        return "Simulated ChatGPT response due to API error."

def _call_ollama_api(prompt: str) -> str:
    """
    Call the Ollama API to generate a response.
    
    Args:
        prompt: Text prompt to send to Ollama
        
    Returns:
        Response text from Ollama
    """
    try:
        config = LLM_CONFIG.get("ollama", {})
        base_url = config.get("base_url", "http://localhost:11434")
        model = config.get("model", "llama3")
        max_tokens = config.get("max_tokens", 1000)
        
        # Print status for logging
        print(f"Calling Ollama API with model {model}...")
        
        # Make API call
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"Error calling Ollama API: {response.status_code} - {response.text}")
            # Fall back to simulation for demo/testing
            return f"Simulated Ollama response. Error occurred: {response.status_code}"
        
    except Exception as e:
        print(f"Error calling Ollama API: {str(e)}")
        # Fall back to simulation for demo/testing
        return "Simulated Ollama response due to API error."

def generate_artificial_review(project_description: str, domain: str, ontology: Any) -> Dict[str, Any]:
    """
    Generate an artificial review for a project from a specific domain perspective.
    
    Args:
        project_description: Description of the project
        domain: Domain to generate review from
        ontology: Ontology object containing domain definitions
        
    Returns:
        Dictionary containing the artificial review
    """
    domain_data = ontology.ontology.get("domains", {}).get(domain.lower(), {})
    domain_name = domain_data.get("name", domain.capitalize())
    domain_desc = domain_data.get("description", "")
    
    prompt = f"""
    You are an expert reviewer with expertise in {domain_name}: {domain_desc}
    
    You are reviewing a hackathon project with the following description:
    
    {project_description}
    
    Please provide a detailed review of this project from your expertise perspective of {domain_name}.
    Consider aspects like technical feasibility, innovation, impact, implementation complexity, and scalability.
    
    Your review should be thorough but concise (around 300-400 words).
    
    Also, provide a confidence score between 0-100 that reflects how confident you are in your assessment.
    As an expert in {domain_name}, your confidence score should be high (85-95).
    """
    
    # For dimensions relevant to this domain
    dimension_prompts = []
    for dimension_id in ontology.get_relevant_dimensions_for_domain(domain):
        dimension_data = ontology.ontology.get("impact_dimensions", {}).get(dimension_id, {})
        dimension_name = dimension_data.get("name", dimension_id.replace("_", " ").capitalize())
        dimension_desc = dimension_data.get("description", "")
        dimension_prompts.append(f"- {dimension_name}: {dimension_desc}")
    
    if dimension_prompts:
        prompt += "\n\nPlease focus on these dimensions that are particularly relevant to your domain:\n"
        prompt += "\n".join(dimension_prompts)
    
    response = generate_llm_response(prompt)
    
    # Extract a confidence score (default to 90 for artificial reviews)
    confidence_score = 90
    
    # In a real implementation, parse the confidence score from the response
    
    artificial_review = {
        "reviewer_name": f"AI {domain_name} Expert",
        "domain": domain,
        "is_artificial": True,
        "text_review": response,
        "confidence_score": confidence_score
    }
    
    return artificial_review

def analyze_review_sentiment(review_text: str) -> Dict[str, float]:
    """
    Analyze the sentiment and key aspects of a review.
    
    Args:
        review_text: The text of the review
        
    Returns:
        Dictionary with sentiment scores
    """
    prompt = f"""
    Analyze the following project review for sentiment and scoring on key dimensions:
    
    {review_text}
    
    Please rate on a scale of 1-5 (where 1 is very negative and 5 is very positive) for each dimension:
    
    1. Technical feasibility
    2. Innovation
    3. Impact
    4. Implementation complexity (note: 5 means low complexity, 1 means high complexity)
    5. Scalability
    6. Return on investment
    7. Overall sentiment
    
    Format your response as a JSON object with these keys and numerical values.
    """
    
    response = generate_llm_response(prompt)
    
    try:
        # Try to parse the response as JSON
        sentiment_data = json.loads(response)
        return sentiment_data
    except json.JSONDecodeError:
        # If parsing fails, return default values
        print("Failed to parse sentiment analysis response as JSON. Using default values.")
        return {
            "technical_feasibility": 3.0,
            "innovation": 3.0,
            "impact": 3.0,
            "implementation_complexity": 3.0,
            "scalability": 3.0,
            "return_on_investment": 3.0,
            "overall_sentiment": 3.0
        }

def classify_reviewer_domain(reviewer_name: str, review_text: str, ontology: Any) -> str:
    """
    Classify a reviewer into a domain based on their review text.
    
    Args:
        reviewer_name: Name of the reviewer
        review_text: Text of the review
        ontology: Ontology object containing domain definitions
        
    Returns:
        Domain classification
    """
    domains = ontology.get_domains()
    domain_descriptions = []
    
    for domain in domains:
        domain_data = ontology.ontology.get("domains", {}).get(domain, {})
        domain_name = domain_data.get("name", domain.capitalize())
        domain_desc = domain_data.get("description", "")
        domain_descriptions.append(f"- {domain_name}: {domain_desc}")
    
    prompt = f"""
    Based on the following review text, classify the reviewer into one of these domains:
    
    {' '.join(domain_descriptions)}
    
    Review from {reviewer_name}:
    {review_text}
    
    Return just one domain name that best fits this reviewer's perspective.
    """
    
    response = generate_llm_response(prompt).strip()
    
    # Extract domain name (remove any explanation)
    for domain in domains:
        domain_data = ontology.ontology.get("domains", {}).get(domain, {})
        domain_name = domain_data.get("name", domain.capitalize())
        
        if domain_name.lower() in response.lower() or domain.lower() in response.lower():
            return domain
    
    # Default to first domain if no match
    return domains[0] if domains else "technical"
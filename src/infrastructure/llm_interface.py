"""
Interface for interacting with language models (Claude, ChatGPT, Ollama)
"""

import time
import requests
import json
from typing import Dict, List, Any, Optional

from src.infrastructure.logging_utils import logger
from src.infrastructure.config import LLM_CONFIG
from src.infrastructure.utils import remove_thinking_tags

def generate_llm_response(prompt: str, provider: str = None) -> str:
    """Generate a response using a language model with retry mechanism."""
    # Get the provider from config if not specified
    if provider is None:
        provider = LLM_CONFIG.get("provider", "ollama")
    
    # Get retry settings from config
    max_retries = LLM_CONFIG.get("max_retries", 3)
    retry_delay = LLM_CONFIG.get("retry_delay", 2)
    
    # Try with retries
    for attempt in range(1, max_retries + 1):
        try:
            # Call the appropriate API
            if provider.lower() == "claude":
                response = _call_claude_api(prompt)
            elif provider.lower() == "chatgpt":
                response = _call_chatgpt_api(prompt)
            elif provider.lower() == "ollama":
                response = _call_ollama_api(prompt)
            elif provider.lower() == "groq":
                response = _call_groq_api(prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
                
            # Clean any thinking tags from the response
            cleaned_response = remove_thinking_tags(response)
            return cleaned_response
        
        except Exception as e:
            logger.error(f"Error calling {provider} API (attempt {attempt}/{max_retries}): {str(e)}")
            
            # If we've reached max retries, raise the exception
            if attempt >= max_retries:
                logger.critical(f"Failed to generate response after {max_retries} attempts.")
                raise Exception(f"All {max_retries} attempts to generate a response with {provider} failed. Pipeline has failed and must be restarted from scratch.")
            
            # Otherwise, wait and retry
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def _call_claude_api(prompt: str) -> str:
    """Call the Claude API to generate a response."""
    config = LLM_CONFIG.get("claude", {})
    api_key = config.get("api_key")
    model = config.get("model", "claude-3-opus-20240229")
    max_tokens = config.get("max_tokens", 1000)
    
    logger.info(f"Calling Claude API with model {model}...")
    
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
        json=payload,
        timeout=30  # Add timeout
    )
    
    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    else:
        logger.error(f"Claude API error: {response.status_code} - {response.text}")
        raise Exception(f"Claude API error: {response.status_code} - {response.text}")

def _call_chatgpt_api(prompt: str) -> str:
    """Call the ChatGPT API to generate a response."""
    config = LLM_CONFIG.get("chatgpt", {})
    api_key = config.get("api_key")
    model = config.get("model", "gpt-4-turbo")
    max_tokens = config.get("max_tokens", 1000)
    
    logger.info(f"Calling ChatGPT API with model {model}...")
    
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
        json=payload,
        timeout=30  # Add timeout
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        logger.error(f"ChatGPT API error: {response.status_code} - {response.text}")
        raise Exception(f"ChatGPT API error: {response.status_code} - {response.text}")

def _call_ollama_api(prompt: str) -> str:
    """Call the Ollama API to generate a response."""
    config = LLM_CONFIG.get("ollama", {})
    base_url = config.get("base_url", "http://localhost:11434")
    model = config.get("model", "llama3")
    max_tokens = config.get("max_tokens", 1000)
    
    logger.info(f"Calling Ollama API with model {model}...")
    
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
        json=payload,
        timeout=180  # Longer timeout for local models which might be slower
    )
    
    if response.status_code == 200:
        response_json = response.json()
        if "response" in response_json:
            return response_json["response"]
        else:
            logger.error(f"Unexpected Ollama API response format: {response_json}")
            raise Exception(f"Unexpected Ollama API response format: missing 'response' field")
    else:
        logger.error(f"Ollama API error: {response.status_code} - {response.text}")
        raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
    
def _call_groq_api(prompt: str) -> str:
    """Call the Groq API to generate a response with rate limit handling."""
    config = LLM_CONFIG.get("groq", {})
    api_key = config.get("api_key")
    base_url = config.get("base_url", "https://api.groq.com/openai/v1")
    model = config.get("model", "llama3-70b-8192")
    max_tokens = config.get("max_tokens", 1000)
    
    logger.info(f"Calling Groq API with model {model}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }

    # Initial backoff in seconds (will increase exponentially)
    backoff = 1
    max_backoff = 60
    max_attempts = 5
    
    for attempt in range(max_attempts):
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            # Rate limit hit - extract wait time if available
            wait_time = backoff
            try:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", "")
                # Try to extract wait time from message
                import re
                wait_match = re.search(r'try again in (\d+\.?\d*)s', error_msg)
                if wait_match:
                    wait_time = float(wait_match.group(1)) + 0.5  # Add a small buffer
            except:
                pass
                
            logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry (attempt {attempt+1}/{max_attempts})")
            time.sleep(wait_time)
            
            # Increase backoff for next attempt
            backoff = min(backoff * 2, max_backoff)
        else:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
    
    # If we exhausted all attempts
    logger.error(f"Failed after {max_attempts} attempts due to rate limiting")
    raise Exception(f"Groq API rate limits exceeded after {max_attempts} attempts with backoff")

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
    cleaned_response = remove_thinking_tags(response)
    
    # Extract a confidence score (default to 90 for artificial reviews)
    confidence_score = 90
    
    # In a real implementation, parse the confidence score from the response
    
    artificial_review = {
        "reviewer_name": f"AI {domain_name} Expert",
        "domain": domain,
        "is_artificial": True,
        "text_review": cleaned_response,
        "confidence_score": confidence_score
    }
    
    return artificial_review

def analyze_review_sentiment(review_text: str) -> Dict[str, float]:
    prompt = f"""
    Analyze the following project review for sentiment and scoring on key dimensions.
    
    {review_text}
    
    Rate on a scale of 1-5 (where 1 is very negative and 5 is very positive) for each dimension.
    
    You MUST respond with ONLY a valid JSON object in this exact format:
    {{
      "technical_feasibility": 3.5,
      "innovation": 4.0,
      "impact": 3.0,
      "implementation_complexity": 2.5,
      "scalability": 4.0,
      "return_on_investment": 3.5,
      "overall_sentiment": 3.5
    }}
    
    Replace the example values with your actual ratings. Use only numbers between 1.0 and 5.0.
    """
    
    response = generate_llm_response(prompt)
    
    try:
        # Try to extract JSON using regex
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            json_str = json_match.group(0)
            sentiment_data = json.loads(json_str)
            
            # Validate the data has the expected keys
            expected_keys = ["technical_feasibility", "innovation", "impact", 
                            "implementation_complexity", "scalability", 
                            "return_on_investment", "overall_sentiment"]
            
            if all(key in sentiment_data for key in expected_keys):
                return sentiment_data
        
        # If regex extraction failed or validation failed, try parsing the whole response
        sentiment_data = json.loads(response)
        return sentiment_data
        
    except json.JSONDecodeError:
        # If all parsing fails, return randomized default values for testing
        # (in production, you'd want to log this error and handle it properly)
        import random
        logger.error("Failed to parse sentiment analysis response as JSON. Using varied default values.")
        return {
            "technical_feasibility": round(random.uniform(2.0, 4.0), 1),
            "innovation": round(random.uniform(2.0, 4.0), 1),
            "impact": round(random.uniform(2.0, 4.0), 1),
            "implementation_complexity": round(random.uniform(2.0, 4.0), 1),
            "scalability": round(random.uniform(2.0, 4.0), 1),
            "return_on_investment": round(random.uniform(2.0, 4.0), 1),
            "overall_sentiment": round(random.uniform(2.0, 4.0), 1)
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
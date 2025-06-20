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
        timeout=30
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
        timeout=30
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
        timeout=180
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
            wait_time = backoff
            try:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", "")
                import re
                wait_match = re.search(r'try again in (\d+\.?\d*)s', error_msg)
                if wait_match:
                    wait_time = float(wait_match.group(1)) + 0.5
            except:
                pass
                
            logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry (attempt {attempt+1}/{max_attempts})")
            time.sleep(wait_time)
            backoff = min(backoff * 2, max_backoff)
        else:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
    
    logger.error(f"Failed after {max_attempts} attempts due to rate limiting")
    raise Exception(f"Groq API rate limits exceeded after {max_attempts} attempts with backoff")

# Updated functions that use dynamic prompts from ontology

def generate_artificial_review(project_description: str, domain: str, ontology: Any) -> Dict[str, Any]:
    """
    Generate an artificial review for a project from a specific domain perspective.
    Now uses dynamic prompts from the ontology.
    
    Args:
        project_description: Description of the project
        domain: Domain to generate review from
        ontology: Ontology object with prompt generator
        
    Returns:
        Dictionary containing the artificial review
    """
    # Use dynamic prompt generator
    prompt = ontology.prompt_generator.generate_artificial_review_prompt(
        project_description, domain
    )
    
    response = generate_llm_response(prompt)
    cleaned_response = remove_thinking_tags(response)
    
    # Parse response for review and confidence
    confidence_score = 90  # Default
    review_text = cleaned_response
    
    # Try to extract confidence score from response
    import re
    confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', cleaned_response)
    if confidence_match:
        confidence_score = int(confidence_match.group(1))
        # Remove confidence line from review text
        review_text = re.sub(r'CONFIDENCE:\s*\d+', '', cleaned_response).strip()
    
    # Remove "REVIEW:" prefix if present
    review_text = re.sub(r'^REVIEW:\s*', '', review_text).strip()
    
    artificial_review = {
        "reviewer_name": f"AI {domain.capitalize()} Expert",
        "domain": domain,
        "is_artificial": True,
        "text_review": review_text,
        "confidence_score": confidence_score
    }
    
    return artificial_review

def analyze_review_sentiment(review_text: str, ontology: Any = None) -> Dict[str, float]:
    """
    Analyze review sentiment using dynamic prompts from ontology.
    
    Args:
        review_text: Text of the review to analyze
        ontology: Ontology object with prompt generator (optional for backward compatibility)
        
    Returns:
        Dictionary of sentiment scores by dimension
    """
    if ontology and hasattr(ontology, 'prompt_generator'):
        # Use dynamic prompt from ontology
        prompt = ontology.prompt_generator.generate_sentiment_analysis_prompt(review_text)
    else:
        # Fallback to static prompt for backward compatibility
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
            
            # Validate basic structure
            if isinstance(sentiment_data, dict) and len(sentiment_data) > 0:
                return sentiment_data
        
        # If regex extraction failed, try parsing the whole response
        sentiment_data = json.loads(response)
        return sentiment_data
        
    except json.JSONDecodeError:
        # If all parsing fails, return default values
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
    Now uses dynamic prompts from the ontology.
    
    Args:
        reviewer_name: Name of the reviewer
        review_text: Text of the review
        ontology: Ontology object with prompt generator
        
    Returns:
        Domain classification
    """
    # Use dynamic prompt generator
    prompt = ontology.prompt_generator.generate_reviewer_classification_prompt(
        reviewer_name, review_text
    )
    
    response = generate_llm_response(prompt).strip()
    
    # Validate response against available domains
    available_domains = ontology.get_domains()
    response_lower = response.lower()
    
    for domain in available_domains:
        if domain.lower() in response_lower:
            return domain
    
    # Default to first domain if no match
    return available_domains[0] if available_domains else "technical"

def generate_final_review_from_ontology(project_info: Dict[str, Any], 
                                      reviews_data: List[Dict[str, Any]], 
                                      feedback_scores: Dict[str, float],
                                      ontology: Any) -> str:
    """
    Generate final review text using dynamic prompts from ontology.
    
    Args:
        project_info: Project information dictionary
        reviews_data: List of review data
        feedback_scores: Calculated feedback scores
        ontology: Ontology object with prompt generator
        
    Returns:
        Generated final review text
    """
    prompt = ontology.prompt_generator.generate_final_review_synthesis_prompt(
        project_info, reviews_data, feedback_scores
    )
    
    return generate_llm_response(prompt)
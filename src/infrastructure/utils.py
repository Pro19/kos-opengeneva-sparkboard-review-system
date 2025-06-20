import os
import re
import json
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.infrastructure.logging_utils import logger

def parse_markdown_file(file_path: str) -> Dict[str, str]:
    """
    Parse markdown files into structured data.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Dictionary with parsed content
    """
    from src.infrastructure.logging_utils import logger
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract sections based on markdown headers
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('# '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[2:].strip()
            current_content = []
        elif line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            # Remove trailing colon if present (common in markdown formats)
            header_text = line[3:].strip()
            if header_text.endswith(':'):
                header_text = header_text[:-1].strip()
            current_section = header_text
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Add the last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Log the parsed sections for debugging
    logger.debug(f"Parsed sections from {file_path}: {list(sections.keys())}")
    
    return sections

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two text strings."""
    
    # Validate inputs
    if not text1 or not text2:
        logger.warning("Empty text provided for similarity calculation")
        raise ValueError("Both text strings must be non-empty for similarity calculation")
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        logger.debug(f"Calculated text similarity: {similarity}")
        return float(similarity)  # Ensure we return a float
    
    except ImportError as e:
        logger.error(f"Missing dependency for text similarity: {str(e)}")
        raise ValueError(f"Required dependency not available: {str(e)}")
    
    except ValueError as e:
        logger.error(f"Vectorization error in text similarity: {str(e)}")
        raise ValueError(f"Error in text vectorization: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in text similarity calculation: {str(e)}")
        raise ValueError(f"Error calculating text similarity: {str(e)}")

def extract_confidence_score(review_content: Dict[str, str]) -> int:
    """
    Extract the confidence score from review content.
    
    Args:
        review_content: Parsed review content
        
    Returns:
        Confidence score as an integer (0-100)
    """
    confidence_text = review_content.get('Confidence score (0-100) _How much confidence do you have in your own review?_', '0')
    
    # Extract numbers from the text
    numbers = re.findall(r'\d+', confidence_text)
    
    if numbers:
        score = int(numbers[0])
        return min(max(score, 0), 100)  # Ensure score is between 0 and 100
    
    return 0

def extract_links(review_content: Dict[str, str]) -> Dict[str, str]:
    """
    Extract external links from reviewer information.
    
    Args:
        review_content: Parsed review content
        
    Returns:
        Dictionary of link types and URLs
    """
    links_section = review_content.get('Links', '')
    links = {}
    
    # Extract links using regex
    linkedin_match = re.search(r'LinkedIn\s*:\s*(https?://[^\s]+)', links_section)
    scholar_match = re.search(r'Google Scholar\s*:\s*(https?://[^\s]+)', links_section)
    github_match = re.search(r'Github\s*:\s*(https?://[^\s]+)', links_section)
    
    if linkedin_match:
        links['linkedin'] = linkedin_match.group(1)
    if scholar_match:
        links['google_scholar'] = scholar_match.group(1)
    if github_match:
        links['github'] = github_match.group(1)
    
    return links

def save_json(data: Any, file_path: str) -> None:
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save
        file_path: Path to save the JSON file
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def load_json(file_path: str) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded JSON data
    """
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def remove_thinking_tags(text: str) -> str:
    """
    Remove thinking tags and their contents from LLM-generated text.
    
    Args:
        text: Raw text that might contain thinking tags
        
    Returns:
        Clean text with thinking tags and their contents removed
    """
    import re
    from src.infrastructure.logging_utils import logger
    
    # Patterns to look for
    patterns = [
        r'<think>[\s\S]*?</think>',  # <think> tags
        r'<thinking>[\s\S]*?</thinking>',  # <thinking> tags
        r'<reasoning>[\s\S]*?</reasoning>',  # <reasoning> tags
        r'<internal>[\s\S]*?</internal>'  # <internal> tags
    ]
    
    original_length = len(text)
    
    # Apply each pattern
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    
    # Check if we made any replacements
    if len(text) < original_length:
        logger.info(f"Removed {original_length - len(text)} characters of thinking/reasoning tags")
    
    return text
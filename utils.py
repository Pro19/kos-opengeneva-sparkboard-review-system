"""
Utility functions for the hackathon review system.
"""

import os
import re
import json
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def parse_markdown_file(file_path: str) -> Dict[str, str]:
    """
    Parse markdown files into structured data.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Dictionary with parsed content
    """
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
            current_section = line[3:].strip()
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Add the last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    # This is a simplified version - in production, use a proper embedding model
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        return 0.0

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

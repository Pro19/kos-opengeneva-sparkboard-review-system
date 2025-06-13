"""
Reviewer classification and profiling for hackathon review system.
"""

import os
import re
from typing import Dict, List, Any, Optional

from src.infrastructure.utils import extract_links, calculate_text_similarity
from src.infrastructure.config import REVIEW_THRESHOLDS
from src.infrastructure.llm_interface import classify_reviewer_domain

class ReviewerProfile:
    """Class for managing reviewer profiles and expertise assessment."""
    
    def __init__(self, ontology):
        """
        Initialize the reviewer profiler.
        
        Args:
            ontology: Ontology object with domain definitions
        """
        self.ontology = ontology
        self.reviewer_profiles = {}  # Cache for reviewer profiles
    
    def classify_reviewer(self, reviewer_name: str, review_text: str, confidence_score: int, links: Dict[str, str] = None) -> Dict[str, Any]:
        """Classify a reviewer based on their review and profile information."""
        from logging_utils import logger
        
        # Check if we already have a profile for this reviewer
        if reviewer_name in self.reviewer_profiles:
            return self.reviewer_profiles[reviewer_name]
        
        # Determine expertise level based on confidence score
        expertise_level = self.ontology.get_expertise_level(confidence_score)
        
        # Classify reviewer into a domain
        domain = classify_reviewer_domain(reviewer_name, review_text, self.ontology)
        
        # Check external profiles if links are provided and not empty
        external_data = {}
        if links and any(links.values()):
            logger.info(f"External links provided for {reviewer_name}, checking profiles...")
            external_data = self._check_external_profiles(links)
            # Use external profile data to enhance domain classification if possible
            # (Keeping mock implementation for now as requested)
        else:
            logger.info(f"No external links provided for {reviewer_name}, relying on confidence score ({confidence_score}) and review text...")
            # When no links are provided, we rely entirely on confidence score and review text
        
        # Create reviewer profile
        profile = {
            "name": reviewer_name,
            "domain": domain,
            "expertise_level": expertise_level,
            "confidence_score": confidence_score,
            "external_data": external_data
        }
        
        # Cache the profile
        self.reviewer_profiles[reviewer_name] = profile
        
        return profile
    
    def _check_external_profiles(self, links: Dict[str, str]) -> Dict[str, Any]:
        """
        Check external profiles for additional information.
        
        Args:
            links: Dictionary of external profile links
            
        Returns:
            Dictionary with data from external profiles
        """
        external_data = {}
        
        # This would involve API calls to external services or web scraping
        # For this implementation, we'll simulate the data
        
        if 'linkedin' in links:
            # Simulate LinkedIn profile data
            external_data['linkedin'] = {
                "title": "Simulated Job Title",
                "industry": "Simulated Industry",
                "experience_years": 5,
                "skills": ["Simulated Skill 1", "Simulated Skill 2"]
            }
        
        if 'google_scholar' in links:
            # Simulate Google Scholar data
            external_data['google_scholar'] = {
                "publications": 10,
                "citations": 100,
                "h_index": 5,
                "research_areas": ["Simulated Area 1", "Simulated Area 2"]
            }
        
        if 'github' in links:
            # Simulate GitHub data
            external_data['github'] = {
                "repositories": 15,
                "stars": 50,
                "contributions": 500,
                "languages": ["Simulated Language 1", "Simulated Language 2"]
            }
        
        return external_data
    
    def check_domain_relevance(self, project_description: str, domain: str) -> float:
        """
        Check the relevance of a domain to a project.
        
        Args:
            project_description: Description of the project
            domain: Domain to check relevance for
            
        Returns:
            Relevance score (0-1)
        """
        return self.ontology.calculate_domain_relevance(project_description, domain)
    
    def should_accept_review(self, review: Dict[str, Any], project_description: str) -> bool:
        """
        Determine if a review should be accepted based on relevance and confidence.
        
        Args:
            review: Review data dictionary
            project_description: Project description
            
        Returns:
            Boolean indicating if review should be accepted
        """
        domain = review.get("domain")
        confidence_score = review.get("confidence_score", 0)
        
        # Always accept artificial reviews
        if review.get("is_artificial", False):
            return True
        
        # Check confidence score threshold
        min_confidence = REVIEW_THRESHOLDS.get("min_confidence_score", 40)
        if confidence_score < min_confidence:
            return False
        
        # Check domain relevance
        if domain:
            relevance_score = self.check_domain_relevance(project_description, domain)
            review["relevance_score"] = relevance_score
            
            min_relevance = REVIEW_THRESHOLDS.get("min_domain_relevance", 0.3)
            
            # Low confidence and low relevance -> reject
            if confidence_score < REVIEW_THRESHOLDS.get("expert_confidence_threshold", 80) and relevance_score < min_relevance:
                return False
        
        return True
    
    def filter_reviews(self, project) -> None:
        """
        Filter reviews for a project based on relevance and confidence.
        
        Args:
            project: Project object with reviews
        """
        project_description = project.get_full_description()
        
        for review in project.reviews:
            # First classify the reviewer if not already done
            if not review.get("domain"):
                reviewer_profile = self.classify_reviewer(
                    review.get("reviewer_name", "Anonymous"),
                    review.get("text_review", ""),
                    review.get("confidence_score", 0),
                    review.get("links", {})
                )
                
                review["domain"] = reviewer_profile.get("domain")
                review["expertise_level"] = reviewer_profile.get("expertise_level")
            
            # Determine if the review should be accepted
            is_accepted = self.should_accept_review(review, project_description)
            review["is_accepted"] = is_accepted
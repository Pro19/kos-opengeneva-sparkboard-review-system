"""
Project data structures and parsing for hackathon review system.
"""

import os
import glob
from typing import Dict, List, Any, Optional

from src.infrastructure.utils import parse_markdown_file
from src.infrastructure.config import PATHS

class Project:
    """Class representing a hackathon project."""
    
    def __init__(self, project_id: str, project_dir: str):
        """
        Initialize a project.
        
        Args:
            project_id: Unique identifier for the project
            project_dir: Directory path containing project files
        """
        self.project_id = project_id
        self.project_dir = project_dir
        self.description_file = os.path.join(project_dir, "description.md")
        
        self.project_data = self._load_project_data()
        self.reviews = self._load_reviews()
        
        # Additional attributes to be set later
        self.project_type = None
        self.domain_relevance_scores = {}
        self.final_review = None
        self.feedback_scores = {}
    
    def _load_project_data(self) -> Dict[str, Any]:
        """
        Load project data from description file.
        
        Returns:
            Dictionary containing project data
        """
        if not os.path.exists(self.description_file):
            print(f"Warning: Description file not found at {self.description_file}")
            return {
                "name": self.project_id,
                "description": "",
                "hackathon_id": "",
                "work_done": ""
            }
        
        sections = parse_markdown_file(self.description_file)
        
        # Map section names to standardized keys
        return {
            "name": sections.get("Project Name", self.project_id),
            "description": sections.get("Project Description (max 400 words)", ""),
            "hackathon_id": sections.get("Hackathon ID", ""),
            "work_done": sections.get("Explain the work you've done so far", "")
        }
    
    def _load_reviews(self) -> List[Dict[str, Any]]:
        """Load all review files for the project."""
        from src.infrastructure.logging_utils import logger
        
        reviews = []
        review_files = glob.glob(os.path.join(self.project_dir, "review*.md"))
        
        for review_file in review_files:
            try:
                review_content = parse_markdown_file(review_file)
                
                # Extract reviewer information
                reviewer_name = review_content.get("Reviewer name", "Anonymous")
                
                # Extract links section
                links = review_content.get("Links", {})
                
                # Extract review text
                review_text = review_content.get("Text review of the project (max 400 words)", "")
                
                # Extract confidence score - try multiple possible key formats
                confidence_score = 0
                confidence_keys = [
                    "Confidence score (0-100) _How much confidence do you have in your own review?_",
                    "Confidence score (0-100)",
                    "Confidence score"
                ]
                
                for key in confidence_keys:
                    if key in review_content:
                        confidence_score_text = review_content[key]
                        confidence_score = self._parse_confidence_score(confidence_score_text)
                        if confidence_score > 0:
                            break
                
                # Log the extracted confidence score
                logger.info(f"Extracted confidence score {confidence_score} for reviewer {reviewer_name}")
                
                review_data = {
                    "reviewer_name": reviewer_name,
                    "links": links,
                    "text_review": review_text,
                    "confidence_score": confidence_score,
                    "file_path": review_file,
                    "is_artificial": False,
                    # These fields will be populated during analysis
                    "domain": None,
                    "expertise_level": None,
                    "relevance_score": None,
                    "sentiment_scores": None,
                    "is_accepted": None
                }
                
                reviews.append(review_data)
                
            except Exception as e:
                logger.error(f"Error parsing review file {review_file}: {str(e)}")
        
        return reviews
    
    def _parse_confidence_score(self, confidence_text: str) -> int:
        """
        Parse confidence score from text.
        
        Args:
            confidence_text: Text containing confidence score
            
        Returns:
            Integer confidence score (0-100)
        """
        from src.infrastructure.logging_utils import logger
        
        logger.debug(f"Parsing confidence score from: '{confidence_text}'")
        
        # Try to extract a number from the text
        try:
            # First, check if it's already a number
            if confidence_text.isdigit():
                score = int(confidence_text)
                return max(0, min(100, score))
                
            # Extract numbers using regex
            import re
            numbers = re.findall(r'\d+', confidence_text)
            if numbers:
                score = int(numbers[0])
                logger.debug(f"Found confidence score: {score}")
                return max(0, min(100, score))  # Ensure in range 0-100
                
            logger.warning(f"No valid confidence score found in: '{confidence_text}'")
        except Exception as e:
            logger.error(f"Error parsing confidence score: {str(e)}")
        
        return 0  # Default if no valid score found
    
    def add_artificial_review(self, review_data: Dict[str, Any]) -> None:
        """
        Add an artificially generated review to the project.
        
        Args:
            review_data: Dictionary containing artificial review data
        """
        # Ensure it's marked as artificial
        review_data["is_artificial"] = True
        
        # Add to reviews list
        self.reviews.append(review_data)
    
    def get_full_description(self) -> str:
        """
        Get the full project description text.
        
        Returns:
            Combined project description text
        """
        description = f"Project Name: {self.project_data.get('name', '')}\n\n"
        description += f"Project Description: {self.project_data.get('description', '')}\n\n"
        description += f"Work Done So Far: {self.project_data.get('work_done', '')}"
        
        return description
    
    def get_accepted_reviews(self) -> List[Dict[str, Any]]:
        """
        Get all accepted reviews.
        
        Returns:
            List of accepted review dictionaries
        """
        return [review for review in self.reviews if review.get("is_accepted", False)]
    
    def get_reviews_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get all reviews for a specific domain.
        
        Args:
            domain: Domain to filter by
            
        Returns:
            List of review dictionaries for the specified domain
        """
        return [
            review for review in self.reviews 
            if review.get("domain") == domain and review.get("is_accepted", False)
        ]
    
    def set_feedback_scores(self, scores: Dict[str, float]) -> None:
        """
        Set the feedback scores for the project.
        
        Args:
            scores: Dictionary of dimension names to score values
        """
        self.feedback_scores = scores
    
    def set_final_review(self, review_text: str) -> None:
        """
        Set the final review text for the project.
        
        Args:
            review_text: Final aggregated review text
        """
        self.final_review = review_text

def load_all_projects() -> List[Project]:
    """
    Load all projects from the projects directory.
    
    Returns:
        List of Project objects
    """
    projects = []
    projects_dir = PATHS.get("projects_dir", "projects/")
    
    if not os.path.exists(projects_dir):
        print(f"Warning: Projects directory not found at {projects_dir}")
        return []
    
    # Get all subdirectories in the projects directory
    project_dirs = [d for d in os.listdir(projects_dir) 
                   if os.path.isdir(os.path.join(projects_dir, d))]
    
    for project_dir_name in project_dirs:
        project_id = project_dir_name
        project_dir_path = os.path.join(projects_dir, project_dir_name)
        
        # Create Project object
        project = Project(project_id, project_dir_path)
        projects.append(project)
    
    return projects
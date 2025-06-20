import os
import re
from typing import Dict, List, Any, Optional

from src.infrastructure.utils import extract_links, calculate_text_similarity
from src.infrastructure.config import REVIEW_THRESHOLDS
from src.infrastructure.llm_interface import classify_reviewer_domain

class ReviewerProfile:
    def __init__(self, ontology):
        """
        Initialize the reviewer profiler.
        
        Args:
            ontology: RDF Ontology object with dynamic capabilities
        """
        self.ontology = ontology
        self.reviewer_profiles = {}  # Cache for reviewer profiles
    
    def classify_reviewer(self, reviewer_name: str, review_text: str, confidence_score: int, links: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Classify a reviewer based on their review and profile information using RDF ontology.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text of the review
            confidence_score: Reviewer's confidence score (0-100)
            links: Optional external profile links
            
        Returns:
            Dictionary containing reviewer profile information
        """
        from src.infrastructure.logging_utils import logger
        
        # Check if we already have a profile for this reviewer
        if reviewer_name in self.reviewer_profiles:
            return self.reviewer_profiles[reviewer_name]
        
        # Determine expertise level based on confidence score using ontology
        expertise_level = self.ontology.get_expertise_level(confidence_score)
        
        # Classify reviewer into a domain using dynamic prompts from ontology
        domain = classify_reviewer_domain(reviewer_name, review_text, self.ontology)
        
        # Validate domain against available domains in ontology
        available_domains = self.ontology.get_domains()
        if domain not in available_domains:
            logger.warning(f"Classified domain '{domain}' not in ontology. Using closest match.")
            # Find closest match or default to first domain
            domain = self._find_closest_domain(domain, available_domains) or available_domains[0]
        
        # Check external profiles if links are provided and not empty
        external_data = {}
        if links and any(links.values()):
            logger.info(f"External links provided for {reviewer_name}, checking profiles...")
            external_data = self._check_external_profiles(links)
            # Use external profile data to enhance domain classification if possible
            enhanced_domain = self._enhance_domain_from_external(external_data, domain)
            if enhanced_domain:
                domain = enhanced_domain
        else:
            logger.info(f"No external links provided for {reviewer_name}, relying on confidence score ({confidence_score}) and review text...")
        
        # Get domain information from ontology for richer profiling
        domain_info = self.ontology.rdf_ontology.get_domain_by_id(domain)
        
        # Create reviewer profile
        profile = {
            "name": reviewer_name,
            "domain": domain,
            "domain_info": domain_info,  # Include rich domain information
            "expertise_level": expertise_level,
            "confidence_score": confidence_score,
            "external_data": external_data,
            "relevant_dimensions": self.ontology.get_relevant_dimensions_for_domain(domain)
        }
        
        # Cache the profile
        self.reviewer_profiles[reviewer_name] = profile
        
        logger.info(f"Classified {reviewer_name} as {expertise_level} {domain} reviewer")
        
        return profile
    
    def _find_closest_domain(self, classified_domain: str, available_domains: List[str]) -> Optional[str]:
        """Find the closest matching domain in the ontology."""
        classified_lower = classified_domain.lower()
        
        # Direct match
        for domain in available_domains:
            if domain.lower() == classified_lower:
                return domain
        
        # Partial match
        for domain in available_domains:
            if classified_lower in domain.lower() or domain.lower() in classified_lower:
                return domain
        
        # Check domain keywords
        for domain in available_domains:
            keywords = self.ontology.get_domain_keywords(domain)
            for keyword in keywords:
                if keyword.lower() in classified_lower or classified_lower in keyword.lower():
                    return domain
        
        return None
    
    def _enhance_domain_from_external(self, external_data: Dict[str, Any], current_domain: str) -> Optional[str]:
        """
        Enhance domain classification using external profile data.
        
        Args:
            external_data: Data from external profiles
            current_domain: Currently classified domain
            
        Returns:
            Enhanced domain or None if no enhancement needed
        """
        # This is a placeholder for actual external data analysis
        # In a real implementation, we would analyze LinkedIn titles, GitHub repos, etc.
        
        # For example, if LinkedIn shows "Software Engineer", reinforce technical domain
        linkedin_data = external_data.get('linkedin', {})
        if linkedin_data.get('title'):
            title = linkedin_data['title'].lower()
            if any(term in title for term in ['engineer', 'developer', 'technical']):
                return 'technical'
            elif any(term in title for term in ['doctor', 'physician', 'clinical']):
                return 'clinical'
            elif any(term in title for term in ['business', 'manager', 'entrepreneur']):
                return 'business'
            elif any(term in title for term in ['designer', 'design']):
                return 'design'
        
        return None  # No enhancement needed
    
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
        # For this implementation, we'll simulate realistic data based on common patterns
        
        if 'linkedin' in links and links['linkedin']:
            # Simulate LinkedIn profile data
            external_data['linkedin'] = {
                "title": "Senior Software Engineer",  # Simulated based on common patterns
                "industry": "Technology",
                "experience_years": 5,
                "skills": ["Python", "Machine Learning", "Software Development"],
                "company": "Tech Company",
                "verified": True
            }
        
        if 'google_scholar' in links and links['google_scholar']:
            # Simulate Google Scholar data
            external_data['google_scholar'] = {
                "publications": 12,
                "citations": 150,
                "h_index": 6,
                "research_areas": ["Machine Learning", "Healthcare Informatics"],
                "verified": True
            }
        
        if 'github' in links and links['github']:
            # Simulate GitHub data
            external_data['github'] = {
                "repositories": 25,
                "stars": 75,
                "contributions": 800,
                "languages": ["Python", "JavaScript", "TypeScript"],
                "top_repos": ["ml-healthcare-tool", "review-system"],
                "verified": True
            }
        
        return external_data
    
    def check_domain_relevance(self, project_description: str, domain: str) -> float:
        """
        Check the relevance of a domain to a project using RDF ontology.
        
        Args:
            project_description: Description of the project
            domain: Domain to check relevance for
            
        Returns:
            Relevance score (0-1)
        """
        return self.ontology.calculate_domain_relevance(project_description, domain)
    
    def should_accept_review(self, review: Dict[str, Any], project_description: str) -> bool:
        """
        Determine if a review should be accepted based on relevance and confidence using RDF ontology.
        
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
        
        # Check domain relevance using ontology
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
        Filter reviews for a project based on relevance and confidence using RDF ontology.
        
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
                review["domain_info"] = reviewer_profile.get("domain_info")
            
            # Determine if the review should be accepted
            is_accepted = self.should_accept_review(review, project_description)
            review["is_accepted"] = is_accepted
    
    def get_reviewer_insights(self, project) -> Dict[str, Any]:
        """
        Generate insights about reviewers for a project using ontology information.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary with reviewer insights
        """
        insights = {
            "total_reviewers": len(project.reviews),
            "accepted_reviewers": 0,
            "domain_coverage": {},
            "expertise_distribution": {},
            "confidence_stats": {
                "min": 100,
                "max": 0,
                "average": 0
            },
            "external_profiles": {
                "linkedin": 0,
                "github": 0,
                "google_scholar": 0
            }
        }
        
        confidence_scores = []
        
        for review in project.reviews:
            if review.get("is_accepted", False):
                insights["accepted_reviewers"] += 1
                
                # Domain coverage
                domain = review.get("domain", "unknown")
                if domain not in insights["domain_coverage"]:
                    # Get domain info from ontology
                    domain_info = self.ontology.rdf_ontology.get_domain_by_id(domain)
                    insights["domain_coverage"][domain] = {
                        "name": domain_info["name"] if domain_info else domain.capitalize(),
                        "count": 0,
                        "artificial_count": 0,
                        "description": domain_info["description"] if domain_info else ""
                    }
                
                insights["domain_coverage"][domain]["count"] += 1
                if review.get("is_artificial", False):
                    insights["domain_coverage"][domain]["artificial_count"] += 1
                
                # Expertise distribution
                expertise = review.get("expertise_level", "unknown")
                insights["expertise_distribution"][expertise] = insights["expertise_distribution"].get(expertise, 0) + 1
                
                # Confidence stats
                confidence = review.get("confidence_score", 0)
                confidence_scores.append(confidence)
                insights["confidence_stats"]["min"] = min(insights["confidence_stats"]["min"], confidence)
                insights["confidence_stats"]["max"] = max(insights["confidence_stats"]["max"], confidence)
                
                # External profiles
                if not review.get("is_artificial", False):
                    links = review.get("links", {})
                    for platform in ["linkedin", "github", "google_scholar"]:
                        if links.get(platform):
                            insights["external_profiles"][platform] += 1
        
        # Calculate average confidence
        if confidence_scores:
            insights["confidence_stats"]["average"] = sum(confidence_scores) / len(confidence_scores)
        
        return insights
    
    def get_missing_domain_recommendations(self, project) -> List[Dict[str, Any]]:
        """
        Get recommendations for missing domain coverage using ontology.
        
        Args:
            project: Project object
            
        Returns:
            List of recommendations for missing domains
        """
        # Get all available domains from ontology
        all_domains = self.ontology.get_domains()
        
        # Get covered domains
        covered_domains = set()
        for review in project.reviews:
            if review.get("is_accepted", False) and not review.get("is_artificial", False):
                domain = review.get("domain")
                if domain:
                    covered_domains.add(domain)
        
        # Find missing domains and check relevance
        missing_domains = []
        project_description = project.get_full_description()
        
        for domain in all_domains:
            if domain not in covered_domains:
                relevance = self.check_domain_relevance(project_description, domain)
                if relevance >= 0.2:  # Only recommend relevant domains
                    domain_info = self.ontology.rdf_ontology.get_domain_by_id(domain)
                    missing_domains.append({
                        "domain_id": domain,
                        "domain_name": domain_info["name"] if domain_info else domain.capitalize(),
                        "description": domain_info["description"] if domain_info else "",
                        "relevance_score": relevance,
                        "recommendation": f"Consider seeking a {domain_info['name'] if domain_info else domain} expert review"
                    })
        
        # Sort by relevance score
        missing_domains.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return missing_domains
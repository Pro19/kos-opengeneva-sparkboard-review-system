"""
Ontology management and generation for hackathon review system.
"""

import os
import json
from typing import Dict, List, Any, Optional
from config import PATHS, CORE_DOMAINS
from llm_interface import generate_llm_response

class Ontology:
    """
    Class for managing the ontology for the hackathon review system.
    """
    
    def __init__(self, load_existing: bool = True):
        """
        Initialize the ontology.
        
        Args:
            load_existing: Whether to load an existing ontology file
        """
        self.ontology_path = PATHS.get("ontology_file", "ontology.json")
        
        if load_existing and os.path.exists(self.ontology_path):
            self.load_ontology()
        else:
            self.create_initial_ontology()
    
    def load_ontology(self) -> None:
        """Load the ontology from file."""
        try:
            with open(self.ontology_path, 'r') as file:
                self.ontology = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Error loading ontology from {self.ontology_path}, creating new one.")
            self.create_initial_ontology()
    
    def save_ontology(self) -> None:
        """Save the ontology to file."""
        with open(self.ontology_path, 'w') as file:
            json.dump(self.ontology, file, indent=2)
    
    def create_initial_ontology(self) -> None:
        """Create an initial ontology structure."""
        self.ontology = {
            "domains": self._generate_domains(),
            "project_types": self._generate_project_types(),
            "impact_dimensions": self._generate_impact_dimensions(),
            "expertise_levels": self._generate_expertise_levels(),
            "review_dimensions": self._generate_review_dimensions(),
        }
        self.save_ontology()
    
    def _generate_domains(self) -> Dict[str, Dict[str, Any]]:
        """Generate initial domain definitions."""
        domains = {}
        
        # Core domains with definitions
        domains["technical"] = {
            "name": "Technical",
            "description": "Expertise in programming, software engineering, hardware development, or technical implementation",
            "keywords": ["programming", "software", "hardware", "development", "engineering", "technical", "code"],
            "subdomains": {
                "frontend": {"name": "Frontend Development", "keywords": ["UI", "UX", "web", "mobile", "frontend"]},
                "backend": {"name": "Backend Development", "keywords": ["server", "database", "API", "backend"]},
                "data_science": {"name": "Data Science", "keywords": ["machine learning", "AI", "data", "analytics"]},
                "devops": {"name": "DevOps", "keywords": ["deployment", "infrastructure", "cloud", "CI/CD"]}
            }
        }
        
        domains["clinical"] = {
            "name": "Clinical",
            "description": "Medical or healthcare expertise related to patient care, diagnosis, or treatment",
            "keywords": ["medical", "healthcare", "clinical", "patient", "diagnosis", "treatment", "doctor", "nurse"],
            "subdomains": {
                "primary_care": {"name": "Primary Care", "keywords": ["general practice", "family medicine"]},
                "specialty": {"name": "Medical Specialties", "keywords": ["cardiology", "neurology", "oncology"]},
                "nursing": {"name": "Nursing", "keywords": ["nurse", "patient care", "bedside"]},
                "emergency": {"name": "Emergency Medicine", "keywords": ["emergency", "urgent care", "trauma"]}
            }
        }
        
        domains["administrative"] = {
            "name": "Administrative",
            "description": "Expertise in healthcare administration, policy, and management",
            "keywords": ["administration", "management", "policy", "governance", "operations"],
            "subdomains": {
                "hospital_admin": {"name": "Hospital Administration", "keywords": ["hospital", "facility", "operations"]},
                "health_policy": {"name": "Health Policy", "keywords": ["policy", "regulation", "compliance"]},
                "operations": {"name": "Healthcare Operations", "keywords": ["workflow", "process", "efficiency"]}
            }
        }
        
        domains["business"] = {
            "name": "Business",
            "description": "Expertise in business models, market analysis, and commercialization",
            "keywords": ["business", "market", "commercialization", "monetization", "startup", "entrepreneur"],
            "subdomains": {
                "strategy": {"name": "Business Strategy", "keywords": ["strategy", "planning", "vision"]},
                "finance": {"name": "Finance", "keywords": ["funding", "investment", "revenue", "cost"]},
                "marketing": {"name": "Marketing", "keywords": ["marketing", "branding", "growth"]},
                "entrepreneurship": {"name": "Entrepreneurship", "keywords": ["startup", "venture", "founding"]}
            }
        }
        
        domains["design"] = {
            "name": "Design",
            "description": "Expertise in user interface, user experience, and visual design",
            "keywords": ["design", "UI", "UX", "visual", "graphic", "user interface", "user experience"],
            "subdomains": {
                "ui_design": {"name": "UI Design", "keywords": ["interface", "visual", "graphic"]},
                "ux_design": {"name": "UX Design", "keywords": ["experience", "interaction", "usability", "accessibility"]},
                "service_design": {"name": "Service Design", "keywords": ["service", "journey", "touchpoint"]}
            }
        }
        
        domains["user_experience"] = {
            "name": "User Experience",
            "description": "Expertise in how users interact with products and services",
            "keywords": ["user", "experience", "usability", "user testing", "user research", "human-computer interaction"],
            "subdomains": {
                "user_research": {"name": "User Research", "keywords": ["research", "interviews", "surveys", "testing"]},
                "accessibility": {"name": "Accessibility", "keywords": ["accessible", "inclusion", "disability"]},
                "behavior": {"name": "User Behavior", "keywords": ["behavior", "psychology", "cognitive"]}
            }
        }
        
        return domains
    
    def _generate_project_types(self) -> Dict[str, Dict[str, Any]]:
        """Generate initial project type definitions."""
        project_types = {
            "software": {
                "name": "Software",
                "description": "Projects primarily focused on software solutions",
                "keywords": ["app", "application", "software", "platform", "digital", "mobile", "web"]
            },
            "hardware": {
                "name": "Hardware",
                "description": "Projects involving physical devices or hardware components",
                "keywords": ["device", "hardware", "physical", "wearable", "sensor", "equipment"]
            },
            "data": {
                "name": "Data",
                "description": "Projects centered around data collection, analysis, or visualization",
                "keywords": ["data", "analytics", "visualization", "dashboard", "metrics", "statistics"]
            },
            "process": {
                "name": "Process",
                "description": "Projects focused on improving workflows or processes",
                "keywords": ["process", "workflow", "procedure", "protocol", "method", "system"]
            },
            "service": {
                "name": "Service",
                "description": "Projects creating or improving service delivery",
                "keywords": ["service", "delivery", "care", "support", "assistance", "help"]
            }
        }
        return project_types
    
    def _generate_impact_dimensions(self) -> Dict[str, Dict[str, Any]]:
        """Generate initial impact dimension definitions."""
        impact_dimensions = {
            "technical_feasibility": {
                "name": "Technical Feasibility",
                "description": "How technically feasible is the project to implement",
                "scale": {
                    "1": "Extremely difficult or impossible with current technology",
                    "2": "Substantial technical challenges",
                    "3": "Moderate technical challenges",
                    "4": "Few technical challenges",
                    "5": "Easily implementable with existing technology"
                }
            },
            "innovation": {
                "name": "Innovation",
                "description": "How innovative or novel is the approach",
                "scale": {
                    "1": "Not innovative, duplicates existing solutions",
                    "2": "Minor improvements to existing approaches",
                    "3": "Moderate innovation with some novel aspects",
                    "4": "Significantly innovative approach",
                    "5": "Groundbreaking, completely novel approach"
                }
            },
            "impact": {
                "name": "Impact",
                "description": "Potential impact on the target problem or domain",
                "scale": {
                    "1": "Minimal or no impact",
                    "2": "Limited impact",
                    "3": "Moderate impact",
                    "4": "Significant impact",
                    "5": "Transformative impact"
                }
            },
            "implementation_complexity": {
                "name": "Implementation Complexity",
                "description": "Complexity of implementing the solution in practice",
                "scale": {
                    "1": "Extremely complex implementation",
                    "2": "Highly complex implementation",
                    "3": "Moderately complex implementation",
                    "4": "Relatively simple implementation",
                    "5": "Very straightforward implementation"
                }
            },
            "scalability": {
                "name": "Scalability",
                "description": "Ability to scale to wider implementation",
                "scale": {
                    "1": "Not scalable beyond initial context",
                    "2": "Limited scalability",
                    "3": "Moderately scalable",
                    "4": "Highly scalable",
                    "5": "Extremely scalable with minimal effort"
                }
            },
            "return_on_investment": {
                "name": "Return on Investment",
                "description": "Expected return relative to investment required",
                "scale": {
                    "1": "Poor ROI, costs greatly exceed benefits",
                    "2": "Limited ROI, costs somewhat exceed benefits",
                    "3": "Moderate ROI, benefits roughly equal costs",
                    "4": "Good ROI, benefits exceed costs",
                    "5": "Excellent ROI, benefits greatly exceed costs"
                }
            }
        }
        return impact_dimensions
    
    def _generate_expertise_levels(self) -> Dict[str, Dict[str, Any]]:
        """Generate initial expertise level definitions."""
        expertise_levels = {
            "beginner": {
                "name": "Beginner",
                "description": "Basic understanding of the domain",
                "confidence_range": [0, 40]
            },
            "skilled": {
                "name": "Skilled",
                "description": "Practical experience and good understanding of the domain",
                "confidence_range": [41, 70]
            },
            "talented": {
                "name": "Talented",
                "description": "Deep understanding and significant experience in the domain",
                "confidence_range": [71, 85]
            },
            "seasoned": {
                "name": "Seasoned",
                "description": "Extensive experience and comprehensive knowledge of the domain",
                "confidence_range": [86, 95]
            },
            "expert": {
                "name": "Expert",
                "description": "Top-level expertise with mastery of the domain",
                "confidence_range": [96, 100]
            }
        }
        return expertise_levels
    
    def _generate_review_dimensions(self) -> Dict[str, List[str]]:
        """Generate initial review dimension mappings by domain."""
        review_dimensions = {
            "technical": [
                "technical_feasibility",
                "implementation_complexity",
                "scalability",
                "innovation"
            ],
            "clinical": [
                "impact",
                "implementation_complexity",
                "technical_feasibility"
            ],
            "administrative": [
                "implementation_complexity",
                "scalability",
                "return_on_investment"
            ],
            "business": [
                "return_on_investment",
                "scalability",
                "impact"
            ],
            "design": [
                "innovation",
                "impact",
                "implementation_complexity"
            ],
            "user_experience": [
                "impact",
                "implementation_complexity",
                "innovation"
            ]
        }
        return review_dimensions
    
    def update_ontology_with_llm(self, context: str = "") -> None:
        """
        Update the ontology using an LLM model with additional context.
        
        Args:
            context: Additional context to inform the ontology update
        """
        prompt = f"""
        You are an expert in healthcare innovation and hackathons. You need to help update an ontology 
        for a multi-perspective peer review system. The current ontology includes:
        
        1. Domains (e.g., technical, clinical, administrative)
        2. Project types (e.g., software, hardware, data)
        3. Impact dimensions (e.g., technical feasibility, innovation, impact)
        4. Expertise levels (e.g., beginner, skilled, expert)
        
        Based on the following context, suggest improvements or additions to the ontology:
        
        {context}
        
        Provide your response as a JSON object with the following structure:
        {{
            "domains_to_add": [{{
                "name": "domain_name",
                "description": "domain_description",
                "keywords": ["keyword1", "keyword2"]
            }}],
            "project_types_to_add": [{{
                "name": "project_type_name",
                "description": "project_type_description",
                "keywords": ["keyword1", "keyword2"]
            }}],
            "impact_dimensions_to_add": [{{
                "name": "dimension_name",
                "description": "dimension_description",
                "scale": {{
                    "1": "description_of_1",
                    "5": "description_of_5"
                }}
            }}]
        }}
        """
        
        response = generate_llm_response("claude", prompt)
        try:
            updates = json.loads(response)
            
            # Apply updates to the ontology
            for domain in updates.get("domains_to_add", []):
                if domain.get("name") and domain.get("name").lower() not in self.ontology["domains"]:
                    self.ontology["domains"][domain.get("name").lower()] = {
                        "name": domain.get("name"),
                        "description": domain.get("description", ""),
                        "keywords": domain.get("keywords", []),
                        "subdomains": {}
                    }
            
            for project_type in updates.get("project_types_to_add", []):
                if project_type.get("name") and project_type.get("name").lower() not in self.ontology["project_types"]:
                    self.ontology["project_types"][project_type.get("name").lower()] = {
                        "name": project_type.get("name"),
                        "description": project_type.get("description", ""),
                        "keywords": project_type.get("keywords", [])
                    }
            
            for impact_dimension in updates.get("impact_dimensions_to_add", []):
                if impact_dimension.get("name") and impact_dimension.get("name").lower() not in self.ontology["impact_dimensions"]:
                    self.ontology["impact_dimensions"][impact_dimension.get("name").lower().replace(" ", "_")] = {
                        "name": impact_dimension.get("name"),
                        "description": impact_dimension.get("description", ""),
                        "scale": impact_dimension.get("scale", {})
                    }
            
            self.save_ontology()
            print("Ontology updated successfully with LLM suggestions.")
        except json.JSONDecodeError:
            print("Failed to parse LLM response as JSON.")
    
    def get_domains(self) -> List[str]:
        """Get list of all domains in the ontology."""
        return list(self.ontology.get("domains", {}).keys())
    
    def get_domain_keywords(self, domain: str) -> List[str]:
        """Get keywords for a specific domain."""
        domain_data = self.ontology.get("domains", {}).get(domain.lower(), {})
        return domain_data.get("keywords", [])
    
    def get_expertise_level(self, confidence_score: int) -> str:
        """
        Determine expertise level based on confidence score.
        
        Args:
            confidence_score: Confidence score (0-100)
            
        Returns:
            Expertise level name
        """
        for level_id, level_data in self.ontology.get("expertise_levels", {}).items():
            min_score, max_score = level_data.get("confidence_range", [0, 100])
            if min_score <= confidence_score <= max_score:
                return level_id
        
        return "beginner"  # Default to beginner if no match
    
    def get_relevant_dimensions_for_domain(self, domain: str) -> List[str]:
        """
        Get relevant impact dimensions for a specific domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of dimension IDs relevant to the domain
        """
        return self.ontology.get("review_dimensions", {}).get(domain.lower(), [])
    
    def classify_project_type(self, project_description: str) -> str:
        """
        Classify a project into a project type based on its description.
        
        Args:
            project_description: Text description of the project
            
        Returns:
            Project type ID
        """
        best_match = None
        best_score = 0
        
        for project_type_id, project_type_data in self.ontology.get("project_types", {}).items():
            score = 0
            for keyword in project_type_data.get("keywords", []):
                if keyword.lower() in project_description.lower():
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = project_type_id
        
        return best_match or "software"  # Default to software if no match
    
    def calculate_domain_relevance(self, project_description: str, domain: str) -> float:
        """
        Calculate relevance score of a domain to a project.
        
        Args:
            project_description: Text description of the project
            domain: Domain to check relevance for
            
        Returns:
            Relevance score (0-1)
        """
        domain_data = self.ontology.get("domains", {}).get(domain.lower(), {})
        keywords = domain_data.get("keywords", [])
        
        if not keywords:
            return 0.0
        
        # Count keyword matches
        match_count = 0
        for keyword in keywords:
            if keyword.lower() in project_description.lower():
                match_count += 1
        
        return min(1.0, match_count / max(1, len(keywords) * 0.3))
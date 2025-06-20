import os
import json
from typing import Dict, List, Any, Optional

from src.infrastructure.config import PATHS, CORE_DOMAINS
from src.infrastructure.llm_interface import generate_llm_response
from src.infrastructure.logging_utils import logger
from src.core.ontology_rdf import RDFOntology
from src.core.dynamic_prompts import DynamicPromptGenerator

class Ontology:
    """
    Updated ontology class that uses RDF/TTL backend with dynamic prompt generation.
    """
    
    def __init__(self, load_existing: bool = True):
        """
        Initialize the ontology with RDF backend.
        
        Args:
            load_existing: Whether to load an existing ontology file
        """
        self.ttl_path = PATHS.get("ontology_ttl", "data/ontology.ttl")
        self.json_path = PATHS.get("ontology_file", "data/ontology.json")  # Keep for backward compatibility
        
        # Initialize RDF ontology
        if load_existing and os.path.exists(self.ttl_path):
            self.rdf_ontology = RDFOntology(self.ttl_path)
            logger.info("Loaded RDF ontology from TTL file")
        else:
            logger.warning(f"TTL file not found at {self.ttl_path}")
            # Fallback to JSON if TTL doesn't exist
            self._load_from_json_fallback()
        
        # Initialize dynamic prompt generator
        self.prompt_generator = DynamicPromptGenerator(self.rdf_ontology)
        
        # Cache for compatibility with existing code
        self._json_cache = None
    
    def _load_from_json_fallback(self):
        """Fallback to load from JSON and convert to RDF if TTL doesn't exist."""
        if os.path.exists(self.json_path):
            logger.info("Loading from JSON as fallback and converting to RDF")
            with open(self.json_path, 'r') as f:
                json_data = json.load(f)
            
            # Convert JSON to RDF (implementation needed)
            self._convert_json_to_rdf(json_data)
        else:
            raise FileNotFoundError(f"Neither TTL ({self.ttl_path}) nor JSON ({self.json_path}) ontology found")
    
    def _convert_json_to_rdf(self, json_data: Dict[str, Any]):
        """Convert JSON ontology to RDF format."""
        # This would implement conversion from existing JSON to RDF
        # For now, create empty RDF ontology
        self.rdf_ontology = RDFOntology()
        logger.warning("JSON to RDF conversion not yet implemented")
    
    @property
    def ontology(self) -> Dict[str, Any]:
        """
        Backward compatibility property that returns JSON-like structure.
        """
        if self._json_cache is None:
            self._json_cache = self._rdf_to_json()
        return self._json_cache
    
    def _rdf_to_json(self) -> Dict[str, Any]:
        """Convert RDF ontology to JSON structure for backward compatibility."""
        domains = {}
        for domain in self.rdf_ontology.get_domains():
            domains[domain["id"]] = {
                "name": domain["name"],
                "description": domain["description"],
                "keywords": domain["keywords"],
                "subdomains": domain["subdomains"]
            }
        
        dimensions = {}
        for dim in self.rdf_ontology.get_impact_dimensions():
            dimensions[dim["id"]] = {
                "name": dim["name"],
                "description": dim["description"],
                "scale": dim["scale"]
            }
        
        levels = {}
        for level in self.rdf_ontology.get_expertise_levels():
            levels[level["id"]] = {
                "name": level["name"],
                "description": level["description"],
                "confidence_range": level["confidence_range"]
            }
        
        types = {}
        for ptype in self.rdf_ontology.get_project_types():
            types[ptype["id"]] = {
                "name": ptype["name"],
                "description": ptype["description"],
                "keywords": ptype["keywords"]
            }
        
        # Build review dimensions mapping
        review_dimensions = {}
        for domain in self.rdf_ontology.get_domains():
            domain_id = domain["id"]
            relevant_dims = self.rdf_ontology.get_relevant_dimensions_for_domain(domain_id)
            review_dimensions[domain_id] = relevant_dims
        
        return {
            "domains": domains,
            "impact_dimensions": dimensions,
            "expertise_levels": levels,
            "project_types": types,
            "review_dimensions": review_dimensions
        }
    
    def save_ontology(self) -> None:
        """Save the ontology to TTL file."""
        self.rdf_ontology.save_ontology()
        # Clear cache so it gets regenerated
        self._json_cache = None
    
    def get_domains(self) -> List[str]:
        """Get list of all domain IDs."""
        return [domain["id"] for domain in self.rdf_ontology.get_domains()]
    
    def get_domain_keywords(self, domain: str) -> List[str]:
        """Get keywords for a specific domain."""
        domain_data = self.rdf_ontology.get_domain_by_id(domain)
        return domain_data.get("keywords", []) if domain_data else []
    
    def get_expertise_level(self, confidence_score: int) -> str:
        """Determine expertise level based on confidence score."""
        return self.rdf_ontology.get_expertise_level_by_confidence(confidence_score)
    
    def get_relevant_dimensions_for_domain(self, domain: str) -> List[str]:
        """Get relevant impact dimensions for a specific domain."""
        return self.rdf_ontology.get_relevant_dimensions_for_domain(domain)
    
    def classify_project_type(self, project_description: str) -> str:
        """Classify a project into a project type based on its description."""
        return self.rdf_ontology.classify_project_type(project_description)
    
    def calculate_domain_relevance(self, project_description: str, domain: str) -> float:
        """Calculate relevance score of a domain to a project."""
        return self.rdf_ontology.calculate_domain_relevance(project_description, domain)
    
    # New methods that leverage RDF capabilities
    def add_domain(self, domain_id: str, name: str, description: str, 
                   keywords: List[str], relevant_dimensions: List[str] = None) -> None:
        """Add a new domain to the ontology."""
        self.rdf_ontology.add_domain(domain_id, name, description, keywords)
        
        if relevant_dimensions:
            self.rdf_ontology.link_domain_to_dimensions(domain_id, relevant_dimensions)
        
        # Clear cache
        self._json_cache = None
        logger.info(f"Added new domain: {domain_id}")
    
    def add_impact_dimension(self, dimension_id: str, name: str, description: str, 
                           scale: Dict[str, str]) -> None:
        """Add a new impact dimension to the ontology."""
        self.rdf_ontology.add_impact_dimension(dimension_id, name, description, scale)
        
        # Clear cache
        self._json_cache = None
        logger.info(f"Added new impact dimension: {dimension_id}")
    
    def update_ontology_with_llm(self, context: str = "") -> None:
        """
        Update the ontology using LLM suggestions based on context.
        Now uses dynamic prompts from the ontology.
        """
        if not context:
            logger.info("No context provided for ontology update, skipping")
            return
        
        try:
            # Use dynamic prompt generator
            prompt = self.prompt_generator.generate_ontology_update_prompt(context)
            response = generate_llm_response(prompt)
            
            # Parse and apply suggestions
            suggestions = json.loads(response)
            
            # Apply new domains
            for domain_data in suggestions.get("domains_to_add", []):
                self.add_domain(
                    domain_data["id"],
                    domain_data["name"],
                    domain_data["description"],
                    domain_data["keywords"],
                    domain_data.get("relevant_dimensions", [])
                )
            
            # Apply new dimensions
            for dim_data in suggestions.get("dimensions_to_add", []):
                self.add_impact_dimension(
                    dim_data["id"],
                    dim_data["name"],
                    dim_data["description"],
                    dim_data["scale"]
                )
            
            # Save changes
            self.save_ontology()
            
            logger.info("Ontology updated successfully with LLM suggestions")
            
        except Exception as e:
            logger.error(f"Failed to update ontology with LLM: {str(e)}")
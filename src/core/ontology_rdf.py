import os
from typing import Dict, List, Any, Optional, Tuple
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.plugins.sparql import prepareQuery

from src.infrastructure.config import PATHS
from src.infrastructure.logging_utils import logger

# Define namespaces
HR = Namespace("http://example.org/hackathon-review/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

class RDFOntology:
    def __init__(self, ttl_path: Optional[str] = None):
        """
        Initialize the RDF ontology.
        
        Args:
            ttl_path: Path to TTL file. If None, uses default from config.
        """
        self.ttl_path = ttl_path or os.path.join(PATHS.get("data_dir", "data/"), "ontology.ttl")
        self.graph = Graph()
        self.graph.bind("hr", HR)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("rdf", RDF)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
        
        # Load the ontology
        self.load_ontology()
        
        # Prepare common SPARQL queries
        self._prepare_queries()
    
    def load_ontology(self) -> None:
        """Load the ontology from TTL file."""
        try:
            if os.path.exists(self.ttl_path):
                self.graph.parse(self.ttl_path, format="turtle")
                logger.info(f"Loaded ontology from {self.ttl_path}")
                logger.info(f"Graph contains {len(self.graph)} triples")
            else:
                logger.error(f"Ontology file not found at {self.ttl_path}")
                raise FileNotFoundError(f"Ontology file not found at {self.ttl_path}")
        except Exception as e:
            logger.error(f"Error loading ontology: {str(e)}")
            raise
    
    def save_ontology(self) -> None:
        """Save the ontology to TTL file."""
        try:
            self.graph.serialize(destination=self.ttl_path, format="turtle")
            logger.info(f"Saved ontology to {self.ttl_path}")
        except Exception as e:
            logger.error(f"Error saving ontology: {str(e)}")
            raise
    
    def _prepare_queries(self) -> None:
        """Prepare common SPARQL queries."""
        # Query for getting all domains
        self.domains_query = prepareQuery("""
            SELECT ?domain ?name ?description
            WHERE {
                ?domain a hr:Domain .
                ?domain hr:hasName ?name .
                ?domain hr:hasDescription ?description .
            }
        """, initNs={"hr": HR})
        
        # Query for getting domain keywords
        self.domain_keywords_query = prepareQuery("""
            SELECT ?keyword
            WHERE {
                ?domain hr:hasKeyword ?keyword .
            }
        """, initNs={"hr": HR})
        
        # Query for getting subdomains
        self.subdomains_query = prepareQuery("""
            SELECT ?subdomain ?name
            WHERE {
                ?domain hr:hasSubdomain ?subdomain .
                ?subdomain hr:hasName ?name .
            }
        """, initNs={"hr": HR})
        
        # Query for getting impact dimensions
        self.dimensions_query = prepareQuery("""
            SELECT ?dimension ?name ?description
            WHERE {
                ?dimension a hr:ImpactDimension .
                ?dimension hr:hasName ?name .
                ?dimension hr:hasDescription ?description .
            }
        """, initNs={"hr": HR})
        
        # Query for getting dimension scale values
        self.scale_values_query = prepareQuery("""
            SELECT ?value
            WHERE {
                ?dimension hr:hasScaleValue ?value .
            }
        """, initNs={"hr": HR})
        
        # Query for getting expertise levels
        self.expertise_levels_query = prepareQuery("""
            SELECT ?level ?name ?description ?min ?max
            WHERE {
                ?level a hr:ExpertiseLevel .
                ?level hr:hasName ?name .
                ?level hr:hasDescription ?description .
                ?level hr:hasConfidenceRangeMin ?min .
                ?level hr:hasConfidenceRangeMax ?max .
            }
        """, initNs={"hr": HR})
        
        # Query for getting relevant dimensions for a domain
        self.relevant_dimensions_query = prepareQuery("""
            SELECT ?dimension
            WHERE {
                ?domain hr:hasRelevantDimension ?dimension .
            }
        """, initNs={"hr": HR})
        
        # Query for project types
        self.project_types_query = prepareQuery("""
            SELECT ?type ?name ?description
            WHERE {
                ?type a hr:ProjectType .
                ?type hr:hasName ?name .
                ?type hr:hasDescription ?description .
            }
        """, initNs={"hr": HR})
    
    def get_domains(self) -> List[Dict[str, Any]]:
        """
        Get all domains from the ontology.
        
        Returns:
            List of domain dictionaries with id, name, description, and keywords
        """
        domains = []
        
        for row in self.graph.query(self.domains_query):
            domain_uri = row.domain
            domain_id = domain_uri.split('/')[-1]  # Extract ID from URI
            
            # Get keywords for this domain
            keywords = []
            for keyword_row in self.graph.query(self.domain_keywords_query, initBindings={'domain': domain_uri}):
                keywords.append(str(keyword_row.keyword))
            
            # Get subdomains
            subdomains = {}
            for subdomain_row in self.graph.query(self.subdomains_query, initBindings={'domain': domain_uri}):
                subdomain_uri = subdomain_row.subdomain
                subdomain_id = subdomain_uri.split('/')[-1]
                
                # Get keywords for subdomain
                subdomain_keywords = []
                for kw_row in self.graph.query(self.domain_keywords_query, initBindings={'domain': subdomain_uri}):
                    subdomain_keywords.append(str(kw_row.keyword))
                
                subdomains[subdomain_id] = {
                    "name": str(subdomain_row.name),
                    "keywords": subdomain_keywords
                }
            
            domains.append({
                "id": domain_id,
                "name": str(row.name),
                "description": str(row.description),
                "keywords": keywords,
                "subdomains": subdomains
            })
        
        return domains
    
    def get_domain_by_id(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific domain by its ID.
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            Domain dictionary or None if not found
        """
        domains = self.get_domains()
        for domain in domains:
            if domain["id"] == domain_id:
                return domain
        return None
    
    def get_impact_dimensions(self) -> List[Dict[str, Any]]:
        """
        Get all impact dimensions from the ontology.
        
        Returns:
            List of dimension dictionaries
        """
        dimensions = []
        
        for row in self.graph.query(self.dimensions_query):
            dimension_uri = row.dimension
            dimension_id = dimension_uri.split('/')[-1]
            
            # Get scale values
            scale = {}
            for scale_row in self.graph.query(self.scale_values_query, initBindings={'dimension': dimension_uri}):
                value_str = str(scale_row.value)
                # Parse "1, Description" format
                if ', ' in value_str:
                    num, desc = value_str.split(', ', 1)
                    scale[num] = desc
            
            dimensions.append({
                "id": dimension_id,
                "name": str(row.name),
                "description": str(row.description),
                "scale": scale
            })
        
        return dimensions
    
    def get_dimension_by_id(self, dimension_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific dimension by its ID."""
        dimensions = self.get_impact_dimensions()
        for dim in dimensions:
            if dim["id"] == dimension_id:
                return dim
        return None
    
    def get_expertise_levels(self) -> List[Dict[str, Any]]:
        """
        Get all expertise levels from the ontology.
        
        Returns:
            List of expertise level dictionaries
        """
        levels = []
        
        for row in self.graph.query(self.expertise_levels_query):
            level_uri = row.level
            level_id = level_uri.split('/')[-1]
            
            levels.append({
                "id": level_id,
                "name": str(row.name),
                "description": str(row.description),
                "confidence_range": [int(row.min), int(row.max)]
            })
        
        # Sort by minimum confidence score
        levels.sort(key=lambda x: x["confidence_range"][0])
        
        return levels
    
    def get_expertise_level_by_confidence(self, confidence_score: int) -> str:
        """
        Determine expertise level based on confidence score.
        
        Args:
            confidence_score: Confidence score (0-100)
            
        Returns:
            Expertise level ID
        """
        levels = self.get_expertise_levels()
        
        for level in levels:
            min_score, max_score = level["confidence_range"]
            if min_score <= confidence_score <= max_score:
                return level["id"]
        
        return "beginner"  # Default
    
    def get_relevant_dimensions_for_domain(self, domain_id: str) -> List[str]:
        """
        Get relevant impact dimensions for a specific domain.
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            List of dimension IDs
        """
        domain_uri = HR[domain_id]
        dimensions = []
        
        for row in self.graph.query(self.relevant_dimensions_query, initBindings={'domain': domain_uri}):
            dimension_uri = row.dimension
            dimension_id = dimension_uri.split('/')[-1]
            dimensions.append(dimension_id)
        
        return dimensions
    
    def get_project_types(self) -> List[Dict[str, Any]]:
        """Get all project types from the ontology."""
        types = []
        
        for row in self.graph.query(self.project_types_query):
            type_uri = row.type
            type_id = type_uri.split('/')[-1]
            
            # Get keywords
            keywords = []
            for kw_row in self.graph.query(self.domain_keywords_query, initBindings={'domain': type_uri}):
                keywords.append(str(kw_row.keyword))
            
            types.append({
                "id": type_id,
                "name": str(row.name),
                "description": str(row.description),
                "keywords": keywords
            })
        
        return types
    
    def classify_project_type(self, project_description: str) -> str:
        """
        Classify a project into a project type based on its description.
        
        Args:
            project_description: Text description of the project
            
        Returns:
            Project type ID
        """
        project_types = self.get_project_types()
        best_match = None
        best_score = 0
        
        for ptype in project_types:
            score = 0
            for keyword in ptype.get("keywords", []):
                if keyword.lower() in project_description.lower():
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = ptype["id"]
        
        return best_match or "software"  # Default
    
    def calculate_domain_relevance(self, project_description: str, domain_id: str) -> float:
        """
        Calculate relevance score of a domain to a project.
        
        Args:
            project_description: Text description of the project
            domain_id: Domain to check relevance for
            
        Returns:
            Relevance score (0-1)
        """
        domain = self.get_domain_by_id(domain_id)
        if not domain:
            return 0.0
        
        keywords = domain.get("keywords", [])
        if not keywords:
            return 0.0
        
        # Count keyword matches
        match_count = 0
        for keyword in keywords:
            if keyword.lower() in project_description.lower():
                match_count += 1
        
        # Also check subdomain keywords
        for subdomain in domain.get("subdomains", {}).values():
            for keyword in subdomain.get("keywords", []):
                if keyword.lower() in project_description.lower():
                    match_count += 0.5  # Subdomain keywords have less weight
        
        # Calculate relevance score
        total_keywords = len(keywords) + sum(len(sd.get("keywords", [])) for sd in domain.get("subdomains", {}).values())
        return min(1.0, match_count / max(1, total_keywords * 0.3))
    
    def add_domain(self, domain_id: str, name: str, description: str, keywords: List[str]) -> None:
        """
        Add a new domain to the ontology.
        
        Args:
            domain_id: Unique identifier for the domain
            name: Human-readable name
            description: Domain description
            keywords: List of keywords associated with the domain
        """
        domain_uri = HR[domain_id]
        
        # Add domain as instance of Domain class
        self.graph.add((domain_uri, RDF.type, HR.Domain))
        self.graph.add((domain_uri, HR.hasName, Literal(name)))
        self.graph.add((domain_uri, HR.hasDescription, Literal(description)))
        
        # Add keywords
        for keyword in keywords:
            self.graph.add((domain_uri, HR.hasKeyword, Literal(keyword)))
        
        logger.info(f"Added new domain: {domain_id}")
    
    def add_impact_dimension(self, dimension_id: str, name: str, description: str, 
                           scale: Dict[str, str]) -> None:
        """
        Add a new impact dimension to the ontology.
        
        Args:
            dimension_id: Unique identifier for the dimension
            name: Human-readable name
            description: Dimension description
            scale: Dictionary mapping scale values (1-5) to descriptions
        """
        dimension_uri = HR[dimension_id]
        
        # Add dimension as instance of ImpactDimension class
        self.graph.add((dimension_uri, RDF.type, HR.ImpactDimension))
        self.graph.add((dimension_uri, HR.hasName, Literal(name)))
        self.graph.add((dimension_uri, HR.hasDescription, Literal(description)))
        
        # Add scale values
        for value, desc in scale.items():
            self.graph.add((dimension_uri, HR.hasScaleValue, Literal(f"{value}, {desc}")))
        
        logger.info(f"Added new impact dimension: {dimension_id}")
    
    def link_domain_to_dimensions(self, domain_id: str, dimension_ids: List[str]) -> None:
        """
        Link a domain to relevant dimensions.
        
        Args:
            domain_id: Domain identifier
            dimension_ids: List of dimension identifiers
        """
        domain_uri = HR[domain_id]
        
        for dimension_id in dimension_ids:
            dimension_uri = HR[dimension_id]
            self.graph.add((domain_uri, HR.hasRelevantDimension, dimension_uri))
        
        logger.info(f"Linked domain {domain_id} to dimensions: {dimension_ids}")
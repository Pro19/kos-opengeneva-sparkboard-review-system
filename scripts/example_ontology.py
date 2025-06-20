"""
Complete example demonstrating the RDF ontology-driven system.
This script shows how to use all the new features.
"""

import json
from src.core.ontology import Ontology
from src.infrastructure.logging_utils import logger

def demonstrate_rdf_ontology():
    """Demonstrate RDF-based ontology features"""
    print("=== RDF Ontology Demonstration ===\n")
    
    try:
        # Initialize ontology (uses RDF backend)
        ontology = Ontology(load_existing=True)
        print("RDF ontology loaded successfully!")
    except Exception as e:
        print(f"Failed to load RDF ontology: {str(e)}")
        print("Please ensure data/ontology.ttl exists")
        return
    
    # 1. Show domains from RDF
    print("\n1. Domains loaded from TTL:")
    domains = ontology.rdf_ontology.get_domains()
    for domain in domains:
        print(f"   - {domain['name']} ({domain['id']})")
        print(f"     Description: {domain['description'][:80]}...")
        print(f"     Keywords: {', '.join(domain['keywords'][:4])}...")
        if domain['subdomains']:
            print(f"     Subdomains: {', '.join(domain['subdomains'].keys())}")
        print()
    
    # 2. Show impact dimensions
    print("\n2. Impact Dimensions from TTL:")
    dimensions = ontology.rdf_ontology.get_impact_dimensions()
    for dim in dimensions:
        print(f"   - {dim['name']}: {dim['description']}")
        print(f"     Scale: 1 = {dim['scale'].get('1', 'N/A')}")
        print(f"            5 = {dim['scale'].get('5', 'N/A')}")
        print()
    
    # 3. Demonstrate dynamic prompt generation
    print("\n3. Dynamic Prompt Generation Example:")
    project_desc = "An AI-powered system to help doctors diagnose rare diseases using machine learning and computer vision"
    
    # Generate prompt for clinical domain
    print("   Generating clinical domain review prompt...")
    prompt = ontology.prompt_generator.generate_artificial_review_prompt(
        project_desc, 
        "clinical"
    )
    print(f"   Generated prompt (first 300 chars):")
    print(f"   {prompt[:300]}...")
    print()
    
    # Generate sentiment analysis prompt
    print("   Generating dynamic sentiment analysis prompt...")
    sample_review = "This project shows great potential for clinical impact. The AI approach is innovative but may face regulatory challenges."
    sentiment_prompt = ontology.prompt_generator.generate_sentiment_analysis_prompt(sample_review)
    print(f"   Sentiment prompt includes {len(dimensions)} dynamic dimensions from ontology")
    print()
    
    # 4. Show expertise levels
    print("\n4. Expertise Levels:")
    levels = ontology.rdf_ontology.get_expertise_levels()
    for level in levels:
        print(f"   - {level['name']}: confidence {level['confidence_range'][0]}-{level['confidence_range'][1]}")
        print(f"     {level['description']}")
    print()
    
    # 5. Show domain-dimension relationships
    print("\n5. Domain-Dimension Relationships:")
    for domain in ontology.get_domains()[:3]:  # Show first 3
        relevant_dims = ontology.get_relevant_dimensions_for_domain(domain)
        domain_info = ontology.rdf_ontology.get_domain_by_id(domain)
        print(f"   {domain_info['name']} domain focuses on:")
        for dim_id in relevant_dims:
            dim_info = ontology.rdf_ontology.get_dimension_by_id(dim_id)
            if dim_info:
                print(f"     - {dim_info['name']}")
    print()
    
    # 6. Demonstrate project classification
    print("\n6. Project Classification:")
    project_types = ontology.rdf_ontology.get_project_types()
    classified_type = ontology.classify_project_type(project_desc)
    type_info = ontology.rdf_ontology.get_project_types()
    matching_type = next((pt for pt in type_info if pt['id'] == classified_type), None)
    print(f"   Project classified as: {matching_type['name'] if matching_type else classified_type}")
    print()
    
    # 7. Domain relevance calculation
    print("\n7. Domain Relevance Calculation:")
    for domain in ontology.get_domains()[:4]:
        relevance = ontology.calculate_domain_relevance(project_desc, domain)
        domain_info = ontology.rdf_ontology.get_domain_by_id(domain)
        print(f"   {domain_info['name']}: {relevance:.2f} relevance")
    print()

def add_new_domain_example():
    """Example of adding a new domain to the RDF ontology"""
    print("\n=== Adding New Domain to RDF Ontology ===\n")
    
    try:
        # Initialize ontology
        ontology = Ontology(load_existing=True)
        print("RDF ontology loaded")
    except Exception as e:
        print(f"Failed to load ontology: {str(e)}")
        return
    
    # Define a new domain
    new_domain = {
        "id": "environmental",
        "name": "Environmental Impact",
        "description": "Expertise in environmental sustainability, climate impact, and ecological considerations for technology projects",
        "keywords": ["sustainability", "climate", "ecology", "carbon footprint", "renewable", "green technology", "environmental"],
        "relevant_dimensions": ["impact", "scalability", "return_on_investment"]
    }
    
    print(f"Adding new domain: {new_domain['name']}")
    print(f"Description: {new_domain['description']}")
    print(f"Keywords: {', '.join(new_domain['keywords'])}")
    
    try:
        # Check if domain already exists
        existing = ontology.rdf_ontology.get_domain_by_id(new_domain["id"])
        if existing:
            print(f" Domain '{new_domain['id']}' already exists, skipping...")
            return
        
        # Add to ontology
        ontology.add_domain(
            domain_id=new_domain["id"],
            name=new_domain["name"],
            description=new_domain["description"],
            keywords=new_domain["keywords"],
            relevant_dimensions=new_domain["relevant_dimensions"]
        )
        
        print("Domain added successfully to RDF ontology!")
        
        # Verify it was added
        domain = ontology.rdf_ontology.get_domain_by_id("environmental")
        if domain:
            print(f"Verified: {domain['name']} is now in the ontology")
            print(f"   Keywords: {', '.join(domain['keywords'])}")
        
        # Save changes
        ontology.save_ontology()
        print("RDF ontology saved with new domain")
        
    except Exception as e:
        print(f"Error adding domain: {str(e)}")

def add_new_dimension_example():
    """Example of adding a new evaluation dimension to RDF ontology"""
    print("\n=== Adding New Dimension to RDF Ontology ===\n")
    
    try:
        ontology = Ontology(load_existing=True)
        print("RDF ontology loaded")
    except Exception as e:
        print(f"Failed to load ontology: {str(e)}")
        return
    
    # Define a new dimension
    new_dimension = {
        "id": "sustainability",
        "name": "Environmental Sustainability",
        "description": "Measures the environmental impact and sustainability aspects of the solution",
        "scale": {
            "1": "Significant negative environmental impact",
            "2": "Some negative environmental impact with few mitigation measures",
            "3": "Neutral environmental impact with basic considerations",
            "4": "Positive environmental contribution with sustainability features",
            "5": "Exceptional environmental benefits and comprehensive sustainability approach"
        }
    }
    
    print(f"Adding new dimension: {new_dimension['name']}")
    print(f"Description: {new_dimension['description']}")
    print("Scale:")
    for level, desc in new_dimension['scale'].items():
        print(f"  {level}: {desc}")
    
    try:
        # Check if dimension already exists
        existing = ontology.rdf_ontology.get_dimension_by_id(new_dimension["id"])
        if existing:
            print(f" Dimension '{new_dimension['id']}' already exists, skipping...")
            return
        
        # Add to ontology
        ontology.add_impact_dimension(
            dimension_id=new_dimension["id"],
            name=new_dimension["name"],
            description=new_dimension["description"],
            scale=new_dimension["scale"]
        )
        
        print("Dimension added successfully to RDF ontology!")
        
        # Verify it was added
        dimension = ontology.rdf_ontology.get_dimension_by_id("sustainability")
        if dimension:
            print(f"Verified: {dimension['name']} is now in the ontology")
            print(f"   Scale levels: {len(dimension['scale'])} defined")
        
        # Save changes
        ontology.save_ontology()
        print("RDF ontology saved with new dimension")
        
    except Exception as e:
        print(f"Error adding dimension: {str(e)}")

def query_ontology_example():
    """Example of querying the RDF ontology with SPARQL"""
    print("\n=== Querying RDF Ontology with SPARQL ===\n")
    
    try:
        # Direct RDF access
        from src.core.ontology_rdf import RDFOntology
        rdf_ontology = RDFOntology()
        print("Direct RDF ontology access established")
    except Exception as e:
        print(f"Failed to access RDF ontology: {str(e)}")
        return
    
    # Example SPARQL query - find all domains with "health" related keywords
    query = """
    PREFIX hr: <http://example.org/hackathon-review/>
    SELECT ?domain ?name ?keyword
    WHERE {
        ?domain a hr:Domain .
        ?domain hr:hasName ?name .
        ?domain hr:hasKeyword ?keyword .
        FILTER(CONTAINS(LCASE(?keyword), "health") || CONTAINS(LCASE(?keyword), "medical"))
    }
    """
    
    print("SPARQL Query: Find domains with health/medical keywords")
    print("Results:")
    try:
        results = rdf_ontology.graph.query(query)
        found_results = False
        for row in results:
            domain_id = str(row.domain).split('/')[-1]
            print(f"   - {row.name} ({domain_id}): keyword '{row.keyword}'")
            found_results = True
        
        if not found_results:
            print("   No health/medical related domains found")
            
    except Exception as e:
        print(f"   Query failed: {str(e)}")
    
    # Another query - find dimensions with specific scale descriptions
    query2 = """
    PREFIX hr: <http://example.org/hackathon-review/>
    SELECT ?dimension ?name (COUNT(?scale) as ?scale_count)
    WHERE {
        ?dimension a hr:ImpactDimension .
        ?dimension hr:hasName ?name .
        ?dimension hr:hasScaleValue ?scale .
    }
    GROUP BY ?dimension ?name
    ORDER BY DESC(?scale_count)
    """
    
    print("\nSPARQL Query: Dimensions by scale complexity")
    print("Results:")
    try:
        results = rdf_ontology.graph.query(query2)
        for row in results:
            dimension_id = str(row.dimension).split('/')[-1]
            print(f"   - {row.name}: {row.scale_count} scale levels defined")
            
    except Exception as e:
        print(f"   Query failed: {str(e)}")

def test_dynamic_prompts():
    """Test dynamic prompt generation with different scenarios"""
    print("\n=== Testing Dynamic Prompt Generation ===\n")
    
    try:
        ontology = Ontology(load_existing=True)
        print("Ontology loaded for prompt testing")
    except Exception as e:
        print(f"Failed to load ontology: {str(e)}")
        return
    
    # Test scenarios
    scenarios = [
        {
            "name": "Healthcare AI Project",
            "description": "A machine learning system that analyzes medical images to detect early signs of cancer using deep learning and computer vision techniques.",
            "test_domain": "clinical"
        },
        {
            "name": "Sustainable Transport App",
            "description": "A mobile application that helps users find eco-friendly transportation options and tracks their carbon footprint reduction.",
            "test_domain": "environmental"  # This might not exist yet
        },
        {
            "name": "Blockchain Fintech Solution",
            "description": "A decentralized finance platform that enables peer-to-peer lending with smart contracts and automated risk assessment.",
            "test_domain": "business"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. Testing: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        # Test domain relevance
        relevance = ontology.calculate_domain_relevance(scenario['description'], scenario['test_domain'])
        print(f"   Domain relevance ({scenario['test_domain']}): {relevance:.2f}")
        
        # Test prompt generation (if domain exists)
        domain_exists = scenario['test_domain'] in ontology.get_domains()
        if domain_exists:
            try:
                prompt = ontology.prompt_generator.generate_artificial_review_prompt(
                    scenario['description'], 
                    scenario['test_domain']
                )
                print(f"   Generated {len(prompt)} character prompt for {scenario['test_domain']} domain")
                
                # Show prompt structure
                if "You are an expert reviewer" in prompt:
                    print("   Prompt includes expert persona")
                if scenario['test_domain'] in prompt.lower():
                    print("   Prompt includes domain-specific context")
                if "CONFIDENCE:" in prompt:
                    print("   Prompt requests confidence score")
                    
            except Exception as e:
                print(f"   Prompt generation failed: {str(e)}")
        else:
            print(f"    Domain '{scenario['test_domain']}' not found in ontology")
        
        print()

def demonstrate_api_integration():
    """Show how the ontology integrates with the API system"""
    print("\n=== API Integration Example ===\n")
    
    print("The RDF ontology system now provides these API capabilities:")
    print()
    
    api_endpoints = [
        ("GET /api/v1/ontology/stats", "Get ontology statistics"),
        ("GET /api/v1/ontology/domains", "List all domains"),
        ("POST /api/v1/ontology/domains", "Add new domain"),
        ("GET /api/v1/ontology/dimensions", "List all evaluation dimensions"),
        ("POST /api/v1/ontology/dimensions", "Add new dimension"),
        ("GET /api/v1/ontology/domains/{id}/relevant-dimensions", "Get domain-specific dimensions"),
        ("POST /api/v1/ontology/reload", "Reload ontology from TTL file")
    ]
    
    for endpoint, description in api_endpoints:
        print(f"   {endpoint}")
        print(f"      {description}")
        print()
    
    print("Key benefits of API integration:")
    print("   Dynamic ontology management without code changes")
    print("   Real-time prompt generation based on current ontology state")
    print("   Automatic review processing using latest domain definitions")
    print("   RESTful access to ontology structure and relationships")
    print()

if __name__ == "__main__":
    # Run all demonstrations
    print("Starting RDF Ontology System Demonstration")
    print("=" * 60)
    
    try:
        demonstrate_rdf_ontology()
        test_dynamic_prompts()
        query_ontology_example()
        demonstrate_api_integration()
        
        # Optional: Add new elements (uncomment to test)
        # add_new_domain_example()
        # add_new_dimension_example()
        
        print("\n" + "=" * 60)
        print("Demo Complete - RDF Ontology System Fully Operational!")
        
    except KeyboardInterrupt:
        print("\n\n Demo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo failed with error: {str(e)}")
        print("Please check your RDF ontology file and dependencies")
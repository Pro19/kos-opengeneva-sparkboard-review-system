import os
import argparse
import json
from typing import Dict, List, Any, Optional

from src.core.ontology import Ontology
from src.core.project import Project, load_all_projects
from src.core.reviewer import ReviewerProfile
from src.core.review import ReviewAnalyzer
from src.core.feedback import FeedbackGenerator
from src.infrastructure.config import PATHS, SETTINGS
from src.infrastructure.logging_utils import logger

def check_requirements():
    """Check for required dependencies and warn about optional ones."""
    from src.infrastructure.logging_utils import logger
    
    # Required dependencies
    required = ["requests", "sklearn", "rdflib"]
    missing_required = []
    
    # Optional dependencies
    optional = {
        "matplotlib": "Visualization charts will be skipped"
    }
    missing_optional = []
    
    # Check required
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    # Check optional
    for package, message in optional.items():
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(f"{package} - {message}")
    
    # Report results
    if missing_required:
        logger.error(f"Missing required dependencies: {', '.join(missing_required)}")
        logger.error("Please install them with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        logger.warning("Missing optional dependencies:")
        for missing in missing_optional:
            logger.warning(f"  - {missing}")
    
    return True

def process_project(project: Project, ontology: Ontology, output_dir: str = "output") -> None:
    """
    Process a single project through the RDF ontology-driven review pipeline.
    
    Args:
        project: Project object to process
        ontology: RDF Ontology object
        output_dir: Directory to save output files
    """
    logger.info(f"Processing project: {project.project_id}")
    
    # Initialize components with RDF ontology
    reviewer_profiler = ReviewerProfile(ontology)
    review_analyzer = ReviewAnalyzer(ontology, reviewer_profiler)
    feedback_generator = FeedbackGenerator(ontology)
    
    # Step 1: Get reviewer insights before processing
    logger.info("Analyzing reviewer profiles...")
    initial_insights = reviewer_profiler.get_reviewer_insights(project)
    logger.info(f"Initial reviewer analysis: {initial_insights['total_reviewers']} reviewers across {len(initial_insights['domain_coverage'])} domains")
    
    # Step 2: Analyze all reviews for the project using RDF ontology
    logger.info("Analyzing reviews with RDF ontology...")
    review_analyzer.analyze_project_reviews(project)
    
    # Step 3: Generate feedback report with dynamic dimensions
    logger.info("Generating feedback report with dynamic dimensions...")
    report_path = feedback_generator.generate_feedback_report(project, output_dir)
    logger.info(f"Feedback report saved to: {report_path}")
    
    # Step 4: Prepare visualization data with ontology information
    viz_data = feedback_generator.visualize_feedback(project)
    viz_path = os.path.join(output_dir, f"{project.project_id}_visualization.json")
    with open(viz_path, 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, indent=2)
    logger.info(f"Visualization data saved to: {viz_path}")
    
    # Step 5: Generate reviewer insights report
    final_insights = reviewer_profiler.get_reviewer_insights(project)
    insights_path = os.path.join(output_dir, f"{project.project_id}_reviewer_insights.json")
    with open(insights_path, 'w', encoding='utf-8') as f:
        json.dump(final_insights, f, indent=2)
    logger.info(f"Reviewer insights saved to: {insights_path}")
    
    # Step 6: Get missing domain recommendations
    missing_domains = reviewer_profiler.get_missing_domain_recommendations(project)
    if missing_domains:
        logger.info("Missing domain recommendations:")
        for rec in missing_domains[:3]:  # Show top 3
            logger.info(f"  - {rec['domain_name']}: {rec['recommendation']} (relevance: {rec['relevance_score']:.2f})")
    
    # Step 7: Update ontology with project insights (if enabled)
    update_ontology = SETTINGS.get("update_ontology", False)
    if update_ontology:
        logger.info("Updating ontology with project insights...")
        try:
            ontology.update_ontology_with_llm(project.get_full_description())
            logger.info("Ontology updated successfully")
        except Exception as e:
            logger.warning(f"Failed to update ontology: {str(e)}")
    else:
        logger.info("Skipping ontology update (disabled in settings)")

def analyze_ontology(ontology: Ontology) -> None:
    """
    Analyze and display information about the loaded ontology.
    
    Args:
        ontology: RDF Ontology object
    """
    logger.info("=== Ontology Analysis ===")
    
    # Get basic stats
    domains = ontology.rdf_ontology.get_domains()
    dimensions = ontology.rdf_ontology.get_impact_dimensions()
    levels = ontology.rdf_ontology.get_expertise_levels()
    project_types = ontology.rdf_ontology.get_project_types()
    
    logger.info(f"Loaded RDF ontology with:")
    logger.info(f"  - {len(domains)} domains")
    logger.info(f"  - {len(dimensions)} evaluation dimensions")
    logger.info(f"  - {len(levels)} expertise levels")
    logger.info(f"  - {len(project_types)} project types")
    
    # Show domains with their keywords
    logger.info("\nDomains:")
    for domain in domains:
        keywords = ', '.join(domain['keywords'][:3]) + ('...' if len(domain['keywords']) > 3 else '')
        logger.info(f"  - {domain['name']}: {keywords}")
    
    # Show dimensions
    logger.info("\nEvaluation Dimensions:")
    for dim in dimensions:
        logger.info(f"  - {dim['name']}: {dim['description'][:50]}...")
    
    # Show expertise levels
    logger.info("\nExpertise Levels:")
    for level in levels:
        conf_range = f"{level['confidence_range'][0]}-{level['confidence_range'][1]}"
        logger.info(f"  - {level['name']} ({conf_range}): {level['description']}")

def validate_ontology(ontology: Ontology) -> bool:
    """
    Validate the ontology structure and relationships.
    
    Args:
        ontology: RDF Ontology object
        
    Returns:
        True if validation passes, False otherwise
    """
    logger.info("=== Ontology Validation ===")
    
    try:
        # Check basic structure
        domains = ontology.get_domains()
        if not domains:
            logger.error("No domains found in ontology")
            return False
        
        # Check that all domains have relevant dimensions
        for domain in domains:
            relevant_dims = ontology.get_relevant_dimensions_for_domain(domain)
            if not relevant_dims:
                logger.warning(f"Domain '{domain}' has no relevant dimensions defined")
        
        # Check dimension consistency
        dimensions = ontology.rdf_ontology.get_impact_dimensions()
        for dim in dimensions:
            if not dim.get('scale'):
                logger.warning(f"Dimension '{dim['id']}' has no scale defined")
        
        # Check expertise levels coverage
        levels = ontology.rdf_ontology.get_expertise_levels()
        coverage = []
        for level in levels:
            coverage.extend(range(level['confidence_range'][0], level['confidence_range'][1] + 1))
        
        if not (0 in coverage and 100 in coverage):
            logger.warning("Expertise levels don't cover full confidence range (0-100)")
        
        logger.info("Ontology validation completed")
        return True
        
    except Exception as e:
        logger.error(f"Ontology validation failed: {str(e)}")
        return False

def create_ontology_backup(ontology: Ontology, backup_dir: str = "backups") -> str:
    """
    Create a backup of the current ontology.
    
    Args:
        ontology: RDF Ontology object
        backup_dir: Directory to store backups
        
    Returns:
        Path to the backup file
    """
    import datetime
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"ontology_backup_{timestamp}.ttl")
    
    # Copy the TTL file
    import shutil
    shutil.copy2(ontology.ttl_path, backup_path)
    
    logger.info(f"Ontology backup created: {backup_path}")
    return backup_path

def main() -> None:
    """Main entry point for the RDF ontology-driven application."""
    if not check_requirements():
        return
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="RDF Ontology-Driven Hackathon Review System")
    parser.add_argument("--project", help="Process a specific project ID")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--new-ontology", action="store_true", help="Create a new ontology instead of loading existing")
    parser.add_argument("--analyze-ontology", action="store_true", help="Analyze and display ontology information")
    parser.add_argument("--validate-ontology", action="store_true", help="Validate ontology structure and relationships")
    parser.add_argument("--backup-ontology", action="store_true", help="Create a backup of the current ontology")
    parser.add_argument("--force-ttl", action="store_true", help="Force use of TTL file even if JSON exists")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize or load RDF ontology
    logger.info("Initializing RDF ontology...")
    try:
        ontology = Ontology(load_existing=not args.new_ontology)
        logger.info("RDF ontology loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load RDF ontology: {str(e)}")
        logger.error("Please ensure data/ontology.ttl exists and is properly formatted")
        return
    
    # Handle ontology-specific commands
    if args.analyze_ontology:
        analyze_ontology(ontology)
        return
    
    if args.validate_ontology:
        if validate_ontology(ontology):
            logger.info("Ontology validation passed")
        else:
            logger.error("Ontology validation failed")
            return
    
    if args.backup_ontology:
        create_ontology_backup(ontology)
        return
    
    # Load projects
    projects = load_all_projects()
    logger.info(f"Loaded {len(projects)} projects")
    
    if not projects:
        logger.warning("No projects found. Please add project directories to the projects/ folder.")
        return
    
    # Process projects
    if args.project:
        # Process specific project
        for project in projects:
            if project.project_id == args.project:
                process_project(project, ontology, args.output)
                break
        else:
            logger.error(f"Project {args.project} not found")
    else:
        # Process all projects
        for i, project in enumerate(projects, 1):
            logger.info(f"Processing project {i}/{len(projects)}: {project.project_id}")
            try:
                process_project(project, ontology, args.output)
                logger.info(f"Successfully processed {project.project_id}")
            except Exception as e:
                logger.error(f"Error processing {project.project_id}: {str(e)}")
                continue
    
    # Save final ontology state
    ontology.save_ontology()
    logger.info("Processing complete! RDF ontology saved.")

if __name__ == "__main__":
    main()
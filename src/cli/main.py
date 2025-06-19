"""
Main entry point for the ontology-driven hackathon review system.
"""

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
    required = ["requests", "sklearn"]
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
    Process a single project through the review pipeline.
    
    Args:
        project: Project object to process
        ontology: Ontology object
        output_dir: Directory to save output files
    """
    logger.info(f"Processing project: {project.project_id}")
    
    # Initialize components
    reviewer_profiler = ReviewerProfile(ontology)
    review_analyzer = ReviewAnalyzer(ontology, reviewer_profiler)
    feedback_generator = FeedbackGenerator(ontology)
    
    # Step 1: Analyze all reviews for the project
    logger.info("Analyzing reviews")
    review_analyzer.analyze_project_reviews(project)
    
    # Step 2: Generate feedback report
    logger.info("Generating feedback report")
    report_path = feedback_generator.generate_feedback_report(project, output_dir)
    logger.info(f"Feedback report saved to: {report_path}")
    
    # Step 3: Prepare visualization data
    viz_data = feedback_generator.visualize_feedback(project)
    viz_path = os.path.join(output_dir, f"{project.project_id}_visualization.json")
    with open(viz_path, 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, indent=2)
    logger.info(f"Visualization data saved to: {viz_path}")
    
    # Step 4: Update ontology with project insights
    update_ontology = SETTINGS.get("update_ontology", False)
    if update_ontology:
        logger.info("Updating ontology with project insights...")
        ontology.update_ontology_with_llm(project.get_full_description())
    else:
        logger.info("Skipping ontology update (disabled in settings)")

def main() -> None:
    """Main entry point for the application."""
    if not check_requirements():
        return
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ontology-Driven Hackathon Review System")
    parser.add_argument("--project", help="Process a specific project ID")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--new-ontology", action="store_true", help="Create a new ontology instead of loading existing")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize or load ontology
    logger.info("Initializing ontology")
    ontology = Ontology(load_existing=not args.new_ontology)
    
    # Load projects
    projects = load_all_projects()
    logger.info(f"Loaded {len(projects)} projects")
    
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
        for project in projects:
            process_project(project, ontology, args.output)
    
    # Save final ontology
    ontology.save_ontology()
    logger.info("Processing complete!")

if __name__ == "__main__":
    main()
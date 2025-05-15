"""
Main entry point for the ontology-driven hackathon review system.
"""

import os
import argparse
import json
from typing import Dict, List, Any, Optional

from ontology import Ontology
from project import Project, load_all_projects
from reviewer import ReviewerProfile
from review import ReviewAnalyzer
from feedback import FeedbackGenerator
from config import PATHS

def process_project(project: Project, ontology: Ontology, output_dir: str = "output") -> None:
    """
    Process a single project through the review pipeline.
    
    Args:
        project: Project object to process
        ontology: Ontology object
        output_dir: Directory to save output files
    """
    print(f"\nProcessing project: {project.project_id}")
    
    # Initialize components
    reviewer_profiler = ReviewerProfile(ontology)
    review_analyzer = ReviewAnalyzer(ontology, reviewer_profiler)
    feedback_generator = FeedbackGenerator(ontology)
    
    # Step 1: Analyze all reviews for the project
    print("Analyzing reviews...")
    review_analyzer.analyze_project_reviews(project)
    
    # Step 2: Generate feedback report
    print("Generating feedback report...")
    report_path = feedback_generator.generate_feedback_report(project, output_dir)
    print(f"Feedback report saved to: {report_path}")
    
    # Step 3: Prepare visualization data
    viz_data = feedback_generator.visualize_feedback(project)
    viz_path = os.path.join(output_dir, f"{project.project_id}_visualization.json")
    with open(viz_path, 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, indent=2)
    print(f"Visualization data saved to: {viz_path}")
    
    # Step 4: Update ontology with project insights
    print("Updating ontology with project insights...")
    ontology.update_ontology_with_llm(project.get_full_description())

def main() -> None:
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ontology-Driven Hackathon Review System")
    parser.add_argument("--project", help="Process a specific project ID")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--new-ontology", action="store_true", help="Create a new ontology instead of loading existing")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize or load ontology
    print("Initializing ontology...")
    ontology = Ontology(load_existing=not args.new_ontology)
    
    # Load projects
    projects = load_all_projects()
    print(f"Loaded {len(projects)} projects")
    
    if args.project:
        # Process specific project
        for project in projects:
            if project.project_id == args.project:
                process_project(project, ontology, args.output)
                break
        else:
            print(f"Project {args.project} not found")
    else:
        # Process all projects
        for project in projects:
            process_project(project, ontology, args.output)
    
    # Save final ontology
    ontology.save_ontology()
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
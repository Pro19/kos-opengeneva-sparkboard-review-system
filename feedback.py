"""
Feedback generation for hackathon review system.
"""

import os
from typing import Dict, List, Any, Optional
import json
from config import FEEDBACK_SETTINGS

class FeedbackGenerator:
    """Class for generating final feedback and visualizations."""
    
    def __init__(self, ontology):
        """
        Initialize the feedback generator.
        
        Args:
            ontology: Ontology object
        """
        self.ontology = ontology
        self.dimensions = FEEDBACK_SETTINGS.get("dimensions", [])
    
    def generate_feedback_report(self, project, output_dir: str = "output") -> str:
        """
        Generate a comprehensive feedback report for a project.
        
        Args:
            project: Project object
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare report data
        report_data = self._prepare_report_data(project)
        
        # Generate markdown report
        report_md = self._generate_markdown_report(report_data)
        
        # Save report to file
        report_file = os.path.join(output_dir, f"{project.project_id}_feedback.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_md)
        
        # Save JSON data for potential visualization
        json_file = os.path.join(output_dir, f"{project.project_id}_feedback.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        return report_file
    
    def _prepare_report_data(self, project) -> Dict[str, Any]:
        """
        Prepare data structure for the feedback report.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary with report data
        """
        report_data = {
            "project_id": project.project_id,
            "project_name": project.project_data.get("name", project.project_id),
            "project_description": project.project_data.get("description", ""),
            "feedback_scores": project.feedback_scores,
            "final_review": project.final_review,
            "reviews_by_domain": {},
            "artificial_reviews": []
        }
        
        # Group reviews by domain
        domains = {}
        for review in project.reviews:
            if review.get("is_accepted", False):
                domain = review.get("domain", "unknown")
                
                if domain not in domains:
                    domains[domain] = []
                
                # Prepare review data
                review_data = {
                    "reviewer_name": review.get("reviewer_name", "Anonymous"),
                    "expertise_level": review.get("expertise_level", "beginner"),
                    "confidence_score": review.get("confidence_score", 0),
                    "text_review": review.get("text_review", ""),
                    "sentiment_scores": review.get("sentiment_scores", {}),
                    "is_artificial": review.get("is_artificial", False)
                }
                
                domains[domain].append(review_data)
                
                # Track artificial reviews separately
                if review.get("is_artificial", False):
                    report_data["artificial_reviews"].append(review_data)
        
        report_data["reviews_by_domain"] = domains
        
        return report_data
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        Generate a markdown format report.
        
        Args:
            report_data: Dictionary with report data
            
        Returns:
            Markdown formatted report
        """
        md = f"# Feedback Report: {report_data['project_name']}\n\n"
        
        # Project description
        md += "## Project Description\n\n"
        md += f"{report_data['project_description']}\n\n"
        
        # Feedback scores
        md += "## Feedback Scores\n\n"
        md += "| Dimension | Score (1-5) |\n"
        md += "|-----------|------------|\n"
        
        for dimension, score in report_data["feedback_scores"].items():
            dimension_name = dimension.replace("_", " ").title()
            md += f"| {dimension_name} | {score} |\n"
        
        md += "\n"
        
        # Radar chart visualization note
        md += "> Note: A radar chart visualization of these scores can be generated from the accompanying JSON data.\n\n"
        
        # Final review
        md += "## Synthesized Review\n\n"
        md += f"{report_data['final_review']}\n\n"
        
        # Domain-specific feedback
        md += "## Domain-Specific Feedback\n\n"
        
        for domain, reviews in report_data["reviews_by_domain"].items():
            domain_name = domain.capitalize()
            md += f"### {domain_name} Perspective\n\n"
            
            for i, review in enumerate(reviews):
                reviewer_type = "AI-generated" if review.get("is_artificial", False) else "Human"
                expertise = review.get("expertise_level", "").capitalize()
                reviewer_name = review.get("reviewer_name", "Anonymous")
                
                md += f"#### {reviewer_type} {expertise} Reviewer: {reviewer_name}\n\n"
                md += f"**Confidence Score:** {review.get('confidence_score', 0)}/100\n\n"
                md += f"{review.get('text_review', '')}\n\n"
                
                # Add sentiment scores if available
                sentiment_scores = review.get("sentiment_scores", {})
                if sentiment_scores:
                    md += "**Dimension Scores:**\n\n"
                    md += "| Dimension | Score |\n"
                    md += "|-----------|-------|\n"
                    
                    for dim, score in sentiment_scores.items():
                        if dim != "overall_sentiment":
                            dim_name = dim.replace("_", " ").title()
                            md += f"| {dim_name} | {score} |\n"
                    
                    md += "\n"
        
        # Artificial reviews note
        if report_data["artificial_reviews"]:
            md += "## Note on AI-Generated Reviews\n\n"
            md += f"This feedback report includes {len(report_data['artificial_reviews'])} AI-generated reviews to provide perspectives from domains where human reviews were not available. These reviews are clearly marked as 'AI-generated' and are weighted less heavily in the final scores than human reviews.\n\n"
        
        # Methodology
        md += "## Methodology\n\n"
        md += "This feedback was generated using an ontology-driven AI system that:\n\n"
        md += "1. Classified human reviewers by domain expertise\n"
        md += "2. Filtered reviews based on domain relevance and confidence\n"
        md += "3. Generated additional reviews for missing domain perspectives\n"
        md += "4. Scored the project across multiple dimensions\n"
        md += "5. Synthesized a comprehensive review from multiple perspectives\n\n"
        
        md += "The system uses a structured ontology to represent reviewer characteristics and feedback dimensions, enabling multi-perspective analysis that captures how different stakeholders perceive the project.\n"
        
        return md
    
    def visualize_feedback(self, project) -> Dict[str, Any]:
        """
        Prepare data for feedback visualization.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary with visualization data
        """
        visualization_data = {
            "project_name": project.project_data.get("name", project.project_id),
            "radar_chart": {
                "dimensions": [],
                "scores": []
            },
            "domain_breakdown": []
        }
        
        # Prepare radar chart data
        for dimension, score in project.feedback_scores.items():
            if dimension != "overall_sentiment":
                visualization_data["radar_chart"]["dimensions"].append(
                    dimension.replace("_", " ").title()
                )
                visualization_data["radar_chart"]["scores"].append(score)
        
        # Prepare domain breakdown
        domains_with_reviews = {}
        for review in project.reviews:
            if review.get("is_accepted", False):
                domain = review.get("domain", "unknown")
                if domain not in domains_with_reviews:
                    domains_with_reviews[domain] = {
                        "name": domain.capitalize(),
                        "count": 0,
                        "artificial_count": 0,
                        "average_scores": {}
                    }
                
                domains_with_reviews[domain]["count"] += 1
                
                if review.get("is_artificial", False):
                    domains_with_reviews[domain]["artificial_count"] += 1
                
                # Aggregate scores by domain
                sentiment_scores = review.get("sentiment_scores", {})
                for dimension, score in sentiment_scores.items():
                    if dimension != "overall_sentiment":
                        if dimension not in domains_with_reviews[domain]["average_scores"]:
                            domains_with_reviews[domain]["average_scores"][dimension] = []
                        
                        domains_with_reviews[domain]["average_scores"][dimension].append(score)
        
        # Calculate average scores by domain
        for domain, data in domains_with_reviews.items():
            domain_data = {
                "name": data["name"],
                "review_count": data["count"],
                "artificial_count": data["artificial_count"],
                "dimension_scores": {}
            }
            
            for dimension, scores in data["average_scores"].items():
                if scores:
                    domain_data["dimension_scores"][dimension.replace("_", " ").title()] = sum(scores) / len(scores)
            
            visualization_data["domain_breakdown"].append(domain_data)
        
        return visualization_data
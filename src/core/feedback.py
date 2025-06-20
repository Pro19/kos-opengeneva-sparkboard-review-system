"""
Updated feedback generation for hackathon review system.
Now uses RDF ontology for dynamic dimensions and prompts.
"""

import os
from typing import Dict, List, Any, Optional
import json
import matplotlib.pyplot as plt
import numpy as np
from src.infrastructure.config import FEEDBACK_SETTINGS
from src.infrastructure.utils import remove_thinking_tags

class FeedbackGenerator:
    """Class for generating final feedback and visualizations using RDF ontology."""
    
    def __init__(self, ontology):
        """
        Initialize the feedback generator.
        
        Args:
            ontology: RDF Ontology object with dynamic capabilities
        """
        self.ontology = ontology
        # Get dimensions dynamically from ontology instead of hardcoded list
        self.dimensions = self._get_dynamic_dimensions()
    
    def _get_dynamic_dimensions(self) -> List[str]:
        """Get evaluation dimensions dynamically from ontology."""
        dimensions = self.ontology.rdf_ontology.get_impact_dimensions()
        return [dim["id"] for dim in dimensions]
    
    def generate_feedback_report(self, project, output_dir: str = "output") -> str:
        """
        Generate a comprehensive feedback report for a project using dynamic ontology.
        
        Args:
            project: Project object
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        from src.infrastructure.logging_utils import logger
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create visualizations directory
        viz_dir = os.path.join(output_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        # Prepare report data with dynamic dimensions
        report_data = self._prepare_report_data(project)
        
        # Generate radar chart with dynamic dimensions
        chart_path = self._generate_radar_chart(project, viz_dir)
        if chart_path:
            logger.info(f"Radar chart saved to: {chart_path}")
            # Add chart path to report data
            report_data["chart_path"] = os.path.relpath(chart_path, output_dir)
        
        # Generate markdown report
        report_md = self._generate_markdown_report(report_data)

        # One final cleaning pass to make sure no thinking tags remain
        report_md = remove_thinking_tags(report_md)
        
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
        Prepare data structure for the feedback report using dynamic ontology.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary with report data
        """
        # Get dimension information from ontology for better descriptions
        dimension_info = {}
        for dim in self.ontology.rdf_ontology.get_impact_dimensions():
            dimension_info[dim["id"]] = {
                "name": dim["name"],
                "description": dim["description"],
                "scale": dim.get("scale", {})
            }
        
        # Get domain information from ontology
        domain_info = {}
        for domain in self.ontology.rdf_ontology.get_domains():
            domain_info[domain["id"]] = {
                "name": domain["name"],
                "description": domain["description"],
                "keywords": domain["keywords"]
            }
        
        report_data = {
            "project_id": project.project_id,
            "project_name": project.project_data.get("name", project.project_id),
            "project_description": project.project_data.get("description", ""),
            "feedback_scores": project.feedback_scores,
            "final_review": project.final_review,
            "reviews_by_domain": {},
            "artificial_reviews": [],
            "dimension_info": dimension_info,  # Added for richer reporting
            "domain_info": domain_info,        # Added for richer reporting
            "ontology_stats": self._get_ontology_stats()
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
                    "is_artificial": review.get("is_artificial", False),
                    "relevance_score": review.get("relevance_score", 0.0)
                }
                
                domains[domain].append(review_data)
                
                # Track artificial reviews separately
                if review.get("is_artificial", False):
                    report_data["artificial_reviews"].append(review_data)
        
        report_data["reviews_by_domain"] = domains
        
        return report_data
    
    def _get_ontology_stats(self) -> Dict[str, Any]:
        """Get statistics about the ontology for reporting."""
        domains = self.ontology.rdf_ontology.get_domains()
        dimensions = self.ontology.rdf_ontology.get_impact_dimensions()
        levels = self.ontology.rdf_ontology.get_expertise_levels()
        project_types = self.ontology.rdf_ontology.get_project_types()
        
        return {
            "total_domains": len(domains),
            "total_dimensions": len(dimensions),
            "total_expertise_levels": len(levels),
            "total_project_types": len(project_types),
            "domains": [d["name"] for d in domains],
            "dimensions": [d["name"] for d in dimensions]
        }
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        Generate a markdown format report with enhanced ontology information.
        
        Args:
            report_data: Dictionary with report data
            
        Returns:
            Markdown formatted report
        """
        md = f"# Feedback Report: {report_data['project_name']}\n\n"
        
        # Add ontology information
        ontology_stats = report_data.get("ontology_stats", {})
        md += "## Ontology-Driven Analysis\n\n"
        md += f"This report was generated using an RDF ontology with:\n"
        md += f"- **{ontology_stats.get('total_domains', 0)} domains**: {', '.join(ontology_stats.get('domains', []))}\n"
        md += f"- **{ontology_stats.get('total_dimensions', 0)} evaluation dimensions**: {', '.join(ontology_stats.get('dimensions', []))}\n"
        md += f"- **{ontology_stats.get('total_expertise_levels', 0)} expertise levels**\n\n"
    
        # Project description
        md += "## Project Description\n\n"
        md += f"{report_data['project_description']}\n\n"
        
        # Add radar chart if available
        if report_data.get("chart_path"):
            md += "## Project Evaluation Chart\n\n"
            md += f"![Project Evaluation Radar Chart]({report_data['chart_path']})\n\n"
        
        # Feedback scores with enhanced information
        md += "## Feedback Scores\n\n"
        dimension_info = report_data.get("dimension_info", {})
        
        md += "| Dimension | Score (1-5) | Description |\n"
        md += "|-----------|-------------|-------------|\n"
        
        for dimension_id, score in report_data["feedback_scores"].items():
            dim_info = dimension_info.get(dimension_id, {})
            dimension_name = dim_info.get("name", dimension_id.replace("_", " ").title())
            description = dim_info.get("description", "No description available")
            md += f"| {dimension_name} | {score} | {description[:50]}... |\n"
        
        md += "\n"
        
        # Radar chart visualization note
        md += "> Note: The radar chart above visualizes these scores across all evaluation dimensions defined in the ontology.\n\n"
        
        # Final review
        md += "## Synthesized Review\n\n"
        md += f"{report_data['final_review']}\n\n"
        
        # Domain-specific feedback with enhanced information
        md += "## Domain-Specific Feedback\n\n"
        domain_info = report_data.get("domain_info", {})
        
        for domain_id, reviews in report_data["reviews_by_domain"].items():
            domain_data = domain_info.get(domain_id, {})
            domain_name = domain_data.get("name", domain_id.capitalize())
            domain_desc = domain_data.get("description", "")
            
            md += f"### {domain_name} Perspective\n\n"
            if domain_desc:
                md += f"*{domain_desc}*\n\n"
            
            for i, review in enumerate(reviews):
                reviewer_type = "AI-generated" if review.get("is_artificial", False) else "Human"
                expertise = review.get("expertise_level", "").capitalize()
                reviewer_name = review.get("reviewer_name", "Anonymous")
                relevance = review.get("relevance_score", 0.0)
                
                md += f"#### {reviewer_type} {expertise} Reviewer: {reviewer_name}\n\n"
                md += f"**Confidence Score:** {review.get('confidence_score', 0)}/100\n"
                md += f"**Domain Relevance:** {relevance:.2f}\n\n"
                md += f"{review.get('text_review', '')}\n\n"
                
                # Add sentiment scores if available
                sentiment_scores = review.get("sentiment_scores", {})
                if sentiment_scores:
                    md += "**Dimension Scores:**\n\n"
                    md += "| Dimension | Score | Scale Description |\n"
                    md += "|-----------|-------|-------------------|\n"
                    
                    for dim_id, score in sentiment_scores.items():
                        if dim_id != "overall_sentiment":
                            dim_info = dimension_info.get(dim_id, {})
                            dim_name = dim_info.get("name", dim_id.replace("_", " ").title())
                            scale_info = dim_info.get("scale", {})
                            scale_desc = scale_info.get(str(int(score)), "No description") if score == int(score) else "Between ratings"
                            md += f"| {dim_name} | {score} | {scale_desc} |\n"
                    
                    md += "\n"
        
        # Artificial reviews note
        if report_data["artificial_reviews"]:
            md += "## Note on AI-Generated Reviews\n\n"
            md += f"This feedback report includes {len(report_data['artificial_reviews'])} AI-generated reviews to provide perspectives from domains where human reviews were not available. These reviews are generated using dynamic prompts based on the ontological definitions and are clearly marked as 'AI-generated'. They are weighted less heavily in the final scores than human reviews.\n\n"
        
        # Enhanced methodology section
        md += "## Methodology\n\n"
        md += "This feedback was generated using an **RDF ontology-driven AI system** that:\n\n"
        md += "1. **Dynamically classifies** human reviewers by domain expertise using semantic definitions\n"
        md += "2. **Filters reviews** based on domain relevance and confidence scores\n"
        md += "3. **Generates contextual prompts** from ontological knowledge for AI review generation\n"
        md += "4. **Scores projects** across evaluation dimensions defined in the ontology\n"
        md += "5. **Synthesizes comprehensive reviews** from multiple perspectives using dynamic prompt templates\n\n"
        
        md += "### Ontology Structure\n\n"
        md += "The system uses a structured RDF/TTL ontology that represents:\n"
        md += "- **Domain expertise** (e.g., Technical, Clinical, Business, Design)\n"
        md += "- **Evaluation dimensions** (e.g., Technical Feasibility, Innovation, Impact)\n"
        md += "- **Expertise levels** (Beginner to Expert based on confidence scores)\n"
        md += "- **Semantic relationships** between domains and relevant evaluation criteria\n\n"
        
        md += "This ontological foundation enables the system to generate contextually appropriate prompts and provide multi-perspective analysis that captures how different stakeholder groups perceive and would guide each project's development.\n"
        
        return md
    
    def visualize_feedback(self, project) -> Dict[str, Any]:
        """
        Prepare data for feedback visualization using dynamic dimensions.
        
        Args:
            project: Project object
            
        Returns:
            Dictionary with visualization data
        """
        # Get dimension information from ontology
        dimensions_info = self.ontology.rdf_ontology.get_impact_dimensions()
        dimension_map = {dim["id"]: dim["name"] for dim in dimensions_info}
        
        visualization_data = {
            "project_name": project.project_data.get("name", project.project_id),
            "radar_chart": {
                "dimensions": [],
                "scores": []
            },
            "domain_breakdown": [],
            "dimension_info": {dim["id"]: dim for dim in dimensions_info}  # Added for richer viz
        }
        
        # Prepare radar chart data with dynamic dimensions
        for dimension_id, score in project.feedback_scores.items():
            if dimension_id != "overall_sentiment" and dimension_id in dimension_map:
                visualization_data["radar_chart"]["dimensions"].append(
                    dimension_map[dimension_id]
                )
                visualization_data["radar_chart"]["scores"].append(score)
        
        # Prepare domain breakdown
        domains_with_reviews = {}
        for review in project.reviews:
            if review.get("is_accepted", False):
                domain = review.get("domain", "unknown")
                if domain not in domains_with_reviews:
                    # Get domain info from ontology
                    domain_info = self.ontology.rdf_ontology.get_domain_by_id(domain)
                    domain_name = domain_info["name"] if domain_info else domain.capitalize()
                    
                    domains_with_reviews[domain] = {
                        "name": domain_name,
                        "count": 0,
                        "artificial_count": 0,
                        "average_scores": {},
                        "relevance_scores": []
                    }
                
                domains_with_reviews[domain]["count"] += 1
                
                if review.get("is_artificial", False):
                    domains_with_reviews[domain]["artificial_count"] += 1
                
                # Add relevance score
                if review.get("relevance_score"):
                    domains_with_reviews[domain]["relevance_scores"].append(review["relevance_score"])
                
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
                "dimension_scores": {},
                "average_relevance": sum(data["relevance_scores"]) / len(data["relevance_scores"]) if data["relevance_scores"] else 0.0
            }
            
            for dimension, scores in data["average_scores"].items():
                if scores and dimension in dimension_map:
                    domain_data["dimension_scores"][dimension_map[dimension]] = round(sum(scores) / len(scores), 1)
            
            visualization_data["domain_breakdown"].append(domain_data)
        
        return visualization_data
    
    def _generate_radar_chart(self, project, output_dir: str) -> Optional[str]:
        """Generate a radar chart for the project feedback scores using dynamic dimensions."""
        from src.infrastructure.logging_utils import logger
        from src.infrastructure.config import FEEDBACK_SETTINGS
        
        try:
            # Get chart settings from config
            chart_settings = FEEDBACK_SETTINGS.get("chart", {})
            chart_width = chart_settings.get("width", 8)
            chart_height = chart_settings.get("height", 6)
            chart_dpi = chart_settings.get("dpi", 300)
            
            # Get dimensions and scores dynamically from ontology
            dimensions_info = self.ontology.rdf_ontology.get_impact_dimensions()
            dimension_map = {dim["id"]: dim["name"] for dim in dimensions_info}
            
            dimensions = []
            scores = []
            
            for dimension_id, score in project.feedback_scores.items():
                if dimension_id != "overall_sentiment" and dimension_id in dimension_map:
                    dimensions.append(dimension_map[dimension_id])
                    scores.append(score)
            
            if not dimensions:
                logger.warning("No dimensions found for radar chart.")
                return None
            
            # Number of variables
            N = len(dimensions)
            
            # Create angle and repeat first value to close the polygon
            angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
            scores.append(scores[0])
            angles.append(angles[0])
            dimensions.append(dimensions[0])
            
            # Create plot
            fig, ax = plt.subplots(figsize=(chart_width, chart_height), subplot_kw=dict(polar=True))
            
            # Plot data
            ax.plot(angles, scores, 'o-', linewidth=2, label='Project Score')
            ax.fill(angles, scores, alpha=0.25)
            
            # Set labels
            ax.set_thetagrids(np.degrees(angles[:-1]), dimensions[:-1])
            
            # Set y-axis limits
            ax.set_ylim(0, 5)
            ax.set_yticks([1, 2, 3, 4, 5])
            ax.set_yticklabels(['1', '2', '3', '4', '5'])
            ax.grid(True)
            
            # Add title
            plt.title(f"Project Evaluation: {project.project_data.get('name', project.project_id)}", 
                    size=15, color='darkblue', y=1.1)
            
            # Add subtitle with ontology info
            plt.figtext(0.5, 0.02, f"Based on {len(dimensions)-1} evaluation dimensions from RDF ontology", 
                       ha='center', fontsize=10, style='italic')
            
            # Save chart
            chart_file = os.path.join(output_dir, f"{project.project_id}_radar_chart.png")
            plt.tight_layout()
            plt.savefig(chart_file, dpi=chart_dpi, bbox_inches='tight')
            plt.close()
            
            return chart_file
        
        except Exception as e:
            logger.error(f"Error generating radar chart: {str(e)}")
            return None
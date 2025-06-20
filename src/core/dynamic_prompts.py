from typing import Dict, List, Any, Optional
from src.infrastructure.logging_utils import logger


class DynamicPromptGenerator:
    def __init__(self, ontology):
        """
        Initialize the prompt generator with an ontology.
        
        Args:
            ontology: RDFOntology instance
        """
        self.ontology = ontology
    
    def generate_artificial_review_prompt(self, project_description: str, domain_id: str) -> str:
        """
        Generate a prompt for creating an artificial review from a specific domain perspective.
        
        Args:
            project_description: Description of the project
            domain_id: Domain ID to generate review from
            
        Returns:
            Generated prompt string
        """
        # Get domain details from ontology
        domain = self.ontology.get_domain_by_id(domain_id)
        if not domain:
            logger.error(f"Domain {domain_id} not found in ontology")
            return ""
        
        domain_name = domain.get("name", domain_id.capitalize())
        domain_desc = domain.get("description", "")
        keywords = domain.get("keywords", [])
        
        # Get relevant dimensions for this domain
        relevant_dimensions = self.ontology.get_relevant_dimensions_for_domain(domain_id)
        dimension_descriptions = []
        
        for dim_id in relevant_dimensions:
            dimension = self.ontology.get_dimension_by_id(dim_id)
            if dimension:
                dimension_descriptions.append(
                    f"- {dimension['name']}: {dimension['description']}"
                )
        
        # Build the prompt dynamically
        prompt = f"""You are an expert reviewer with deep expertise in {domain_name}.

Domain Context: {domain_desc}
Your expertise encompasses: {', '.join(keywords)}

You are reviewing a hackathon project with the following description:

{project_description}

Please provide a detailed review of this project from your expertise perspective of {domain_name}.

Focus particularly on these evaluation dimensions that are most relevant to your domain:
{chr(10).join(dimension_descriptions)}

Your review should:
1. Assess the project from your specific domain perspective
2. Consider practical implications for {domain_name} stakeholders
3. Evaluate feasibility and potential impact within your field
4. Provide constructive criticism and suggestions
5. Be thorough but concise (around 300-400 words)

Also provide a confidence score between 0-100 that reflects how confident you are in your assessment.
As an expert in {domain_name}, your confidence score should typically be high (85-95) when reviewing projects relevant to your domain.

Structure your response as:
REVIEW: [Your detailed review text]
CONFIDENCE: [Your confidence score 0-100]"""
        
        return prompt
    
    def generate_sentiment_analysis_prompt(self, review_text: str) -> str:
        """
        Generate a prompt for analyzing review sentiment across dimensions.
        
        Args:
            review_text: The review text to analyze
            
        Returns:
            Generated prompt string
        """
        # Get all dimensions from ontology
        dimensions = self.ontology.get_impact_dimensions()
        
        # Build dimension descriptions for the prompt
        dimension_info = []
        dimension_names = []
        
        for dim in dimensions:
            dim_id = dim["id"]
            dim_name = dim["name"]
            dim_desc = dim["description"]
            scale = dim.get("scale", {})
            
            # Format scale information
            scale_desc = "Scale:\n"
            for i in range(1, 6):
                if str(i) in scale:
                    scale_desc += f"  {i}: {scale[str(i)]}\n"
            
            dimension_info.append(f"{dim_name} ({dim_id}):\n{dim_desc}\n{scale_desc}")
            dimension_names.append(dim_id)
        
        prompt = f"""Analyze the following project review and rate it on each evaluation dimension.

Review Text:
{review_text}

Evaluation Dimensions:
{chr(10).join(dimension_info)}

For each dimension, provide a score from 1.0 to 5.0 based on what the review indicates about the project.
If a dimension is not addressed in the review, infer a reasonable score based on the overall tone.

Also provide an overall_sentiment score (1.0 to 5.0) representing the general positivity/negativity of the review.

You MUST respond with ONLY a valid JSON object in this exact format:
{{
{chr(10).join(f'  "{dim_id}": 3.0,' for dim_id in dimension_names)}
  "overall_sentiment": 3.0
}}

Replace the example values with your actual ratings. Use only numbers between 1.0 and 5.0.
Do not include any other text or explanation."""
        
        return prompt
    
    def generate_reviewer_classification_prompt(self, reviewer_name: str, review_text: str) -> str:
        """
        Generate a prompt for classifying a reviewer into a domain.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text of the review
            
        Returns:
            Generated prompt string
        """
        # Get all domains from ontology
        domains = self.ontology.get_domains()
        
        # Build domain descriptions
        domain_options = []
        for domain in domains:
            keywords = ', '.join(domain.get("keywords", []))
            domain_options.append(
                f"- {domain['name']} ({domain['id']}): {domain['description']}\n"
                f"  Keywords: {keywords}"
            )
        
        prompt = f"""Based on the following review, classify the reviewer into the most appropriate domain.

Reviewer: {reviewer_name}
Review Text:
{review_text}

Available Domains:
{chr(10).join(domain_options)}

Analyze the language, focus areas, and expertise demonstrated in the review.
Consider:
1. Technical terminology used
2. Aspects of the project they focus on
3. Type of concerns or suggestions raised
4. Professional perspective evident in the review

Return ONLY the domain ID (e.g., "technical", "clinical", "business") that best matches this reviewer's expertise.
Do not include any explanation or additional text."""
        
        return prompt
    
    def generate_final_review_synthesis_prompt(self, project_info: Dict[str, Any], 
                                             reviews_data: List[Dict[str, Any]], 
                                             feedback_scores: Dict[str, float]) -> str:
        """
        Generate a prompt for synthesizing all reviews into a final comprehensive review.
        
        Args:
            project_info: Project name and description
            reviews_data: List of review data with domains and sentiments
            feedback_scores: Aggregated dimension scores
            
        Returns:
            Generated prompt string
        """
        # Get dimension details from ontology
        dimensions = self.ontology.get_impact_dimensions()
        dimension_map = {dim["id"]: dim["name"] for dim in dimensions}
        
        # Format dimension scores
        dimension_scores_text = ""
        for dim_id, score in feedback_scores.items():
            if dim_id != "overall_sentiment" and dim_id in dimension_map:
                dimension_scores_text += f"- {dimension_map[dim_id]}: {score}/5.0\n"
        
        # Group reviews by domain
        reviews_by_domain = {}
        for review in reviews_data:
            domain_id = review.get("domain", "unknown")
            if domain_id not in reviews_by_domain:
                domain = self.ontology.get_domain_by_id(domain_id)
                domain_name = domain["name"] if domain else domain_id.capitalize()
                reviews_by_domain[domain_id] = {
                    "name": domain_name,
                    "reviews": []
                }
            reviews_by_domain[domain_id]["reviews"].append(review)
        
        # Format domain insights
        domain_insights_text = ""
        for domain_id, domain_data in reviews_by_domain.items():
            domain_insights_text += f"\n{domain_data['name']} Perspective:\n"
            
            for review in domain_data["reviews"]:
                review_type = "AI-generated" if review.get("is_artificial", False) else "Human"
                expertise = review.get("expertise_level", "").capitalize()
                snippet = review.get("text_review", "")[:150].replace('\n', ' ').strip()
                domain_insights_text += f"- {review_type} {expertise} Review: {snippet}...\n"
        
        prompt = f"""You are an expert reviewer synthesizing multiple perspectives on a hackathon project.

Project: {project_info.get('name', '')}
Description: {project_info.get('description', '')}
Work Done: {project_info.get('work_done', '')}

Based on {len(reviews_data)} reviews from different domain experts, the project received these scores:
{dimension_scores_text}

Domain-Specific Insights:
{domain_insights_text}

Please synthesize these perspectives into a comprehensive final review that:
1. Integrates insights from all domain perspectives
2. Highlights the project's key strengths across different evaluation dimensions
3. Identifies critical weaknesses or challenges noted by reviewers
4. Provides balanced, constructive feedback
5. Suggests concrete next steps for improvement
6. Concludes with an overall assessment of the project's potential

The review should be professional, balanced, and actionable. Length should be 400-500 words.
Focus on providing value to the project team by synthesizing the multi-perspective feedback into coherent guidance."""
        
        return prompt
    
    def generate_ontology_update_prompt(self, context: str) -> str:
        """
        Generate a prompt for suggesting ontology updates based on new project context.
        
        Args:
            context: Project description or other context
            
        Returns:
            Generated prompt string
        """
        # Get current ontology structure
        domains = self.ontology.get_domains()
        dimensions = self.ontology.get_impact_dimensions()
        project_types = self.ontology.get_project_types()
        
        # Format current structure
        current_domains = [f"- {d['name']}: {d['description']}" for d in domains]
        current_dimensions = [f"- {d['name']}: {d['description']}" for d in dimensions]
        current_types = [f"- {t['name']}: {t['description']}" for t in project_types]
        
        prompt = f"""You are an expert in hackathon organization and knowledge representation.

Current Ontology Structure:

Domains:
{chr(10).join(current_domains)}

Impact Dimensions:
{chr(10).join(current_dimensions)}

Project Types:
{chr(10).join(current_types)}

Based on the following new project context, suggest improvements or additions to the ontology:

Context:
{context}

Analyze if:
1. New domains are needed to properly categorize expertise
2. Additional impact dimensions would better evaluate projects
3. New project types have emerged
4. Existing definitions need refinement

Provide suggestions in this JSON format:
{{
  "domains_to_add": [
    {{
      "id": "suggested_id",
      "name": "Domain Name",
      "description": "Clear description of the domain",
      "keywords": ["keyword1", "keyword2"],
      "relevant_dimensions": ["dimension_id1", "dimension_id2"]
    }}
  ],
  "dimensions_to_add": [
    {{
      "id": "suggested_id",
      "name": "Dimension Name",
      "description": "What this dimension measures",
      "scale": {{
        "1": "Lowest score description",
        "2": "Low score description",
        "3": "Medium score description",
        "4": "High score description",
        "5": "Highest score description"
      }}
    }}
  ],
  "project_types_to_add": [
    {{
      "id": "suggested_id",
      "name": "Type Name",
      "description": "Type description",
      "keywords": ["keyword1", "keyword2"]
    }}
  ],
  "modifications": [
    {{
      "type": "domain|dimension|project_type",
      "id": "existing_id",
      "changes": {{
        "description": "New description if needed",
        "keywords_to_add": ["new_keyword"],
        "keywords_to_remove": ["old_keyword"]
      }}
    }}
  ]
}}

Only suggest additions or modifications that would meaningfully improve the ontology's coverage and precision."""
        
        return prompt
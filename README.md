# Ontology-Driven AI for Multi-Perspective Peer Review

This implementation provides a complete system for analyzing hackathon project reviews using an ontology-driven approach that leverages AI to generate multi-perspective feedback.

## Setup Instructions

1. Install required dependencies:
   ```
   pip install scikit-learn numpy requests
   ```

2. Set up the project directory structure as specified:
   ```
   projects/
       |- project-1/
           |- description.md
           |- human-review1.md
           |- human-review2.md
       |- project-2/
           |- description.md
           |- human-review3.md
           |- human-review4.md
           |- human-review5.md
   ```

3. Configure the system by updating the API keys in `config.py` if you want to use real LLM APIs:
   ```python
   # Update these with your actual API keys
   LLM_CONFIG = {
       "claude": {
           "api_key": "YOUR_ANTHROPIC_API_KEY",
           "model": "claude-3-opus-20240229"
       },
       "chatgpt": {
           "api_key": "YOUR_OPENAI_API_KEY",
           "model": "gpt-4-turbo"
       }
   }
   ```

## Running the System

1. Run the main script to process all projects:
   ```
   python main.py
   ```

2. Or process a specific project:
   ```
   python main.py --project project-1
   ```

3. Save output to a specific directory:
   ```
   python main.py --output results
   ```

4. Create a new ontology instead of using the existing one:
   ```
   python main.py --new-ontology
   ```

## System Features

1. **Ontology Generation:** Creates and maintains an ontology of domains, project types, impact dimensions, and expertise levels.

2. **Reviewer Classification:** Classifies reviewers by domain expertise and filters reviews based on relevance.

3. **Multi-Domain Analysis:** Groups reviews by domain to provide perspective-specific insights.

4. **Artificial Review Generation:** Creates additional reviews for missing critical domains.

5. **Feedback Aggregation:** Combines reviews across domains with appropriate weighting based on expertise.

6. **Final Report Generation:** Produces comprehensive feedback reports that highlight multi-perspective insights.

## Example Outputs

The system generates two main output files for each project:

1. `{project_id}_feedback.md` - A comprehensive feedback report with scores and insights.
2. `{project_id}_visualization.json` - Data for visualizing the feedback scores.

## Extending the System

To extend the system with additional features:

1. **Add New Domains:** Update the `_generate_domains` method in `ontology.py`
2. **Add New Evaluation Dimensions:** Update the `_generate_impact_dimensions` method in `ontology.py`
3. **Customize Visualizations:** Modify the visualization methods in `feedback.py`
4. **Integrate with External APIs:** Update the integration methods in `llm_interface.py`

## Notes

- The current implementation simulates LLM responses for demo purposes. Connect to actual APIs by uncommenting and updating the relevant code in `llm_interface.py`
- The system assumes all reviews follow the specified format
- For production use, add robust error handling and logging

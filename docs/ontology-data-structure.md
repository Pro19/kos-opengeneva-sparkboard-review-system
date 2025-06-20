# Ontology & Data Structure

## Ontology Design

Our ontology is structured around five core components based on W3C semantic web standards. However, these can be updated based on the hackathon review requirement:

**1. Domains (`hr:Domain`)**

- _Technical_: Programming, software engineering, hardware development
- _Clinical_: Medical/healthcare expertise, patient care, diagnosis
- _Administrative_: Healthcare administration, policy, management
- _Business_: Market analysis, commercialization, entrepreneurship
- _Design_: UI/UX design, visual design, interaction design
- _User Experience_: User research, accessibility, behavior analysis

**2. Expertise Levels (`hr:ExpertiseLevel`)**

Based on confidence scores (0-100):
- _Beginner (0-40)_: Basic understanding
- _Skilled (41-70)_: Practical experience
- _Talented (71-85)_: Deep understanding
- _Seasoned (86-95)_: Extensive experience
- _Expert (96-100)_: Top-level mastery

**3. Impact Dimensions (`hr:ImpactDimension`)**

- _Technical Feasibility_: Implementation difficulty with current technology
- _Innovation_: Novelty and uniqueness of approach
- _Impact_: Potential effect on target problem/domain
- _Implementation Complexity_: Practical deployment difficulty
- _Scalability_: Ability to scale to wider implementation
- _Return on Investment_: Expected benefits vs. costs

**4. Project Types (`hr:ProjectType`)**

Software, Hardware, Data, Process, Service

**5. Review Dimensions Mapping**

Each domain has relevant dimensions for focused evaluation:

- _Technical_: Technical Feasibility, Implementation Complexity, Scalability, Innovation
- _Clinical_: Impact, Implementation Complexity, Technical Feasibility
- _Business_: ROI, Scalability, Impact

## Data Schema

The system uses both file-based storage (for CLI) and SQLite database (for API):
```sql
-- Core entities
Projects: project_id, name, description, work_done, status, processing_status
Reviews: review_id, project_id, reviewer_name, text_review, confidence_score, domain, expertise_level
ProcessingJobs: job_id, project_id, status, progress, started_at, completed_at
FeedbackReports: report_id, project_id, feedback_scores, final_review, domain_insights

-- Ontology storage
RDF Triple Store: subject, predicate, object (managed by rdflib)
```

## RDF/TTL Structure Example
```turtle
@prefix hr: <http://example.org/hackathon-review/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# Domain definition
hr:clinical a hr:Domain ;
    hr:hasName "Clinical" ;
    hr:hasDescription "Medical or healthcare expertise related to patient care" ;
    hr:hasKeyword "medical", "healthcare", "clinical", "patient" ;
    hr:hasRelevantDimension hr:impact, hr:technical_feasibility .

# Impact dimension definition
hr:impact a hr:ImpactDimension ;
    hr:hasName "Impact" ;
    hr:hasDescription "Potential impact on the target problem or domain" ;
    hr:hasScaleValue "1, Minimal or no impact" ;
    hr:hasScaleValue "5, Transformative impact" .
```

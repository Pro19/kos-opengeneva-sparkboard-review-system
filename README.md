# OpenGeneva Sparkboard: Ontology-Driven AI for Multi-Perspective Peer Review in Hackathons

## Team Information

**Course:** D400006 – Knowledge Organization Systems, Université de Genève

**Team Members:**
- Eisha Tir Raazia
- Mahidhar Reddy Vaka
- Oussama Rattazi
- Pranshu Mishra

## Project Description

### Overview

The OpenGeneva Sparkboard is an innovative ontology-driven AI system designed to enhance the depth and utility of peer review systems in hackathon environments. Rather than relying on simplistic ranking scales, our approach leverages structured knowledge representation to capture both reviewer characteristics and feedback dimensions, enabling comprehensive multi-perspective analysis of hackathon projects.

### State-of-the-Art & Problem Statement

Traditional hackathon peer reviews suffer from several limitations:
- Lack of structure in review processes
- Poor expertise matching between reviewers and projects
- Insufficient perspective coverage across different domains
- Inconsistent evaluation criteria across reviewers

### Key Features

- **Ontological Knowledge Representation:** Structured classification of domains, expertise levels, and evaluation dimensions
- **Reviewer Expertise Profiling:** Automatic classification of reviewers based on confidence scores and review content
- **Domain Relevance Scoring:** Intelligent matching between reviewer expertise and project domains
- **Artificial Review Generation:** AI-generated reviews to fill gaps in domain coverage
- **Multi-dimensional Evaluation:** Comprehensive scoring across technical feasibility, innovation, impact, scalability, and ROI
- **Hybrid Human-AI Pipeline:** Combines human expertise with AI augmentation for comprehensive analysis

### Ontology & AI Methods Used

- **Knowledge Graph Structure:** RDF/TTL-based ontology defining domains, subdomains, expertise levels, and evaluation dimensions
- **Natural Language Processing:** LLM-based sentiment analysis and review classification
- **Machine Learning:** Domain classification and relevance scoring using text similarity measures
- **Multi-Provider LLM Integration:** Support for Claude, ChatGPT, Ollama, and Groq APIs
- **Confidence-Based Filtering:** Review acceptance based on expertise level and domain relevance thresholds

---

## Installation & Setup
### Prerequisites
### Dependencies
### Setup Instructions
#### Configure LLM Provider
#### Run the application (CLI Version):
#### Run the application (REST API Version):

---

## Ontology & Data Structure

### Ontology Design

Our ontology is structured around five core components:

1. **Domains (`hr:Domain`)**

- Technical: Programming, software engineering, hardware development
- Clinical: Medical/healthcare expertise, patient care, diagnosis
- Administrative: Healthcare administration, policy, management
- Business: Market analysis, commercialization, entrepreneurship
- Design: UI/UX design, visual design, interaction design
- User Experience: User research, accessibility, behavior analysis

2. **Expertise Levels (`hr:ExpertiseLevel`)**

Based on confidence scores (0-100):
- Beginner (0-40): Basic understanding
- Skilled (41-70): Practical experience
- Talented (71-85): Deep understanding
- Seasoned (86-95): Extensive experience
- Expert (96-100): Top-level mastery

3. **Impact Dimensions (`hr:ImpactDimension`)**

- Technical Feasibility: Implementation difficulty with current technology
- Innovation: Novelty and uniqueness of approach
- Impact: Potential effect on target problem/domain
- Implementation Complexity: Practical deployment difficulty
- Scalability: Ability to scale to wider implementation
- Return on Investment: Expected benefits vs. costs

4. **Project Types (`hr:ProjectType`)**

Software, Hardware, Data, Process, Service

5. **Review Dimensions Mapping**

Each domain has relevant dimensions for focused evaluation:

- Technical → Technical Feasibility, Implementation Complexity, Scalability, Innovation
- Clinical → Impact, Implementation Complexity, Technical Feasibility
- Business → ROI, Scalability, Impact
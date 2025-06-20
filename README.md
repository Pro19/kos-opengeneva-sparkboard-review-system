# OpenGeneva Sparkboard: Ontology-Driven AI for Multi-Perspective Peer Review in Hackathons

## Team Information

**Course:** D400006 – Knowledge Organization Systems, Université de Genève

**Team Members:**

- Eisha Tir Raazia - Eisha.Raazia@etu.unige.ch
- Mahidhar Reddy Vaka - Mahidhar.Vaka@etu.unige.ch
- Oussama Rattazi - Oussama.Rattazi@etu.unige.ch
- Pranshu Mishra - Pranshu.Mishra@etu.unige.ch

---

## Documentation

- [Project Description](#project-description)
    - [Key Features](#key-features)
    - [Screenshots](./docs/screenshots.md)
- [Ontology & Data Structure](./docs/ontology-data-structure.md)
- [Installation & Setup](./docs/installation-setup.md)
    - [Local](./docs/installation-setup.md#local-setup-instructions)
    - [Docker / Podman](./docs/installation-setup.md#docker--podman-setup-instructions)
- [Usage Instructions](./docs/usage-instructions.md)
    - [CLI](./docs/usage-instructions.md#cli-version) &nbsp;&nbsp;(_Local & containerized_)
    - [REST API](./docs/usage-instructions.md#rest-api-version) &nbsp;&nbsp;(_Local & containerized_)
    - [Desktop](./docs/usage-instructions.md#desktop-version) &nbsp;&nbsp;(_Local only_)
    - [Browser](./docs/usage-instructions.md#browser-version) &nbsp;&nbsp;(_Local & containerized_)
- [File Structure](./docs/file-structure.md)
- [Evaluation & Results](./docs/evaluation-results.md)
    - [Methodology](./docs/evaluation-results.md#methodology)
    - [Key Findings](./docs/evaluation-results.md#key-findings)
- [References & Acknowledgments](#references-and-acknowledgments)
    - [Future possibilities](#future-possibilities)
- _Developer Docs_
    - [API Definitions](./docs/dev/api_docs.md)
    - [Uninstall Ollama](./docs/dev/uninstall-ollama.md)

---

## Project Description

### Overview

This project is an innovative **RDF/TTL ontology-driven** AI system designed to enhance the depth and utility of peer review systems in hackathon environments. Rather than relying on simplistic ranking scales, our approach leverages structured knowledge representation to capture both reviewer characteristics and feedback dimensions, enabling comprehensive multi-perspective analysis of hackathon projects.


### State-of-the-Art & Problem Statement

Traditional hackathon peer reviews suffer from several limitations:

- **Static review frameworks** that cannot adapt to new domains or evaluation criteria
- **Poor expertise matching** between reviewers and projects
- **Insufficient perspective coverage** across different stakeholder domains
- **Inconsistent evaluation criteria** that vary between reviewers and events
- **Lack of semantic understanding** of domain relationships and expertise levels

### Our Approach: Dynamic RDF Ontology Based Review System

Our solution transforms static review systems into **adaptive, knowledge-driven platforms** that:

- **Generate prompts dynamically** from RDF ontology definitions
- **Adapt behavior in real-time** based on ontological knowledge updates
- **Understand semantic relationships** between domains and evaluation dimensions
- **Scale automatically** to new domains without code modifications

### Ontology & AI Methods Used

- **RDF/TTL Semantic Web:** Knowledge representation using W3C standards
- **SPARQL Query Engine:** Dynamic knowledge extraction from triple store
- **Natural Language Processing:** LLM-based sentiment analysis and classification
- **Graph-Based Reasoning:** Domain relevance scoring using semantic relationships
- **Multi-Provider LLM Integration:** Support for Claude, ChatGPT, Ollama, and Groq
- **Confidence-Based Filtering:** Review acceptance based on expertise and relevance

### Key Features

#### **🧠 RDF Ontology-Driven Intelligence**

- **Dynamic Knowledge Representation:** RDF/TTL ontology with semantic relationships
- **Runtime Ontology Management:** Add domains/dimensions without code changes
- **Semantic Relationship Modeling:** Explicit domain-dimension associations

#### **🔄 Dynamic AI Prompt Generation**

- **Context-Aware Prompts:** Generated from ontological domain definitions
- **Adaptive Review Criteria:** Evaluation dimensions loaded dynamically from ontology
- **Semantic Personalization:** Prompts include relevant keywords and relationships
- **Multi-Domain Coverage:** Automatic prompt generation for missing expertise areas

#### **👥 Intelligent Reviewer Profiling**

- **Semantic Classification:** Domain assignment using ontological definitions
- **Expertise Level Mapping:** Confidence-based expertise determination
- **Relevance Scoring:** Semantic matching between reviewer expertise and projects
- ~~**External Profile Integration:** LinkedIn, GitHub, Google Scholar analysis~~

#### **📊 Multi-Dimensional Evaluation Framework**

- **Dynamic Scoring Dimensions:** Loaded from RDF ontology definitions
- **Weighted Domain Analysis:** Scoring based on domain-dimension relevance
- **Comprehensive Impact Assessment:** Technical, clinical, business, and design perspectives
- **Adaptive Scale Definitions:** Evaluation criteria defined semantically in ontology

#### **🤖 Hybrid Human-AI Pipeline**

- **Intelligent Review Augmentation:** AI fills gaps in domain coverage
- **Quality-Based Filtering:** Confidence and relevance threshold management
- **Multi-Perspective Synthesis:** Combines human expertise with AI-generated insights
- **Contextual Recommendation Engine:** Actionable suggestions based on ontological analysis

## References and Acknowledgments

### References

- Course contents shared during the class
- Documentations of various toolings like `rdflib` and `fastapi`
- W3C RDF Working Group. (2014). RDF 1.1 concepts and abstract syntax. W3C Recommendation. https://www.w3.org/TR/rdf11-concepts/
- W3C SPARQL Working Group. (2013). SPARQL 1.1 query language. W3C Recommendation. https://www.w3.org/TR/sparql11-query/

### Acknowledgments

Special thanks to:

- Professor and TA of D400006 for guidance
  - Thomas Maillart - Thomas.Maillart@unige.ch
  - Thibaut Chataing - Thibaut.Chataing@unige.ch
- Maintainer of OpenGeneva Sparkboard hackathon platform
  - Matthew Hubert - matt@opengeneva.org
- Our team members

### Future Possibilities

- Import External Ontologies: Load domain-specific ontologies from research
- Reasoning: Add RDFS/OWL reasoning for inferred relationships
- Linked Data: Connect to external knowledge graphs
- Multi-Language Support: Internationalize domain/dimension descriptions
- Advanced Querying: Complex SPARQL queries for deep analysis

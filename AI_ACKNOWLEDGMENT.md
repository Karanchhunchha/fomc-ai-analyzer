# Generative AI Usage Acknowledgment

This document details the use of Generative AI tools in the development of the **FOMC AI Analyzer** project, submitted for the **MathWorks Excellence in AI Challenge (Project #258)**, in accordance with the *Guidelines for Students Using Generative AI in Challenge Projects*.

## 🛠️ Tools Utilized
- **Google Gemini** (via Antigravity / Claude Agent environment): Assisted in code structure, debugging pipeline exceptions, and design advice.
- **Claude 3.5 Sonnet / Gemini 1.5 Pro**: Used for structural code layout, prompt optimization, and designing the hybrid architecture presentation.

## 📝 How AI Was Utilized
1. **Code Architecture & Refactoring**: Assisted in framing modern FastAPI asynchronous route handler structures, SSE (Server-Sent Events) syntax, and setting up the CORS middleware constraints.
2. **RAG Prompt Optimization**: Guided the design of prompt templates in `backend/rag_pipeline.py` to classify query intents and restrict responses strictly to the ground-truth context with 429 backoff rate-limit handling.
3. **Database Integration**: Provided templates for standard SQLite schemas to track sessions and response caches.
4. **MATLAB Hybrid Design**: Assisted in outlining how the MATLAB Database, Text Analytics, and Deep Learning toolbox functions correspond directly with Python microservice workflows.

## 🧑‍💻 Student Ownership, Custom Logic, & Verification
All code, scripts, and structures in this submission have been carefully reviewed, verified, and debugged to ensure correctness:
- **Custom Parsing & Page-Aware Chunking**: I designed the custom PyMuPDF extraction layout logic to capture exact page indices (`page_number`) and dates in Python, which does not exist in standard template libraries.
- **Evidence Retrieval & Reranking**: The specific hybrid reranking integration (vector distance combined with CrossEncoder logits normalized via Sigmoid) was customized to provide reliable citation targets.
- **Validation Execution**: The local validation datasets in Python and verification structures in MATLAB were tested and verified against real FOMC document inputs.
- **Toolbox Alignment**: Checked all MATLAB scripts against official MathWorks documentation to ensure use of native features (e.g., `tokenizedDocument`, `removeWords`, `extractFileText`).

*The final system implementation, correctness, and evaluation are fully owned and verified by the student.*

# MATLAB Financial Analytics Layer

This folder contains the MATLAB implementation scripts for the **MathWorks Excellence in AI Challenge (Project #258)**: *Federal Open Market Committee Minutes Analysis with Large Language Models*.

These scripts implement a **hybrid quantitative research workflow** where MATLAB is utilized for financial text analytics, downloading, local index search, tone scoring, and validation, while a high-concurrency Python backend (FastAPI) serves as the model hosting and vector routing layer.

---

## 🛠️ MATLAB Toolbox Requirements
To run these scripts, you need:
1. **Text Analytics Toolbox™** (for tokenization, stop word filtering, and text preprocessing)
2. **Statistics and Machine Learning Toolbox™** (for sentiment gauge plots, evaluation dashboard charting)
3. **Database Toolbox™** (conceptual data retrieval)
4. **Deep Learning Toolbox™** (conceptual local embeddings)

---

## 📂 Script Inventory & Workflows

### 1. 📥 `fomc_downloader.m`
- **Purpose**: Programmatically downloads real FOMC meeting minutes PDFs from the Board of Governors of the Federal Reserve System.
- **Workflow**: Fetches landing page → parses hyperlinks via regular expressions → saves PDFs directly into `data/raw/` directory.

### 2. 📝 `ingest_documents.m`
- **Purpose**: Document processing and cleaning.
- **Workflow**: Reads PDFs → tokenizes raw text → applies case-folding → filters stop words using `removeWords`.

### 3. 🦅 `fomc_sentiment_analysis.m`
- **Purpose**: Classifies meeting transcripts as **Hawkish** (restrictive, tightening policy) vs. **Dovish** (easing, supportive policy).
- **Workflow**: Matches tokens against domain-specific financial dictionaries → computes the Hawk-Dove Index → plots a live sentiment dial/gauge representation.

### 4. 🔀 `fomc_rag_pipeline.m`
- **Purpose**: Standalone RAG execution in MATLAB.
- **Workflow**: Tokenizes document → performs a local keyword search (cosine similarity on TF-IDF bag-of-words matrix) to retrieve evidence → constructs context-aware LLM prompt → fetches response via direct REST API connection to Gemini API.

### 5. 🔍 `fomc_retrieval.m`
- **Purpose**: Interacts with the local/live FastAPI Python backend.
- **Workflow**: Sends REST payloads to `/query` endpoints and displays the streaming/synthesis results in MATLAB console.

### 6. 📊 `fomc_validation.m`
- **Purpose**: Evaluates RAG accuracy and precision.
- **Workflow**: Queries test questions against the pipeline → calculates semantic theme coverage → displays a validation dashboard with pass/fail metrics.

---

## 🚀 Quick Start
1. Ensure the Python FastAPI backend is running (`uvicorn backend.api:app --port 8000`).
2. Run `fomc_downloader` to grab the latest PDFs.
3. Run `fomc_sentiment_analysis` to check monetary policy tone.
4. Run `fomc_rag_pipeline` to test local MATLAB QA retrieval.
5. Run `fomc_validation` to check pipeline accuracy metrics.

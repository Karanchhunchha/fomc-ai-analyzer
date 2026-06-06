# Project Roadmap & Memory

## Project Vision
**FOMC AI Analyzer** is evolving into an AI-native Financial Intelligence Operating System. It is designed to act as a specialized, grounded financial research assistant for analyzing Federal Reserve actions, inflation narratives, and policy evolutions.

## Core Execution Rule
**Small, incremental steps only.** No massive rewrites. Preserve stability, test everything, and ensure every feature solves a real analyst problem.

## Execution Phases

### Phase 1: Verified RAG
**Goal:** Build a stable, trustworthy, grounded financial RAG system.
- [x] Stable document upload flow
- [x] Grounded retrieval with accurate answers
- [x] Source citations
- [x] Evaluation framework
- [x] Multi-document retrieval
- [x] Financial insight extraction

### Phase 2: Auto Ingestion
**Goal:** Automate the collection of Fed data.
- [x] Federal Reserve auto-downloader (minutes, statements)
- [x] RSS ingestion for news
- [x] Document scheduling pipeline
- [x] Basic metadata extraction (Date, Speaker)

### Phase 3: Structured Financial Memory
**Goal:** Build "Mike Ross" memory with deep tagging.
- [x] Metadata indexing in SQLite/ChromaDB hybrid
- [x] Topic tagging and classification
- [x] Hawkish/Dovish scoring algorithms
- [x] Temporal document relationships (linking past meetings)

### Phase 4: Frontend UI & Multi-Document Intelligence
**Goal:** Integrate the RAG core and Structured Financial Memory into the Next.js UI dashboard.
- [x] Connect the frontend UI dashboard to the `backend/api.py` endpoints
- [x] Implement sentiment (Hawkish/Dovish) timeline visualization in the UI
- [x] Implement topic tags filters on the dashboard for document exploration
- [x] Enable cross-year policy comparisons and narrative tracking in UI

### Phase 5: Multi-Agent Intelligence
**Goal:** "Harvey Specter" execution layer.
- [x] Introduce orchestration (LangGraph/CrewAI)
- [x] FOMC Agent
- [x] Speech Agent
- [x] News Agent
- [x] Market Correlation Agent

## API Priority Stack
1. **LLM Core:** Gemini API, OpenRouter
2. **Hosting:** Render (Backend), Vercel (Frontend)
3. **Embeddings:** Hugging Face (Sentence Transformers)
4. **Future expansions:** Pinecone, Whisper API, Search APIs

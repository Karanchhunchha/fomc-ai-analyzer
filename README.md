# FOMC AI Analyzer 🏛️

**Federal Open Market Committee Minutes Analysis with Large Language Models**

An AI-native financial intelligence platform that uses large language models to extract insights from central bank policy documents. Built as a full-stack RAG (Retrieval-Augmented Generation) system with real-time streaming, semantic search, and interactive policy stance visualization.

> **Impact:** Harness AI to revolutionize financial text analysis and unlock deeper insights from real-world monetary policy documents.

> **Expertise gained:** Artificial Intelligence, Computational Finance, Natural Language Processing, Text Analytics, Neural Networks

---

## 🎯 Motivation

Understanding central bank communication is a competitive edge in today's data-driven financial industry. The Federal Open Market Committee (FOMC) plays a pivotal role in shaping U.S. monetary policy, and its meeting minutes offer valuable insights into interest rate decisions, inflation expectations, and the broader economic outlook. These documents are essential reading for economists, traders, portfolio managers, and policy analysts.

This project automates the analysis pipeline — from downloading raw FOMC documents to chunking, embedding, indexing, and querying them with grounded LLM responses complete with source citations and confidence scoring.

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Frontend["Next.js Frontend (Port 3000)"]
        UI["Dashboard UI"]
        Proxy["API Proxy Route"]
    end

    subgraph Backend["FastAPI Backend (Port 8000)"]
        API["REST API + SSE Streaming"]
        RAG["RAG Pipeline"]
        Embed["Sentence Transformers"]
        Gemini["Gemini 2.5 Flash"]
        OR["OpenRouter Llama (Fallback)"]
    end

    subgraph Storage["Storage Layer"]
        Chroma["ChromaDB Vector Store"]
        PG["PostgreSQL Database"]
    end

    subgraph Data["Data Layer"]
        FOMC["FOMC Minutes (PDF/TXT)"]
        Ingest["Ingestion Worker"]
    end

    UI --> Proxy
    Proxy --> API
    API --> RAG
    RAG --> Embed
    RAG --> Gemini
    RAG --> OR
    Embed --> Chroma
    API --> PG
    FOMC --> Ingest
    Ingest --> Embed
    Ingest --> PG
```

---

## ✨ Features

### Core RAG Pipeline
- **Semantic Search** — Query FOMC documents using natural language with cosine similarity ranking
- **Hybrid Search** — Combines vector search with BM25 keyword matching for better retrieval accuracy
- **Query Rewriting** — Maps conversational queries to formal FOMC terminology for improved relevance
- **Grounded Answers** — LLM responses are strictly constrained to retrieved context with `[Excerpt N]` citations
- **SSE Streaming** — Real-time token-by-token response streaming via Server-Sent Events
- **Multi-Model Fallback** — Gemini 2.5 Flash primary, OpenRouter Llama 3.3 70B fallback with automatic retry + exponential backoff
- **Confidence Scoring** — HIGH/MEDIUM/LOW confidence labels based on similarity threshold analysis
- **Response Caching** — SHA256-hashed query cache to avoid redundant LLM calls

### Document Processing
- **PDF & TXT Upload** — Drag-and-drop document ingestion with MIME validation and size limits (15MB)
- **Page-Aware Chunking** — Intelligent text splitting with section detection and semantic summaries
- **Meeting Date Extraction** — Automatic date parsing from document content
- **Hawkish/Dovish Scoring** — Financial sentiment analysis using keyword-based and LLM-based scoring (-1.0 to +1.0 scale)
- **Topic Classification** — Automatic topic tagging (Inflation, Employment, Interest Rates, etc.)

### Auto-Ingestion Pipeline
- **Federal Reserve RSS Feed** — Automated download of new FOMC minutes, statements, and press releases
- **Deduplication** — MD5 checksum-based duplicate detection to prevent re-processing
- **Background Scheduling** — APScheduler-based periodic ingestion worker

### Interactive Dashboard (Next.js)
- **Workspace** — Main query interface with conversation history and evidence panel
- **Documents** — Document index manager with upload, delete, and metadata inspection
- **Insights** — Macroeconomic analysis pivots (Inflation, Labor, Interest Rates, Global Trade)
- **Compare** — Side-by-side policy comparison across FOMC meetings
- **Sessions** — Chat history management with persistent conversation threads
- **Sentiment Timeline** — Chronological Hawkish/Dovish stance drift visualization

### Multi-Agent Intelligence System
- **Agent Orchestration** — Centralized routing system for specialized financial analysis agents
- **FOMC Agent** — Specialized document analysis with policy stance tracking and cross-meeting comparison
- **Speech Agent** — Federal Reserve speech and testimony analysis with forward guidance extraction
- **News Agent** — Federal Reserve news, press releases, and events analysis
- **Market Agent** — Financial market correlation analysis and policy impact assessment

### Security & Production Features
- **API Key Authentication** — Header-based `X-API-Key` verification
- **Rate Limiting** — SlowAPI-powered request throttling (100/min general, 10/min queries, 5/min uploads)
- **Input Sanitization** — HTML stripping, null byte removal, filename path traversal prevention
- **CORS Configuration** — Configurable allowed origins for cross-origin requests
- **Request Logging** — Structured loguru logging with daily rotation and unique request IDs

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| **Backend** | FastAPI, Python 3.11+, Uvicorn |
| **LLM** | Google Gemini 2.5 Flash, OpenRouter (Llama 3.3 70B) |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Vector DB** | ChromaDB |
| **Database** | PostgreSQL 18 (SQLite fallback) |
| **PDF Processing** | PyMuPDF (fitz) |
| **Logging** | Loguru with structured JSON output |
| **Security** | SlowAPI rate limiting, python-magic MIME detection |

---

## 📂 Project Structure

```
fomc-ai-analyzer/
├── backend/
│   ├── api.py                  # FastAPI app with all REST endpoints
│   ├── rag_pipeline.py         # Core RAG pipeline with SSE streaming
│   ├── semantic_search.py      # ChromaDB semantic search with hybrid BM25
│   ├── embeddings.py           # Sentence Transformer embedding generation
│   ├── vector_store.py         # ChromaDB collection management
│   ├── database.py             # PostgreSQL/SQLite dual-engine database layer
│   ├── document_processor.py   # PDF/TXT page-aware chunking
│   ├── financial_analyzer.py   # Hawkish/Dovish sentiment scoring
│   ├── query_rewriter.py       # Query rewriting for formal terminology
│   ├── bm25_search.py          # BM25 keyword search for hybrid retrieval
│   ├── agent_orchestrator.py   # Multi-agent orchestration framework
│   ├── fomc_agent.py           # FOMC document analysis agent
│   ├── speech_agent.py         # Fed speech analysis agent
│   ├── news_agent.py           # Federal Reserve news analysis agent
│   ├── market_agent.py         # Market correlation analysis agent
│   ├── init_agents.py          # Agent initialization script
│   ├── ingestion_worker.py     # Auto-ingestion from Federal Reserve RSS
│   ├── config.py               # Centralized configuration + Loguru setup
│   ├── auth.py                 # API key authentication
│   └── dependencies.py         # FastAPI dependency injection
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── workspace/      # Main RAG query interface
│   │   │   ├── documents/      # Document index manager
│   │   │   ├── insights/       # Macroeconomic analysis pivots
│   │   │   ├── compare/        # Cross-meeting policy comparison
│   │   │   ├── sessions/       # Chat history manager
│   │   │   └── api/            # Backend proxy routes
│   │   ├── components/         # Reusable UI components
│   │   └── lib/                # API client + utilities
│   └── package.json
├── data/
│   ├── raw/                    # Downloaded FOMC documents
│   └── chroma_db/              # ChromaDB persistent storage
├── evaluation/                 # RAG evaluation framework with LLM-as-a-judge
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render.com deployment config
└── .env.example                # Environment variable template
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 14+** (or use SQLite fallback)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/fomc-ai-analyzer.git
cd fomc-ai-analyzer

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here  # Optional fallback
DATABASE_TYPE=postgres                             # Or 'sqlite'
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
```

### 3. Start PostgreSQL

```bash
# Windows
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\18\data" start

# Linux/macOS
sudo systemctl start postgresql
```

Tables are auto-created on first backend startup.

### 4. Start Backend Server

```bash
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Check health: `GET /health`

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/health` | System health check with uptime and stats | ❌ |
| `POST` | `/upload` | Upload PDF/TXT document for ingestion | ✅ |
| `POST` | `/query` | Query documents with SSE streaming response | ✅ |
| `GET` | `/documents` | List all indexed documents with metadata | ❌ |
| `DELETE` | `/documents/{id}` | Delete document and its vectors | ✅ |
| `GET` | `/sentiment-timeline` | Hawkish/Dovish scores over time | ❌ |
| `GET` | `/sessions` | List all chat sessions | ❌ |
| `POST` | `/sessions` | Create a new chat session | ✅ |
| `GET` | `/sessions/{id}/history` | Get chat history for a session | ❌ |
| `DELETE` | `/sessions/{id}` | Delete a chat session | ✅ |
| `POST` | `/summarize` | Summarize a specific FOMC document | ❌ |

### Example Query (SSE Streaming)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key" \
  -d '{"query": "What was the inflation outlook at the January 2026 meeting?", "top_k": 5}'
```

---

## 🔬 RAG Pipeline Flow

1. **Query Classification** → Automatically detects query intent (Research, Summary, Compare, Study, Resume)
2. **Query Rewriting** → Maps conversational queries to formal FOMC terminology for improved relevance
3. **Hybrid Retrieval** → Combines vector search with BM25 keyword matching for better accuracy
4. **Cross-Encoder Reranking** → Re-ranks results using MS-MARCO Cross-Encoder for precision
5. **Confidence Check** → Validates similarity scores against configurable threshold (default: 0.20)
6. **Cache Lookup** → Checks SHA256-hashed query cache before LLM call
7. **Prompt Construction** → Builds mode-specific grounded prompt with metadata-enriched context
8. **LLM Generation** → Streams response via Gemini with OpenRouter fallback + exponential backoff
9. **Response Caching** → Stores successful responses for future cache hits
10. **Session Logging** → Persists conversation to PostgreSQL for session continuity

---

## 📊 Query Modes

| Mode | Trigger Keywords | Behavior |
|------|-----------------|----------|
| **Research** | Default | Analytical financial research with policy stance analysis |
| **Summary** | "summarize", "overview", "tldr" | Executive summary with key takeaways |
| **Compare** | "compare", "contrast", "versus" | Side-by-side comparative analysis |
| **Study** | "explain", "what is", "how to" | Educational breakdown with definitions |
| **Resume** | "resume", "candidate", "skills" | Technical talent assessment (for uploaded CVs) |

---

## 🧪 Evaluation

The project includes a comprehensive RAG evaluation framework in `evaluation/` for measuring:
- **Retrieval Accuracy** — Are the right chunks being retrieved?
- **Answer Grounding** — Is the LLM staying within the provided context?
- **Citation Quality** — Are excerpt references accurate?
- **LLM-as-a-Judge** — Uses Gemini to evaluate Faithfulness, Answer Relevancy, Context Precision, and Context Recall


---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **MathWorks** — MATLAB Simulink Challenge Project Hub inspiration
- **Federal Reserve** — Public FOMC meeting minutes and statements
- **Google DeepMind** — Gemini API for LLM generation
- **Hugging Face** — Sentence Transformers for embedding models
- **ChromaDB** — Open-source vector database

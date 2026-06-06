# FOMC AI Analyzer 🏛️

<div align="center">

**AI-native financial intelligence platform for Federal Reserve policy analysis**

[![MathWorks Challenge](https://img.shields.io/badge/MathWorks-Challenge%20%23258-E2231A?style=flat-square&logo=mathworks)](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=nextdotjs)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)

[**Challenge Page**](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models)

</div>

---

## What This Is

A production-deployed RAG (Retrieval-Augmented Generation) terminal that ingests Federal Open Market Committee meeting minutes and answers natural language questions about monetary policy — with source citations, confidence scoring, and real-time policy stance visualization.

Built for the **MathWorks Excellence in AI Challenge #258** by [Karan Chhunchha](mailto:karanchhunchha@gmail.com).

```
Upload FOMC Minutes PDF
        ↓
Page-aware chunking + embedding
        ↓
Hybrid vector + BM25 search
        ↓
CrossEncoder reranking
        ↓
Gemini 2.5 Flash synthesis (streamed)
        ↓
Grounded answer with [Excerpt N] citations + CONFIDENCE: HIGH/MEDIUM/LOW
```

---

## Architecture

```mermaid
flowchart LR
  subgraph "Frontend — Vercel"
    UI["Next.js Workspace"]
    UP["Upload PDF/TXT"]
    QI["Query Input"]
    CR["Citation Cards"]
    ST["Hawk-Dove Timeline"]
  end

  subgraph "Auth & Rate Limiting"
    AK["X-API-Key Check"]
    RL["slowapi 10/min"]
  end

  subgraph "FastAPI Backend — Render"
    EP1["/upload"]
    EP2["/query SSE Stream"]
    EP3["/sentiment-timeline"]
    EP4["/health"]
  end

  subgraph "RAG Pipeline"
    CHK["PyMuPDF Chunker"]
    EMB["SentenceTransformer"]
    VEC["ChromaDB + BM25"]
    RR["CrossEncoder Reranker"]
    CAC["SQLite Cache"]
    GEM["Gemini 2.5 Flash"]
    OR["OpenRouter Fallback"]
  end

  subgraph "Render Disk /var/data"
    CD[("ChromaDB")]
    SQ[("SQLite")]
  end

  UP --> AK --> EP1 --> CHK --> EMB --> CD
  QI --> AK --> RL --> EP2 --> VEC --> RR --> CAC
  CAC -- "hit <5ms" --> UI
  CAC -- "miss" --> GEM
  GEM -- "429" --> OR
  GEM --> UI
  EP3 --> ST
  EP4 --> UI
```

---

## Features

### RAG Pipeline
| Feature | Implementation |
|---|---|
| Semantic search | `all-MiniLM-L6-v2` embeddings → ChromaDB cosine similarity |
| Keyword search | BM25 (`rank_bm25`) for term-frequency matching |
| Hybrid retrieval | Vector + BM25 score fusion for better coverage |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` — non-blocking via `ThreadPoolExecutor` |
| Query rewriting | Maps conversational queries to formal FOMC terminology |
| Response caching | SHA256 query hash → SQLite cache (<5ms repeat queries) |
| Streaming | Server-Sent Events (SSE) — token-by-token via `StreamingResponse` |
| Fallback | Gemini 429 → exponential backoff → OpenRouter Llama 3.3 70B |
| Grounding | System prompt enforces context-only answers + `⚠️ LIMITED EVIDENCE` prefix |
| Confidence | `HIGH` (3+ strong excerpts) / `MEDIUM` (1-2) / `LOW` (sparse) |

### Document Processing
- **PDF + TXT** upload with MIME detection (`python-magic`) and 15MB size limit
- **Page-aware chunking** — preserves page numbers in chunk metadata
- **Meeting date extraction** — auto-parsed from document content
- **Hawkish/Dovish scoring** — keyword frequency model (-1.0 to +1.0 scale)
- **Topic classification** — auto-tags chunks (Inflation, Employment, Interest Rates, etc.)
- **Auto-ingestion** — APScheduler polls Federal Reserve RSS for new minutes

### Multi-Agent Intelligence
Four specialized agents routed by an orchestrator:
- **FOMC Agent** — policy stance tracking, cross-meeting comparison
- **Speech Agent** — Fed speech and testimony analysis, forward guidance extraction
- **News Agent** — press releases and Federal Reserve news analysis
- **Market Agent** — financial market correlation and policy impact assessment

### Production Engineering
| Area | What's in place |
|---|---|
| Auth | `X-API-Key` header verification via FastAPI dependency |
| Rate limiting | `slowapi` — 10/min queries, 5/min uploads, 100/min general |
| CORS | Env var whitelist — no `allow_origins=["*"]` |
| Input validation | HTML strip, null byte removal, 2000 char limit, MIME check |
| Persistence | ChromaDB + SQLite on Render Disk `/var/data` — survives restarts |
| Timeouts | 25s Gemini timeout via `ThreadPoolExecutor.result(timeout=25)` + 30s frontend `AbortController` |
| Logging | `loguru` structured logs with `X-Request-ID` per request, daily rotation |
| Health check | `GET /health` — indexed doc count, cache entries, uptime, model |

---

## Evaluation Results

Tested on 10 FOMC-specific Q&A pairs using LLM-as-a-judge evaluation (`evaluation/ragas_eval.py`):

| Metric | Score |
|---|---|
| Retrieval Precision @5 | **0.695** |
| Answer Faithfulness | **0.860** |
| Answer Relevancy | **0.860** |
| Context Recall | **0.860** |

> Run your own evaluation: `python evaluation/ragas_eval.py`

---

## MATLAB Analytics Layer

Eight MATLAB scripts demonstrating the MathWorks challenge toolboxes:

| Script | Toolbox | What it does |
|---|---|---|
| `ingest_documents.m` | Text Analytics Toolbox™ | Tokenization, stop word removal, case folding |
| `fomc_sentiment_analysis.m` | Statistics & ML Toolbox™ | Hawk-Dove Index calculation, policy gauge visualization |
| `fomc_rag_pipeline.m` | Deep Learning Toolbox™ | TF-IDF cosine similarity search, LLM REST integration |
| `fomc_retrieval.m` | Text Analytics Toolbox™ | Semantic retrieval demonstration |
| `fomc_validation.m` | Statistics Toolbox™ | Pipeline validation with pass/fail metric charts |
| `fomc_database.m` | Database Toolbox™ | Document storage and retrieval simulation |
| `fomc_downloader.m` | — | Federal Reserve document download automation |
| `matlab/README.md` | — | Setup guide and toolbox requirements |

> **Architecture note:** MATLAB operates as a standalone analytics validation and visualization layer demonstrating Challenge #258 toolbox requirements. The production API is Python-native for cloud deployment portability. No MATLAB runtime is required to run the live system.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| LLM | Gemini 2.5 Flash (primary), OpenRouter Llama 3.3 70B (fallback) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local) |
| Vector DB | ChromaDB (persistent) |
| Database | SQLite (default) / PostgreSQL (optional) |
| PDF | PyMuPDF (`fitz`) |
| Security | SlowAPI, python-magic, loguru |

---

## Project Structure

```
fomc-ai-analyzer/
├── backend/
│   ├── api.py                  # FastAPI app — all endpoints
│   ├── rag_pipeline.py         # Core RAG with SSE streaming
│   ├── semantic_search.py      # ChromaDB + BM25 hybrid search
│   ├── embeddings.py           # Sentence Transformer (singleton)
│   ├── vector_store.py         # ChromaDB collection management
│   ├── database.py             # SQLite / PostgreSQL dual engine
│   ├── document_processor.py   # Page-aware PDF/TXT chunking
│   ├── financial_analyzer.py   # Hawk/Dove sentiment scoring
│   ├── query_rewriter.py       # Formal terminology mapping
│   ├── bm25_search.py          # BM25 keyword search
│   ├── agent_orchestrator.py   # Multi-agent routing
│   ├── fomc_agent.py           # FOMC document analysis agent
│   ├── speech_agent.py         # Fed speech analysis agent
│   ├── news_agent.py           # Federal Reserve news agent
│   ├── market_agent.py         # Market correlation agent
│   ├── ingestion_worker.py     # Auto-ingestion from Fed RSS
│   ├── config.py               # Config + loguru setup
│   ├── auth.py                 # X-API-Key dependency
│   └── dependencies.py         # FastAPI lru_cache singletons
├── frontend/
│   ├── src/app/
│   │   ├── workspace/          # Main query interface
│   │   ├── documents/          # Document manager
│   │   ├── insights/           # Macroeconomic analysis pivots
│   │   ├── compare/            # Cross-meeting comparison
│   │   ├── sessions/           # Chat history
│   │   └── api/                # Secure Next.js backend proxy
│   └── src/components/         # Topbar, Sidebar, ResponseCard, SentimentTimeline
├── matlab/                     # 8 MATLAB analytics scripts
├── data/raw/sample/            # Sample FOMC document for testing
├── evaluation/
│   └── ragas_eval.py           # LLM-as-a-judge evaluation runner
├── render.yaml                 # Render deployment with Disk config
└── .env.example                # All required environment variables
```

---

## API Reference

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/health` | 🌐 Public | System status — doc count, cache, uptime, model |
| `POST` | `/upload` | 🔒 Auth | Upload PDF/TXT — MIME validation, 15MB limit |
| `POST` | `/query` | 🔒 Auth | SSE streaming query with citations |
| `GET` | `/documents` | 🌐 Public | List all indexed documents |
| `DELETE` | `/documents/{id}` | 🔒 Auth | Delete document + vectors |
| `GET` | `/sentiment-timeline` | 🌐 Public | Hawk/Dove scores over time |
| `POST` | `/sessions` | 🔒 Auth | Create chat session |
| `GET` | `/sessions/{id}/history` | 🌐 Public | Get session history |
| `DELETE` | `/sessions/{id}` | 🔒 Auth | Delete session |

**Example query:**
```bash
curl -X POST https://fomc-ai-analyzer-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key" \
  -d '{"query": "What was the inflation outlook at the January 2026 meeting?", "top_k": 5}'
```

---

## Getting Started (Local)

### 1 — Clone & backend setup

```bash
git clone https://github.com/Karanchhunchha/fomc-ai-analyzer.git
cd fomc-ai-analyzer

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### 2 — Configure environment

```bash
cp .env.example .env
```

Minimum required in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get a free Gemini key at: https://aistudio.google.com/apikey

> SQLite is the default — no PostgreSQL setup needed.

### 3 — Start backend

```bash
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

Verify: `GET http://localhost:8000/health`

### 4 — Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

### 5 — Test it

1. Upload `data/raw/sample/fomc_jan_2026_sample.txt`
2. Ask: *"What was the rate decision in January 2026?"*
3. You should see a grounded answer with `[Excerpt N]` citations and `CONFIDENCE: HIGH`

---

## Deployment

### Render (Backend)

1. Connect GitHub repo → New Web Service
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn backend.api:app --host 0.0.0.0 --port $PORT --workers 2`
4. Health check path: `/health`
5. Add **Disk**: mount path `/var/data`, size 1GB
6. Environment variables:

```env
GEMINI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
INTERNAL_API_KEY=generate_with_python_uuid4
ALLOWED_ORIGINS=https://your-vercel-url.vercel.app
CHROMA_PERSIST_PATH=/var/data/chroma_db
SQLITE_DB_PATH=/var/data/ck_workspace.db
GEMINI_MODEL=gemini-2.5-flash
MIN_SIMILARITY_THRESHOLD=0.20
TOP_K_RETRIEVAL=5
```

> ⚠️ The Render Disk is required. Without it, ChromaDB resets on every restart.

### Vercel (Frontend)

1. Import repo → set root directory to `frontend/`
2. Environment variables:

```env
API_BASE_URL=https://your-render-url.onrender.com
INTERNAL_API_KEY=same_key_as_backend
```

---

## Live Test Queries

After deploying or running locally with the sample document:

```
Q: "What was the federal funds rate decision in January 2026?"
A: Maintained at 3½–3¾% — unanimous vote [Excerpt 1]

Q: "What were the main inflation concerns discussed?"
A: Core PCE at 2.8%, shelter costs elevated, tariff effects on goods [Excerpt 2]

Q: "What did participants say about the labor market?"
A: Unemployment stable, low layoffs but low hiring [Excerpt 3]

Q: "Who voted against maintaining rates?"
A: Almost all supported holding — couple preferred to lower [Excerpt 4]
```

---

## MathWorks Challenge Submission

- **Challenge**: [Federal Open Market Committee Minutes Analysis with LLMs — Project #258](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models)
- **Submitted by**: Karan Chhunchha ([karanchhunchha@gmail.com](mailto:karanchhunchha@gmail.com))
- **AI usage**: Documented in [AI_ACKNOWLEDGMENT.md](AI_ACKNOWLEDGMENT.md)
- **License**: [MIT](LICENSE)

---

## Acknowledgments

- [MathWorks](https://www.mathworks.com) — Challenge inspiration and MATLAB toolboxes
- [Federal Reserve](https://www.federalreserve.gov) — Public FOMC meeting minutes
- [Google DeepMind](https://deepmind.google) — Gemini API
- [Hugging Face](https://huggingface.co) — Sentence Transformers, CrossEncoder
- [ChromaDB](https://www.trychroma.com) — Open-source vector database

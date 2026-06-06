# AI-assisted: Code structures for FastAPI endpoints, CORS setup, and SSE streaming handlers 
# were developed with assistance from Google Gemini & Claude models, then verified and refined.

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import re
import json
import time
from uuid import uuid4

from loguru import logger as loguru_logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.rag_pipeline import RAGPipeline
from backend.auth import verify_api_key
from backend.dependencies import get_rag_pipeline as get_rag

# Configure logging — loguru is set up in config.py; keep stdlib as fallback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APP_START_TIME = time.time()

app = FastAPI(title="FOMC AI Analyzer API", description="Financial RAG Platform for FOMC Documents")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS so the Next.js frontend can make requests to this backend
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# ── Request Logging Middleware ──
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with a unique X-Request-ID, method, path, status, and latency."""
    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid4())[:8]
        start = time.monotonic()
        
        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start) * 1000)
        
        loguru_logger.info(
            f"[{req_id}] {request.method} {request.url.path} → {response.status_code} | {elapsed_ms}ms"
        )
        
        response.headers["X-Request-ID"] = req_id
        return response

app.add_middleware(RequestLoggingMiddleware)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    mode: Optional[str] = "auto"
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citations: List[str]
    sources: List[Dict[str, Any]]
    similarity_scores: List[float]
    confidence: float

@app.on_event("startup")
async def startup_event():
    logger.info("Starting FOMC AI Analyzer API...")
    try:
        logger.info("Pre-loading RAG Pipeline singleton...")
        get_rag()
    except Exception as e:
        logger.error(f"Error pre-loading RAG Pipeline: {e}")

@app.get("/health")
async def health_check():
    try:
        from backend.vector_store import VectorStore
        vs = VectorStore()
        doc_count = vs.collection.count()
    except Exception as e:
        logger.error(f"Health check vector store count error: {e}")
        doc_count = -1
        
    try:
        from backend.database import get_cache_count
        cache_count = get_cache_count()
    except Exception as e:
        logger.error(f"Health check cache count error: {e}")
        cache_count = -1
    
    uptime_seconds = int(time.time() - APP_START_TIME)
    
    return {
        "status": "ok",
        "indexed_documents": doc_count,
        "cache_entries": cache_count,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "uptime_seconds": uptime_seconds,
        "version": "2.0.0"
    }

HAWK_KEYWORDS = ["inflation", "tighten", "raise rates", "restrictive", "overshoot", "vigilant"]
DOVE_KEYWORDS = ["employment", "cut rates", "accommodate", "support", "stimulus", "below target"]

def compute_hawk_dove_score(text: str) -> dict:
    text_lower = text.lower()
    hawk = sum(text_lower.count(kw) for kw in HAWK_KEYWORDS)
    dove = sum(text_lower.count(kw) for kw in DOVE_KEYWORDS)
    total = hawk + dove or 1
    hawk_pct = round(hawk / total * 100)
    dove_pct = round(dove / total * 100)
    return {
        "hawk": hawk_pct,
        "dove": dove_pct,
        "net": hawk_pct - dove_pct
    }

@app.get("/sentiment-timeline")
@limiter.limit("30/minute")
async def get_sentiment_timeline(request: Request):
    """
    Returns Hawk/Dove sentiment scores per document grouped by meeting date/source.
    """
    try:
        from backend.vector_store import VectorStore
        vs = VectorStore()
        data = vs.collection.get(include=["metadatas", "documents"])
        
        metadatas = data.get("metadatas", [])
        documents = data.get("documents", [])
        
        if not metadatas or not documents:
            return []
            
        doc_groups = {}
        for meta, doc_text in zip(metadatas, documents):
            if not meta:
                continue
            source = meta.get("source_document", "Unknown")
            date = meta.get("meeting_date", "Unknown")
            h_score = meta.get("hawkish_score", 0.0)
            topics = meta.get("topics", "Unknown")
            
            if source not in doc_groups:
                doc_groups[source] = {
                    "source": source,
                    "date": date,
                    "h_scores": [],
                    "texts": [],
                    "topics": set()
                }
            if h_score != 0.0:
                doc_groups[source]["h_scores"].append(h_score)
            doc_groups[source]["texts"].append(doc_text)
            if topics and topics != "Unknown":
                for t in topics.split(","):
                    t_clean = t.strip()
                    if t_clean:
                        doc_groups[source]["topics"].add(t_clean)
            
        results = []
        for source, item in doc_groups.items():
            if item["h_scores"]:
                # Use averaged LLM stance score (mapped from -1.0..+1.0 scale to -100..+100 scale)
                avg_score = sum(item["h_scores"]) / len(item["h_scores"])
                net_stance = round(avg_score * 100)
                # Distribute into positive/negative scores for visual breakdown
                if net_stance >= 0:
                    hawk_score = net_stance
                    dove_score = 0
                else:
                    hawk_score = 0
                    dove_score = abs(net_stance)
            else:
                combined_text = " ".join(item["texts"])
                scores = compute_hawk_dove_score(combined_text)
                hawk_score = scores["hawk"]
                dove_score = scores["dove"]
                net_stance = scores["net"]
                
            results.append({
                "date": item["date"],
                "source": source,
                "hawk_score": hawk_score,
                "dove_score": dove_score,
                "net_stance": net_stance,
                "topics": list(item["topics"])
            })
            
        return sorted(results, key=lambda x: x["date"])
    except Exception as e:
        logger.error(f"Error computing sentiment timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """
    Upload a FOMC document, extract text, clean, chunk, embed, and store dynamically in ChromaDB.
    """
    import magic
    from pathlib import Path
    
    ALLOWED_EXTENSIONS = {".pdf", ".txt"}
    ALLOWED_MIME_TYPES = {"application/pdf", "text/plain"}
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file extension: {ext}. Only PDF or TXT files are supported.")
        
    # Read file contents
    contents = await file.read()
    
    # Size check
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File size exceeds maximum limit of 15MB. Received {round(len(contents)/1024/1024, 1)}MB"
        )
        
    # MIME detection (content-based)
    detected_mime = magic.from_buffer(contents[:4096], mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415, 
            detail=f"Invalid content type: {detected_mime}. Only PDF or TXT content is supported."
        )
        
    # Empty content guard
    if len(contents.strip()) < 100:
        raise HTTPException(
            status_code=422, 
            detail="Document has no extractable text or is too small (minimum 100 bytes required)."
        )
        
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename)
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', safe_filename)
    if not safe_filename:
        # Fallback to UUID if filename is completely stripped
        from uuid import uuid4
        safe_filename = f"{uuid4()}{ext}"
        
    logger.info(f"Received file upload: {file.filename} (sanitized to: {safe_filename})")
    
    upload_dir = "data/raw"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
        
    try:
        # 1. Extract and chunk text using the new page-aware document processor
        from backend.document_processor import extract_and_chunk_pdf, extract_and_chunk_txt
        if safe_filename.endswith('.pdf'):
            chunks = extract_and_chunk_pdf(file_path, chunk_size=1000, overlap=200)
        else:
            chunks = extract_and_chunk_txt(file_path, chunk_size=1000, overlap=200)
            
        if not chunks:
            raise ValueError("No text or chunks could be extracted from the file.")
            
        # 2. Extract meeting date from first few chunks
        sample_text = "".join([c["text"] for c in chunks[:3]])
        date_match = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+(?:–\d+)?,\s+\d{4}',
            sample_text[:3000]
        )
        meeting_date = date_match.group(0) if date_match else "Unknown"
        logger.info(f"Extracted meeting date: {meeting_date}")

        # Extract full text for sentiment/topic analysis
        full_text = " ".join([c["text"] for c in chunks])
        try:
            from backend.financial_analyzer import analyze_document_sentiment
            analysis = analyze_document_sentiment(full_text)
            hawkish_score = analysis.get("hawkish_score", 0.0)
            topics = analysis.get("topics", "Unknown")
        except Exception as ae:
            logger.error(f"Failed to analyze document sentiment during upload: {ae}")
            hawkish_score = 0.0
            topics = "Unknown"

        # 3. Generate embeddings passing filename as source_document
        from backend.embeddings import generate_embeddings
        records = generate_embeddings(
            chunks,
            source_document=safe_filename,
            meeting_date=meeting_date,
            hawkish_score=hawkish_score,
            topics=topics
        )

        # 4. Add embeddings to ChromaDB
        from backend.vector_store import VectorStore
        store = VectorStore()
        store.add_embeddings(records)
        
        # 5. Log to SQLite ingested_documents
        try:
            import hashlib
            from backend.database import mark_document_ingested
            checksum = hashlib.md5(contents).hexdigest()
            mark_document_ingested(
                url=f"local://{safe_filename}",
                title=safe_filename,
                published_date=meeting_date,
                checksum=checksum,
                hawkish_score=hawkish_score,
                topics=topics
            )
        except Exception as dbe:
            logger.error(f"Failed to log document metadata to SQLite: {dbe}")
        
        logger.info(f"--- UPLOAD VERIFICATION: {safe_filename} ---")
        logger.info(f"- Chunks Generated: {len(chunks)}")
        logger.info(f"- Embeddings Indexed: {len(records)}")
        logger.info(f"- Hawkish Score: {hawkish_score}")
        logger.info(f"- Topics: {topics}")
        logger.info(f"----------------------------------------")
        
        return {
            "message": f"Successfully processed and indexed {safe_filename}",
            "status": "success",
            "metadata": {
                "chunks_extracted": len(chunks),
                "meeting_date": meeting_date,
                "hawkish_score": hawkish_score,
                "topics": topics,
                "semantic_indexing": "complete",
                "extraction_validation": "pass" if len(chunks) > 0 else "fail"
            }
        }

    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        # Clean up partial local file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/query", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def query_documents(request: Request, query_request: QueryRequest):
    """
    Query the RAG pipeline with a macroeconomic question using SSE streaming.
    """
    import html as html_module
    
    def sanitize_query(q: str) -> str:
        # Strip HTML tags
        q = re.sub(r'<[^>]+>', '', q)
        # HTML entity decode to get clean plain text
        q = html_module.unescape(q)
        # Remove null bytes
        q = q.replace('\x00', '')
        # Trim and length limit
        q = q.strip()[:2000]
        return q
    
    clean_query = sanitize_query(query_request.query)
    if not clean_query:
        raise HTTPException(status_code=422, detail="Query cannot be empty")
    if len(clean_query) < 3:
        raise HTTPException(status_code=422, detail="Query too short (minimum 3 characters)")
        
    rag = get_rag()
    
    try:
        raw_stream = rag.query_stream(clean_query, top_k=query_request.top_k, mode=query_request.mode)
        
        def event_generator():
            full_answer = ""
            metadata = {}
            for chunk in raw_stream:
                yield chunk
                
                # Check for event type
                try:
                    if chunk.startswith("event: chunk"):
                        lines = chunk.split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                data_str = line[6:]
                                text_val = json.loads(data_str)
                                full_answer += text_val
                    elif chunk.startswith("event: metadata"):
                        lines = chunk.split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                data_str = line[6:]
                                metadata = json.loads(data_str)
                except Exception as parse_err:
                    logger.warning(f"Error parsing SSE chunk for DB logging: {parse_err}")
            
            # Post-stream hook: save message to DB if session_id is active
            if query_request.session_id:
                try:
                    from backend.database import add_chat_message, create_session, list_sessions
                    # Auto-create session if it doesn't exist
                    existing_sessions = [s["id"] for s in list_sessions()]
                    if query_request.session_id not in existing_sessions:
                        # Use first 30 chars of query as session name
                        s_name = query_request.query[:40] + "..." if len(query_request.query) > 40 else query_request.query
                        create_session(query_request.session_id, s_name)
                        
                    # Save user message
                    add_chat_message(query_request.session_id, "user", query_request.query)
                    # Save assistant message
                    add_chat_message(query_request.session_id, "assistant", full_answer, metadata)
                    logger.info(f"Saved exchange to database session {query_request.session_id}")
                except Exception as db_err:
                    logger.error(f"Failed to log interaction to SQLite history: {db_err}")
                    
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Internal error processing query: {str(e)}") # Secure internal logging
        # Return generic error to client to avoid leaking stack traces or keys
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")

class SessionCreateRequest(BaseModel):
    id: str
    name: str

@app.get("/sessions")
async def get_all_sessions():
    try:
        from backend.database import list_sessions
        return {"sessions": list_sessions()}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return {"sessions": []}

@app.post("/sessions", dependencies=[Depends(verify_api_key)])
async def create_new_session(req: SessionCreateRequest):
    try:
        from backend.database import create_session
        session = create_session(req.id, req.name)
        return {"status": "success", "session": session}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    try:
        from backend.database import get_chat_history
        history = get_chat_history(session_id)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def delete_existing_session(session_id: str):
    try:
        from backend.database import delete_session
        delete_session(session_id)
        return {"status": "success", "message": f"Session {session_id} deleted."}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_document(document_id: str):
    """
    Summarize a specific FOMC document.
    """
    # Implementation pending for future expansion
    return {"message": f"Summarization for {document_id} will be implemented in a future update."}

@app.get("/documents")
async def list_documents():
    """
    List all processed FOMC documents dynamically from the vector store.
    """
    try:
        from backend.vector_store import VectorStore
        store = VectorStore()
        collection = store.get_collection()
        
        # Get all records in the collection to extract metadata
        # We only need metadatas to avoid fetching heavy embeddings and documents
        results = collection.get(include=['metadatas'])
        
        docs_map = {}
        for meta in results.get('metadatas', []):
            if not meta:
                continue
            doc_id = meta.get('source_document', 'Unknown')
            if doc_id not in docs_map:
                topics_raw = meta.get('topics', 'Unknown')
                topics_list = [t.strip() for t in topics_raw.split(',')] if topics_raw and topics_raw != "Unknown" else []
                docs_map[doc_id] = {
                    "id": doc_id,
                    "name": doc_id.replace("_", " ").replace(".txt", "").replace(".pdf", ""),
                    "date": meta.get('meeting_date', 'Unknown'),
                    "hawkish_score": float(meta.get('hawkish_score', 0.0)),
                    "topics": topics_list,
                    "chunks": 0
                }
            docs_map[doc_id]["chunks"] += 1
            
        return {"documents": list(docs_map.values())}
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        return {"documents": []}

@app.delete("/documents/{document_id}", dependencies=[Depends(verify_api_key)])
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks from the vector store.
    """
    try:
        from backend.vector_store import VectorStore
        store = VectorStore()
        collection = store.get_collection()
        
        # Delete from ChromaDB where source_document matches
        collection.delete(where={"source_document": document_id})
        
        # Clean up local raw file if it exists
        file_path = os.path.join("data/raw", document_id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
        return {"message": f"Successfully deleted {document_id}"}
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# AI-assisted: Code structures for FastAPI endpoints, CORS setup, and SSE streaming handlers 
# were developed with assistance from Google Gemini & Claude models, then verified and refined.

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import re
import json

from backend.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="FOMC AI Analyzer API", description="Financial RAG Platform for FOMC Documents")

# Configure CORS so the Next.js frontend can make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Pipeline lazily to avoid loading heavy models on import
rag_pipeline = None

def get_rag():
    global rag_pipeline
    if rag_pipeline is None:
        logger.info("Initializing RAG Pipeline...")
        rag_pipeline = RAGPipeline()
    return rag_pipeline

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

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a FOMC document, extract text, clean, chunk, embed, and store dynamically in ChromaDB.
    """
    if not file.filename.endswith('.pdf') and not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files are supported")
        
    logger.info(f"Received file upload: {file.filename}")
    
    # Save the file temporarily
    upload_dir = "data/raw"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    contents = await file.read()
    # Limit to 15MB to prevent DoS/out-of-memory errors
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds maximum limit of 15MB")
        
    with open(file_path, "wb") as f:
        f.write(contents)
        
    try:
        # 1. Extract and chunk text using the new page-aware document processor
        from backend.document_processor import extract_and_chunk_pdf, extract_and_chunk_txt
        if file.filename.endswith('.pdf'):
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

        # 3. Generate embeddings passing filename as source_document
        from backend.embeddings import generate_embeddings
        records = generate_embeddings(
            chunks,
            source_document=file.filename,
            meeting_date=meeting_date
        )

        # 4. Add embeddings to ChromaDB
        from backend.vector_store import VectorStore
        store = VectorStore()
        store.add_embeddings(records)
        
        logger.info(f"--- UPLOAD VERIFICATION: {file.filename} ---")
        logger.info(f"- Chunks Generated: {len(chunks)}")
        logger.info(f"- Embeddings Indexed: {len(records)}")
        logger.info(f"----------------------------------------")
        
        return {
            "message": f"Successfully processed and indexed {file.filename}",
            "status": "success",
            "metadata": {
                "chunks_extracted": len(chunks),
                "meeting_date": meeting_date,
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

@app.post("/query")
async def query_documents(request: QueryRequest):
    """
    Query the RAG pipeline with a macroeconomic question using SSE streaming.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    rag = get_rag()
    
    try:
        raw_stream = rag.query_stream(request.query, top_k=request.top_k, mode=request.mode)
        
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
            if request.session_id:
                try:
                    from backend.database import add_chat_message, create_session, list_sessions
                    # Auto-create session if it doesn't exist
                    existing_sessions = [s["id"] for s in list_sessions()]
                    if request.session_id not in existing_sessions:
                        # Use first 30 chars of query as session name
                        s_name = request.query[:40] + "..." if len(request.query) > 40 else request.query
                        create_session(request.session_id, s_name)
                        
                    # Save user message
                    add_chat_message(request.session_id, "user", request.query)
                    # Save assistant message
                    add_chat_message(request.session_id, "assistant", full_answer, metadata)
                    logger.info(f"Saved exchange to database session {request.session_id}")
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

@app.post("/sessions")
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

@app.delete("/sessions/{session_id}")
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
                docs_map[doc_id] = {
                    "id": doc_id,
                    "name": doc_id.replace("_", " ").replace(".txt", "").replace(".pdf", ""),
                    "date": meta.get('meeting_date', 'Unknown'),
                    "chunks": 0
                }
            docs_map[doc_id]["chunks"] += 1
            
        return {"documents": list(docs_map.values())}
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        return {"documents": []}

@app.delete("/documents/{document_id}")
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

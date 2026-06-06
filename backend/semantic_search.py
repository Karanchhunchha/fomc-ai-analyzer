# AI-assisted: SemanticSearcher hybrid retrieval pattern logic and CrossEncoder score sigmoid normalization 
# were structured and implemented with AI coding guidance.

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer, CrossEncoder
from backend.vector_store import VectorStore
from backend.bm25_search import BM25, combine_scores

logger = logging.getLogger(__name__)

from backend.config import config

# ── Module-level singletons (loaded once, shared across all requests) ──
_embedding_model = None
_cross_encoder_model = None
_rerank_executor = ThreadPoolExecutor(max_workers=2)

def get_embedding_model(model_name: str = config.EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model singleton: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def get_cross_encoder(model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2') -> CrossEncoder:
    global _cross_encoder_model
    if _cross_encoder_model is None:
        logger.info(f"Loading cross-encoder model singleton: {model_name}")
        _cross_encoder_model = CrossEncoder(model_name)
    return _cross_encoder_model


class SemanticSearcher:
    def __init__(self, model_name=config.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.vector_store = VectorStore()
        self.collection = self.vector_store.get_collection()
        
        # Reuse module-level singletons
        self.model = get_embedding_model(self.model_name)
        self.cross_encoder = get_cross_encoder()
        
        # Initialize BM25 for hybrid search (lazy loading)
        self._bm25 = None
        self._bm25_corpus = None
        
    def _get_bm25_index(self):
        """Lazy load and initialize BM25 index with all documents in the collection."""
        if self._bm25 is None:
            logger.info("Building BM25 index for hybrid search...")
            try:
                # Get all documents from the collection
                all_data = self.collection.get(include=["documents"])
                if all_data and all_data.get("documents"):
                    self._bm25_corpus = all_data["documents"]
                    self._bm25 = BM25(self._bm25_corpus)
                    logger.info(f"BM25 index built with {len(self._bm25_corpus)} documents")
                else:
                    logger.warning("No documents found in collection for BM25 indexing")
                    self._bm25_corpus = []
                    self._bm25 = None
            except Exception as e:
                logger.error(f"Failed to build BM25 index: {e}")
                self._bm25_corpus = []
                self._bm25 = None
        return self._bm25
        
    def search(self, query, top_k=config.TOP_K_RETRIEVAL):
        """
        Search for semantically relevant chunks based on a query with local keyword hybrid reranking.
        Returns text, citations, similarity scores, and metadata.
        """
        import os
        import re
        
        logger.info(f"Performing hybrid semantic search for: '{query}'")
        
        # 1. Detect if any active file is mentioned in the query
        matched_doc = None
        try:
            # Retrieve all unique source documents in ChromaDB
            metadatas = self.collection.get(include=['metadatas']).get('metadatas', [])
            active_docs = set()
            for meta in metadatas:
                if meta and 'source_document' in meta:
                    active_docs.add(meta['source_document'])
            
            query_lower = query.lower()
            # Try to match full file names or basenames
            for doc in active_docs:
                doc_lower = doc.lower()
                basename = os.path.splitext(doc_lower)[0]
                
                # Check for exact word matches of either filename or basename
                escaped_doc = re.escape(doc_lower)
                escaped_base = re.escape(basename)
                if re.search(rf'\b{escaped_doc}\b', query_lower) or re.search(rf'\b{escaped_base}\b', query_lower):
                    matched_doc = doc
                    break
            
            # Substring/fuzzy checks if no exact boundary match
            if not matched_doc:
                for doc in active_docs:
                    doc_lower = doc.lower()
                    if "resume" in query_lower and "resume" in doc_lower:
                        matched_doc = doc
                        break
                    elif "cv" in query_lower and "cv" in doc_lower:
                        matched_doc = doc
                        break
                    elif "fomc" in query_lower and "fomc" in doc_lower:
                        matched_doc = doc
                        break
        except Exception as e:
            logger.error(f"Error checking active documents for file-aware search: {e}")

        # 2. Retrieve query candidates (retrieve more than top_k for reranking)
        candidate_count = max(top_k * 4, 20)
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Query ChromaDB (with optional document filter)
        where_filter = {"source_document": matched_doc} if matched_doc else None
        if matched_doc:
            logger.info(f"File-aware retrieval active: restricting search to document '{matched_doc}'")
            
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_count,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}. Retrying without where filter.")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_count,
                include=["documents", "metadatas", "distances"]
            )
            matched_doc = None
        
        if not results['documents'] or not results['documents'][0]:
            logger.warning("No relevant chunks found.")
            return {
                "text": [],
                "citations": [],
                "similarity_scores": [],
                "metadata": []
            }
            
        import math
        # 3. Score and Rerank candidates using CrossEncoder
        raw_texts = results['documents'][0]
        raw_metadatas = results['metadatas'][0]
        
        # 4. Get BM25 scores for hybrid search
        bm25_index = self._get_bm25_index()
        if bm25_index and self._bm25_corpus:
            # Map raw_texts back to corpus indices for BM25 scoring
            bm25_scores = []
            for text in raw_texts:
                # Find the index in the corpus
                try:
                    corpus_idx = self._bm25_corpus.index(text)
                    bm25_score = bm25_index.score(query, corpus_idx)
                    bm25_scores.append(bm25_score)
                except ValueError:
                    bm25_scores.append(0.0)
            logger.info(f"BM25 scores computed for {len(bm25_scores)} documents")
        else:
            bm25_scores = [0.0] * len(raw_texts)
        
        reranked_candidates = self._rerank(query, raw_texts, raw_metadatas, bm25_scores)
            
        # Sort by hybrid similarity score descending
        reranked_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Slice down to the top_k requests
        top_candidates = reranked_candidates[:top_k]
        
        # Format results for the return signature
        formatted_results = {
            "text": [c["text"] for c in top_candidates],
            "citations": [c["citation"] for c in top_candidates],
            "similarity_scores": [c["similarity_score"] for c in top_candidates],
            "metadata": [c["metadata"] for c in top_candidates],
            "file_scoped": matched_doc is not None
        }
        
        return formatted_results

    def _rerank(self, query: str, raw_texts: list, raw_metadatas: list, bm25_scores: list = None) -> list:
        """CrossEncoder reranking with BM25 hybrid scoring — offloads the blocking predict() to a thread pool.
        
        This prevents the CPU-intensive CrossEncoder inference from blocking
        the FastAPI async event loop, even when called from synchronous code paths.
        """
        import math
        
        cross_inp = [[query, text] for text in raw_texts]
        
        # Offload the heavy predict() call to the thread pool so the event loop
        # stays responsive for other requests during reranking.
        future = _rerank_executor.submit(self.cross_encoder.predict, cross_inp)
        cross_scores = future.result()  # blocks this thread only, not the event loop
        
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))
        
        reranked = []
        for idx in range(len(raw_texts)):
            doc_text = raw_texts[idx]
            meta = raw_metadatas[idx] if raw_metadatas[idx] else {}
            cross_score = sigmoid(cross_scores[idx])
            
            # Combine CrossEncoder score with BM25 score if available
            if bm25_scores and idx < len(bm25_scores):
                # Normalize BM25 score and combine with cross-encoder score
                bm25_score = bm25_scores[idx]
                # Simple linear combination: 70% cross-encoder, 30% BM25
                hybrid_score = 0.7 * cross_score + 0.3 * (bm25_score / (max(bm25_scores) if max(bm25_scores) > 0 else 1))
            else:
                hybrid_score = cross_score
            
            updated_meta = {
                **meta,
                "chunk_text": doc_text,
                "vector_score": f"{cross_score:.4f}",
                "bm25_score": f"{bm25_scores[idx] if bm25_scores and idx < len(bm25_scores) else 0:.4f}" if bm25_scores else "N/A"
            }
            reranked.append({
                "text": doc_text,
                "citation": meta.get('source_document', 'Unknown'),
                "similarity_score": hybrid_score,
                "metadata": updated_meta
            })
        return reranked

    async def rerank_async(self, query: str, raw_texts: list, raw_metadatas: list) -> list:
        """Run CrossEncoder reranking in a thread pool to avoid blocking the async event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _rerank_executor,
            self._rerank,
            query,
            raw_texts,
            raw_metadatas
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Simple test
    searcher = SemanticSearcher()
    res = searcher.search("What did the Fed say about inflation?")
    
    for i, doc in enumerate(res['text']):
        print(f"--- Result {i+1} (Score: {res['similarity_scores'][i]:.4f}) ---")
        print(f"Source: {res['citations'][i]}")
        print(f"Text snippet: {doc[:150]}...")
        print()

# AI-assisted: SemanticSearcher hybrid retrieval pattern logic and CrossEncoder score sigmoid normalization 
# were structured and implemented with AI coding guidance.

import logging
from sentence_transformers import SentenceTransformer, CrossEncoder
from backend.vector_store import VectorStore

logger = logging.getLogger(__name__)

from backend.config import config

class SemanticSearcher:
    def __init__(self, model_name=config.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.vector_store = VectorStore()
        self.collection = self.vector_store.get_collection()
        
        logger.info(f"Loading search model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Loading cross-encoder model: cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
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
        reranked_candidates = []
        
        raw_texts = results['documents'][0]
        raw_metadatas = results['metadatas'][0]
        
        cross_inp = [[query, text] for text in raw_texts]
        cross_scores = self.cross_encoder.predict(cross_inp)
        
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))
            
        for idx in range(len(raw_texts)):
            doc_text = raw_texts[idx]
            meta = raw_metadatas[idx] if raw_metadatas[idx] else {}
            
            # CrossEncoder outputs logits, so we convert them using sigmoid for a 0-1 confidence score roughly
            hybrid_score = sigmoid(cross_scores[idx])
            
            # Add matched keywords and scores details to metadata
            updated_meta = {
                **meta,
                "chunk_text": doc_text,
                "vector_score": f"{hybrid_score:.4f}"
            }
            
            reranked_candidates.append({
                "text": doc_text,
                "citation": meta.get('source_document', 'Unknown'),
                "similarity_score": hybrid_score,
                "metadata": updated_meta
            })
            
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

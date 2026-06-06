"""
Centralized FastAPI dependency injection singletons.
Prevents repeated instantiation of heavy resources (VectorStore, RAG Pipeline).
"""
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store():
    """Return a singleton VectorStore instance."""
    from backend.vector_store import VectorStore
    logger.info("Initializing VectorStore singleton")
    return VectorStore()


@lru_cache(maxsize=1)
def get_rag_pipeline():
    """Return a singleton RAGPipeline instance."""
    from backend.rag_pipeline import RAGPipeline
    logger.info("Initializing RAGPipeline singleton")
    return RAGPipeline()


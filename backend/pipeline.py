import logging
import os
from backend.chunk_text import process_and_save_chunks
from backend.embeddings import process_embeddings
from backend.vector_store import populate_vector_store

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline():
    """
    Run the complete data processing pipeline:
    Extraction -> Cleaning -> Chunking -> Embedding -> ChromaDB Ingestion
    """
    logger.info("Starting Full Automation Pipeline...")
    
    # We assume extraction and cleaning have produced fomc_text_cleaned.txt
    CLEAN_TEXT = "data/processed/fomc_text_cleaned.txt"
    CHUNKS = "data/chunks/fomc_chunks.json"
    EMBEDDINGS = "data/embeddings/fomc_embeddings.json"
    
    if not os.path.exists(CLEAN_TEXT):
        logger.error(f"Clean text file not found: {CLEAN_TEXT}. Please run extraction and cleaning first.")
        return
        
    logger.info("--- Stage 3: Chunking ---")
    process_and_save_chunks(CLEAN_TEXT, CHUNKS)
    
    logger.info("--- Stage 4: Embeddings ---")
    process_embeddings(CHUNKS, EMBEDDINGS)
    
    logger.info("--- Stage 5: Vector Database Ingestion ---")
    populate_vector_store(EMBEDDINGS)
    
    logger.info("Full Automation Pipeline Completed Successfully.")

if __name__ == "__main__":
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
    run_pipeline()

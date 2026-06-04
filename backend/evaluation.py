import logging
import time
from backend.semantic_search import SemanticSearcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEST_QUERIES = [
    "What did the Fed say about inflation?",
    "What concerns existed about labor markets?",
    "What was the monetary policy outlook?",
    "Did the committee discuss economic growth risks?",
    "What risks were associated with inflation persistence?",
    "What is Apple's earnings outlook for next quarter?",
    "What is the price of gold in 2026?",
    "How do you cook a chocolate chip cookie?"
]

def evaluate_retrieval():
    """
    Validate full RAG pipeline quality based on test queries.
    Logs retrieval stats, Gemini responses, and handles out-of-scope verification.
    """
    logger.info("Starting RAG Pipeline Evaluation...")
    from backend.rag_pipeline import RAGPipeline
    rag = RAGPipeline()
    
    for query in TEST_QUERIES:
        logger.info(f"\n========================================\nEvaluating Query: '{query}'")
        
        try:
            res = rag.query(query, top_k=3)
            
            logger.info(f"  [Confidence Score] {res['confidence']:.4f}")
            logger.info(f"  [Citations] {res['citations']}")
            logger.info(f"  [RAG Answer]\n{res['answer']}")
            
        except Exception as e:
            logger.error(f"Error evaluating query '{query}': {e}")
            
        # Add a sleep to stay below the 15 RPM free-tier rate limit
        time.sleep(4)
            
    logger.info("\nRAG Pipeline Evaluation Complete.")

if __name__ == "__main__":
    import os
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
    evaluate_retrieval()

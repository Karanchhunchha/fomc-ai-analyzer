import os
import sys
import logging
from typing import List, Dict

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EVAL_DATASET = [
    {
        "query": "What did the committee say about the labor market?",
        "expected_themes": ["job gains", "unemployment rate", "strong", "labor demand"]
    },
    {
        "query": "Are they going to cut interest rates soon?",
        "expected_themes": ["target range", "federal funds rate", "inflation", "2 percent"]
    },
    {
        "query": "What are the main risks to the economic outlook?",
        "expected_themes": ["geopolitical", "inflation risks", "financial conditions", "commercial real estate"]
    }
]

def run_retrieval_evaluation():
    """
    Evaluates the retrieval and reranking pipeline.
    Checks if the retrieved chunks contain the expected themes.
    """
    logger.info("Initializing RAG Pipeline for Evaluation...")
    rag = RAGPipeline()
    
    total_score = 0
    max_score = len(EVAL_DATASET)
    
    print("\n--- Starting Retrieval Evaluation ---\n")
    
    for i, item in enumerate(EVAL_DATASET):
        query = item["query"]
        expected_themes = item["expected_themes"]
        
        print(f"Test {i+1}: '{query}'")
        try:
            # Get raw chunks from retriever + reranker
            search_results = rag.searcher.search(query, top_k=5)
            chunks = search_results.get("text", [])
            scores = search_results.get("similarity_scores", [])
            
            # Check if expected themes are present in the retrieved chunks
            combined_text = " ".join([text.lower() for text in chunks])
            
            themes_found = sum(1 for theme in expected_themes if theme.lower() in combined_text)
            coverage = themes_found / len(expected_themes)
            
            if coverage >= 0.5:
                print(f"[PASS]: Found {themes_found}/{len(expected_themes)} expected themes in retrieved context.")
                total_score += 1
            else:
                print(f"[FAIL]: Found {themes_found}/{len(expected_themes)} expected themes in retrieved context.")
                
            print(f"   Top Chunk Score: {scores[0] if scores else 'N/A'}")
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] during evaluation: {str(e)}")
            
    print(f"\nFinal Retrieval Accuracy: {total_score}/{max_score} ({(total_score/max_score)*100:.1f}%)")
    
if __name__ == "__main__":
    run_retrieval_evaluation()

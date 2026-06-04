import os
import sys
import logging
from sentence_transformers import CrossEncoder

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_grounding(answer: str, retrieved_chunks: list) -> float:
    """
    Check if the answer is grounded in the retrieved chunks.
    Uses a CrossEncoder to measure entailment/similarity between context and answer.
    """
    try:
        # Load a lightweight cross-encoder for NLI (Natural Language Inference)
        # For demonstration, we'll use a general cross-encoder. In production, a specific NLI model is better.
        logger.info("Loading CrossEncoder for Grounding Check...")
        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
        
        combined_context = " ".join(retrieved_chunks)
        
        # We score how well the context entails the answer.
        score = model.predict([combined_context, answer])
        
        return float(score)
    except Exception as e:
        logger.error(f"Failed to run grounding check: {e}")
        return 0.0

def run_grounding_eval():
    rag = RAGPipeline()
    query = "What is the committee's stance on inflation?"
    
    print(f"\n--- Grounding Check ---")
    print(f"Query: {query}")
    
    # Generate full answer
    print("Generating answer...")
    stream = rag.query_stream(query, top_k=3, mode="auto")
    
    full_answer = ""
    for chunk in stream:
        if "chunk" in chunk:
            try:
                # Simple SSE chunk parser
                import json
                lines = chunk.split("\n")
                for line in lines:
                    if line.startswith("data: "):
                        text = json.loads(line[6:])
                        full_answer += text
            except:
                pass
                
    print("\nAnswer Generated:")
    print(full_answer[:200] + "...")
    
    # Re-retrieve to get the exact chunks
    search_results = rag.searcher.search(query, top_k=3)
    chunks = search_results.get("text", [])
    
    print("\nCalculating Grounding Score...")
    grounding_score = check_grounding(full_answer, chunks)
    
    print(f"Grounding Score: {grounding_score:.4f}")
    if grounding_score > 0.0:
        print("[PASS]: The answer appears to be grounded in the retrieved context.")
    else:
        print("[WARNING]: Potential Hallucination: The answer may not be fully supported by the context.")

if __name__ == "__main__":
    run_grounding_eval()

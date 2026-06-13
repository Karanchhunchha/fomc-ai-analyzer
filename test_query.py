import os
import sys

# Ensure we're in the right directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.rag_pipeline import RAGPipeline

def test():
    try:
        rag = RAGPipeline()
        print("Pipeline initialized. Running query_stream...")
        for chunk in rag.query_stream("What was the rate decision in January 2026?"):
            print(f"SSE: {chunk.strip()}")
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    test()

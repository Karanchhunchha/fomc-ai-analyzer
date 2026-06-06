import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from backend.config import config
MODEL_NAME = config.EMBEDDING_MODEL_NAME

def load_chunks(input_path):
    """Load chunks from the JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_embeddings(chunks, model_name=MODEL_NAME, batch_size=32, source_document="fomc_text_cleaned.txt", meeting_date="Unknown", hawkish_score=0.0, topics="Unknown"):
    """
    Generate embeddings for a list of text chunks.
    Returns a list of dictionaries with chunk metadata and embeddings.
    """
    logger.info(f"Loading model: {model_name}")
    try:
        # Reuse the shared singleton model from semantic_search
        from backend.semantic_search import get_embedding_model
        model = get_embedding_model(model_name)
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise
    
    records = []
    total_chunks = len(chunks)
    
    import hashlib
    # Generate a short unique hash for the source document name to namespace chunk IDs
    doc_hash = hashlib.md5(source_document.encode("utf-8")).hexdigest()[:8]
    
    logger.info(f"Generating embeddings for {total_chunks} chunks in batches of {batch_size}...")
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i+batch_size]
        batch_texts = []
        for item in batch:
            if isinstance(item, dict):
                batch_texts.append(item["text"])
            else:
                batch_texts.append(item)
                
        batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
        
        for j, item in enumerate(batch):
            global_index = i + j
            if isinstance(item, dict):
                chunk_text = item["text"]
                section_name = item.get("section_name", "Overview")
                semantic_summary = item.get("semantic_summary", "")
                page_number = item.get("page_number", 1)
            else:
                chunk_text = item
                section_name = "Overview"
                semantic_summary = ""
                page_number = 1
                
            record = {
                "chunk_id": f"chunk_{doc_hash}_{global_index}",
                "meeting_date": meeting_date,
                "source_document": source_document,
                "section_name": section_name,
                "semantic_summary": semantic_summary,
                "page_number": page_number,
                "hawkish_score": hawkish_score,
                "topics": topics,
                "chunk_text": chunk_text,
                "embedding": batch_embeddings[j].tolist()
            }
            records.append(record)
            
        if (i + batch_size) % 100 == 0 or (i + batch_size) >= total_chunks:
            logger.info(f"Processed {min(i + batch_size, total_chunks)} / {total_chunks} chunks")
            
    return records

def save_embeddings(records, output_path):
    """Save the embeddings records to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
    logger.info(f"Saved {len(records)} embedding records to {output_path}")

def process_embeddings(input_file, output_file):
    """Main pipeline for embedding generation."""
    try:
        logger.info(f"Reading chunks from {input_file}")
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return
            
        chunks = load_chunks(input_file)
        if not chunks:
            logger.warning("No chunks found in the input file.")
            return
            
        records = generate_embeddings(chunks)
        save_embeddings(records, output_file)
        logger.info("Embedding generation completed successfully.")
        
    except Exception as e:
        logger.error(f"An error occurred during embedding generation: {e}")

if __name__ == "__main__":
    INPUT_FILE = "data/chunks/fomc_chunks.json"
    OUTPUT_FILE = "data/embeddings/fomc_embeddings.json"
    
    # Optional: adjust working directory to project root if executed from backend folder
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
        
    process_embeddings(INPUT_FILE, OUTPUT_FILE)

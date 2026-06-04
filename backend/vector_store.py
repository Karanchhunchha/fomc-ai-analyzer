import chromadb
import json
import logging
import os
from chromadb.config import Settings

logger = logging.getLogger(__name__)

from backend.config import config

class VectorStore:
    def __init__(self, db_path=config.CHROMADB_PATH, collection_name=config.CHROMADB_COLLECTION):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistence
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
        
    def add_embeddings(self, embeddings_data, batch_size=100):
        """
        Add embeddings to the ChromaDB collection in batches.
        """
        total = len(embeddings_data)
        logger.info(f"Adding {total} embeddings to the vector store...")
        
        for i in range(0, total, batch_size):
            batch = embeddings_data[i:i+batch_size]
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for item in batch:
                ids.append(item["chunk_id"])
                embeddings.append(item["embedding"])
                documents.append(item["chunk_text"])
                
                # Format metadata
                metadata = {
                    "chunk_id": item["chunk_id"],
                    "meeting_date": item.get("meeting_date", "Unknown"),
                    "source_document": item.get("source_document", "Unknown"),
                    "section_name": item.get("section_name", "Overview"),
                    "semantic_summary": item.get("semantic_summary", ""),
                    "page_number": item.get("page_number", 1),
                    "chunk_index": item["chunk_id"].split("_")[-1] if "_" in item["chunk_id"] else "0"
                }
                metadatas.append(metadata)
                
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                logger.error(f"Failed to add batch {i} to {i+len(batch)}: {e}")
                
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= total:
                logger.info(f"Added {min(i + batch_size, total)} / {total} items to ChromaDB")
                
    def get_collection(self):
        return self.collection

def populate_vector_store(input_file="data/embeddings/fomc_embeddings.json"):
    """Pipeline to read embeddings and store them in ChromaDB."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
            
        store = VectorStore()
        store.add_embeddings(embeddings_data)
        logger.info("Successfully populated vector store.")
    except Exception as e:
        logger.error(f"Error populating vector store: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
        
    INPUT_FILE = "data/embeddings/fomc_embeddings.json"
    if os.path.exists(INPUT_FILE):
        populate_vector_store(INPUT_FILE)
    else:
        logger.error(f"Input file not found: {INPUT_FILE}")

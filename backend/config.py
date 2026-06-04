import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    if not GEMINI_API_KEY and not OPENROUTER_API_KEY:
        raise ValueError("Missing both GEMINI_API_KEY and OPENROUTER_API_KEY environment variables. Please provide at least one.")
        
    # Model Configuration
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    
    # Select default model based on active provider
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    OPENROUTER_MODEL_NAME = "meta-llama/llama-3.3-70b-instruct:free"
    
    # Text Chunking Settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Database Settings
    CHROMADB_PATH = "data/chroma_db"
    CHROMADB_COLLECTION = "fomc_documents"
    
    # Retrieval Settings
    TOP_K_RETRIEVAL = 5
    MIN_SIMILARITY_THRESHOLD = 0.30
    
    # Logging Settings
    LOGS_DIR = "backend/logs"
    QUERY_LOG_FILE = "backend/logs/query_logs.json"

config = Config()

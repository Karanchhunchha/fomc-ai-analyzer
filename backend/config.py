import os
from dotenv import load_dotenv
import logging
import sys

from pathlib import Path
from loguru import logger as loguru_logger

# Load environment variables
load_dotenv()


def _model_list(env_value: str, defaults: list[str]) -> list[str]:
    if env_value:
        return [m.strip() for m in env_value.split(",") if m.strip()]
    return defaults


class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    if not GEMINI_API_KEY and not OPENROUTER_API_KEY:
        raise ValueError("Missing both GEMINI_API_KEY and OPENROUTER_API_KEY environment variables. Please provide at least one.")
        
    # Model Configuration
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    
    # Select default model based on active provider
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")

    GEMINI_FALLBACK_MODELS = _model_list(
        os.getenv("GEMINI_FALLBACK_MODELS", ""),
        ["gemini-2.0-flash", "gemini-1.5-flash"],
    )
    OPENROUTER_FALLBACK_MODELS = _model_list(
        os.getenv("OPENROUTER_FALLBACK_MODELS", ""),
        [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-2-9b-it:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "qwen/qwen-2.5-7b-instruct:free",
        ],
    )

    @classmethod
    def gemini_model_candidates(cls) -> list[str]:
        models = [cls.GEMINI_MODEL_NAME, *cls.GEMINI_FALLBACK_MODELS]
        seen: set[str] = set()
        ordered: list[str] = []
        for model in models:
            if model not in seen:
                seen.add(model)
                ordered.append(model)
        return ordered

    @classmethod
    def openrouter_model_candidates(cls) -> list[str]:
        models = [cls.OPENROUTER_MODEL_NAME, *cls.OPENROUTER_FALLBACK_MODELS]
        seen: set[str] = set()
        ordered: list[str] = []
        for model in models:
            if model not in seen:
                seen.add(model)
                ordered.append(model)
        return ordered
    
    # Text Chunking Settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Database Settings
    CHROMADB_PATH = os.getenv("CHROMA_PERSIST_PATH", "data/chroma_db")
    CHROMADB_COLLECTION = "fomc_documents"
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "backend/data/ck_workspace.db")
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fomc_analyzer")
    
    # Retrieval Settings
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.20"))
    
    # Logging Settings
    LOGS_DIR = "backend/logs"
    QUERY_LOG_FILE = "backend/logs/query_logs.json"

# Ensure directories exist
Path(Config.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)
Path(Config.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(Config.LOGS_DIR).mkdir(parents=True, exist_ok=True)

config = Config()


# ── Loguru Structured Logging Setup ──
class _InterceptHandler(logging.Handler):
    """Intercept stdlib logging and route to loguru."""
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """Configure loguru with console + daily rotated file sinks."""
    # Remove default loguru handler
    loguru_logger.remove()
    
    # Console sink — human-readable
    loguru_logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    
    # File sink — structured JSON, daily rotation
    loguru_logger.add(
        os.path.join(config.LOGS_DIR, "app_{time:YYYY-MM-DD}.log"),
        format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # Rotate at midnight
        retention="7 days",
        compression="gz",
        level="DEBUG",
        serialize=False,
    )
    
    # Intercept stdlib loggers
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = [_InterceptHandler()]
        logging.getLogger(name).propagate = False

setup_logging()
logger = logging.getLogger(__name__)

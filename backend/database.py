import sqlite3
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.config import config

logger = logging.getLogger(__name__)

DB_PATH = config.SQLITE_DB_PATH
_db_initialized = False
_using_sqlite_fallback = False

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def _is_local_postgres_url(url: str) -> bool:
    url_lower = (url or "").lower()
    return "localhost" in url_lower or "127.0.0.1" in url_lower


def _use_postgres() -> bool:
    return config.DATABASE_TYPE == "postgres" and not _using_sqlite_fallback


def _open_connection():
    """Open a database connection without running schema initialization."""
    global _using_sqlite_fallback

    if _use_postgres():
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 is not installed but DATABASE_TYPE is set to 'postgres'.")
        try:
            return psycopg2.connect(config.DATABASE_URL, connect_timeout=3)
        except Exception as exc:
            if _is_local_postgres_url(config.DATABASE_URL):
                logger.warning(
                    "PostgreSQL unavailable (%s). Falling back to SQLite at %s.",
                    exc,
                    DB_PATH,
                )
                _using_sqlite_fallback = True
            else:
                raise

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    _ensure_db_initialized()
    return _open_connection()


def _ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True


class DbCursor:
    """Unified wrapper around SQLite and psycopg2 cursors to translate SQL syntax differences."""
    def __init__(self, conn):
        self.conn = conn
        self.is_postgres = _use_postgres()
        if self.is_postgres:
            self.cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            self.cursor = conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_type is not None:
            self.conn.rollback()
        else:
            self.conn.commit()

    def execute(self, query, params=None):
        if self.is_postgres:
            # 1. Replace SQLite placeholder '?' with PostgreSQL '%s'
            translated_query = query.replace('?', '%s')
            
            # 2. Translate SQLite-specific 'AUTOINCREMENT' to PostgreSQL 'SERIAL'
            if "INTEGER PRIMARY KEY AUTOINCREMENT" in translated_query:
                translated_query = translated_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                
            # 3. Translate SQLite-specific 'INSERT OR REPLACE' to PostgreSQL 'ON CONFLICT'
            if "INSERT OR REPLACE" in translated_query:
                if "INTO sessions" in translated_query:
                    translated_query = """
                    INSERT INTO sessions (id, name, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (id) DO UPDATE SET 
                        name = EXCLUDED.name, 
                        updated_at = EXCLUDED.updated_at
                    """
                elif "INTO query_cache" in translated_query:
                    translated_query = """
                    INSERT INTO query_cache (query_hash, query, response_text, metadata, created_at) 
                    VALUES (%s, %s, %s, %s, %s) 
                    ON CONFLICT (query_hash) DO UPDATE SET 
                        query = EXCLUDED.query, 
                        response_text = EXCLUDED.response_text, 
                        metadata = EXCLUDED.metadata, 
                        created_at = EXCLUDED.created_at
                    """
                elif "INTO ingested_documents" in translated_query:
                    translated_query = """
                    INSERT INTO ingested_documents (url, title, published_date, checksum, processed_at, hawkish_score, topics) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (url) DO UPDATE SET 
                        title = EXCLUDED.title, 
                        published_date = EXCLUDED.published_date, 
                        checksum = EXCLUDED.checksum, 
                        processed_at = EXCLUDED.processed_at, 
                        hawkish_score = EXCLUDED.hawkish_score, 
                        topics = EXCLUDED.topics
                    """
            
            self.cursor.execute(translated_query, params)
        else:
            self.cursor.execute(query, params or ())

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

def init_db():
    engine = "postgres" if _use_postgres() else "sqlite"
    logger.info(f"Initializing database using engine: {engine}")
    conn = _open_connection()
    # PostgreSQL requires autocommit for DDL (CREATE TABLE) to persist
    if _use_postgres():
        conn.autocommit = True
    try:
        with DbCursor(conn) as db:
            # 1. Create sessions table
            db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            
            # 2. Create chat_history table
            db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """)
            
            # Create indexes for performance
            db.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id)")
            
            # 3. Create query_cache table
            db.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                response_text TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
            """)
            
            # 4. Create ingested_documents table for ingestion pipeline
            db.execute("""
            CREATE TABLE IF NOT EXISTS ingested_documents (
                url TEXT PRIMARY KEY,
                title TEXT,
                published_date TEXT,
                checksum TEXT,
                processed_at TEXT NOT NULL,
                hawkish_score REAL,
                topics TEXT
            )
            """)
            
            # Add new columns for Phase 3 if they don't exist
            try:
                db.execute("ALTER TABLE ingested_documents ADD COLUMN hawkish_score REAL")
            except Exception:
                pass # Column already exists or table alter failed
                
            try:
                db.execute("ALTER TABLE ingested_documents ADD COLUMN topics TEXT")
            except Exception:
                pass # Column already exists or table alter failed
    finally:
        conn.close()
    logger.info("Database initialization complete.")

def get_query_hash(query: str, doc_ids: Optional[List[str]] = None) -> str:
    """Generate a stable SHA256 hash for query and documents constraint."""
    doc_str = ",".join(sorted(doc_ids)) if doc_ids else ""
    raw_key = f"{query.strip().lower()}:{doc_str}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def create_session(session_id: str, name: str) -> Dict[str, Any]:
    conn = get_connection()
    now = datetime.utcnow().isoformat() + "Z"
    try:
        with DbCursor(conn) as db:
            db.execute(
                "INSERT OR REPLACE INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, name, now, now)
            )
        return {"id": session_id, "name": name, "created_at": now, "updated_at": now}
    finally:
        conn.close()

def list_sessions() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
            return db.fetchall()
    finally:
        conn.close()

def delete_session(session_id: str) -> None:
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    finally:
        conn.close()

def add_chat_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    conn = get_connection()
    now = datetime.utcnow().isoformat() + "Z"
    meta_str = json.dumps(metadata) if metadata else None
    try:
        with DbCursor(conn) as db:
            db.execute(
                "INSERT INTO chat_history (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, now, meta_str)
            )
            db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
    finally:
        conn.close()

def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute(
                "SELECT role, content, timestamp, metadata FROM chat_history WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = db.fetchall()
            history = []
            for row in rows:
                item = dict(row)
                if item.get("metadata"):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        item["metadata"] = {}
                else:
                    item["metadata"] = {}
                history.append(item)
            return history
    finally:
        conn.close()

def get_cached_query(query: str, doc_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve response from cache if it exists."""
    q_hash = get_query_hash(query, doc_ids)
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute(
                "SELECT response_text, metadata FROM query_cache WHERE query_hash = ?",
                (q_hash,)
            )
            row = db.fetchone()
            if row:
                res = dict(row)
                if res.get("metadata"):
                    try:
                        res["metadata"] = json.loads(res["metadata"])
                    except Exception:
                        res["metadata"] = {}
                else:
                    res["metadata"] = {}
                return res
            return None
    finally:
        conn.close()

def cache_query(query: str, doc_ids: Optional[List[str]], response_text: str, metadata: Optional[Dict[str, Any]]) -> None:
    """Save response to cache."""
    q_hash = get_query_hash(query, doc_ids)
    conn = get_connection()
    now = datetime.utcnow().isoformat() + "Z"
    meta_str = json.dumps(metadata) if metadata else None
    try:
        with DbCursor(conn) as db:
            db.execute(
                "INSERT OR REPLACE INTO query_cache (query_hash, query, response_text, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (q_hash, query, response_text, meta_str, now)
            )
    finally:
        conn.close()

def get_cache_count() -> int:
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute("SELECT COUNT(*) FROM query_cache")
            row = db.fetchone()
            return list(row.values())[0] if row else 0
    except Exception:
        return 0
    finally:
        conn.close()

def is_document_ingested(url: str) -> bool:
    """Check if a document URL has already been processed by the ingestion worker."""
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute("SELECT 1 FROM ingested_documents WHERE url = ?", (url,))
            return db.fetchone() is not None
    finally:
        conn.close()

def mark_document_ingested(url: str, title: str, published_date: str, checksum: str, hawkish_score: Optional[float] = None, topics: Optional[str] = None) -> None:
    """Record a document as successfully processed in the database."""
    conn = get_connection()
    now = datetime.utcnow().isoformat() + "Z"
    try:
        with DbCursor(conn) as db:
            db.execute(
                "INSERT OR REPLACE INTO ingested_documents (url, title, published_date, checksum, processed_at, hawkish_score, topics) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (url, title, published_date, checksum, now, hawkish_score, topics)
            )
    finally:
        conn.close()

def update_document_sentiment(url: str, hawkish_score: float, topics: str) -> None:
    """Update sentiment metrics for an existing document."""
    conn = get_connection()
    try:
        with DbCursor(conn) as db:
            db.execute(
                "UPDATE ingested_documents SET hawkish_score = ?, topics = ? WHERE url = ?",
                (hawkish_score, topics, url)
            )
    finally:
        conn.close()


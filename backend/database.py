import sqlite3
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("backend", "data", "ck_workspace.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    logger.info(f"Initializing SQLite database at: {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    # 2. Create chat_history table
    cursor.execute("""
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id)")
    
    # 3. Create query_cache table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_cache (
        query_hash TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        response_text TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialization complete.")

def get_query_hash(query: str, doc_ids: Optional[List[str]] = None) -> str:
    """Generate a stable SHA256 hash for query and documents constraint."""
    doc_str = ",".join(sorted(doc_ids)) if doc_ids else ""
    raw_key = f"{query.strip().lower()}:{doc_str}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def create_session(session_id: str, name: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, name, now, now)
        )
        conn.commit()
        return {"id": session_id, "name": name, "created_at": now, "updated_at": now}
    finally:
        conn.close()

def list_sessions() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def delete_session(session_id: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

def add_chat_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    meta_str = json.dumps(metadata) if metadata else None
    try:
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, now, meta_str)
        )
        cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT role, content, timestamp, metadata FROM chat_history WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = cursor.fetchall()
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
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT response_text, metadata FROM query_cache WHERE query_hash = ?",
            (q_hash,)
        )
        row = cursor.fetchone()
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
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    meta_str = json.dumps(metadata) if metadata else None
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO query_cache (query_hash, query, response_text, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (q_hash, query, response_text, meta_str, now)
        )
        conn.commit()
    finally:
        conn.close()

# Initialize DB on import
init_db()

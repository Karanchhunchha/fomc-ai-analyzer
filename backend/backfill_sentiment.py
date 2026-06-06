import os
import logging
import sqlite3
from bs4 import BeautifulSoup
from backend.database import get_connection, update_document_sentiment
from backend.financial_analyzer import analyze_document_sentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backfill():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, hawkish_score FROM ingested_documents WHERE hawkish_score IS NULL OR hawkish_score = 0.0")
    docs = cursor.fetchall()
    
    logger.info(f"Found {len(docs)} documents to backfill sentiment.")
    
    for doc in docs:
        url = doc["url"]
        title = doc["title"]
        
        # Derive file path from URL
        filename = url.split('/')[-1].replace('.htm', '.txt')
        file_path = os.path.join("data", "raw", filename)
        
        # fallback path resolution
        if not os.path.exists(file_path):
            file_path = os.path.join("backend", "data", "raw", filename)
            
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            logger.info(f"Analyzing: {title}")
            result = analyze_document_sentiment(text)
            
            hawkish_score = result["hawkish_score"]
            topics = result["topics"]
            
            update_document_sentiment(url, hawkish_score, topics)
            logger.info(f"Updated {url} -> Score: {hawkish_score}, Topics: {topics}")
        else:
            logger.warning(f"File not found for {url}: {file_path}")

if __name__ == "__main__":
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
    backfill()

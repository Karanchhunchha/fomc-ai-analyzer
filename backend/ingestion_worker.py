import os
import asyncio
import aiohttp
import feedparser
import logging
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Allowed hostnames for document downloads (SSRF protection)
ALLOWED_HOSTS = {"www.federalreserve.gov", "federalreserve.gov"}
from apscheduler.schedulers.blocking import BlockingScheduler

# Import existing pipeline components
from backend.database import is_document_ingested, mark_document_ingested
from backend.document_processor import extract_and_chunk_pdf, extract_and_chunk_txt
from backend.embeddings import generate_embeddings
from backend.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Federal Reserve RSS Feed for all press releases
FED_RSS_URL = "https://www.federalreserve.gov/feeds/press_all.xml"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

async def download_document(url: str, title: str) -> str:
    """Download the document asynchronously using aiohttp."""
    # SSRF protection: only allow downloads from trusted Fed domains
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Blocked download from untrusted host: {parsed.hostname}")
    
    logger.info(f"Downloading new document: {url}")
    
    filename = url.split('/')[-1]
    if not filename.endswith('.pdf') and not filename.endswith('.htm'):
        # Create a safe filename from title if URL doesn't have a good extension
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_title = safe_title.replace(" ", "_").lower()[:50]
        filename = f"{safe_title}.html"
        
    file_path = os.path.join(RAW_DIR, filename)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
            response.raise_for_status()
            content = await response.read()
            
            # If it's HTML, we should extract the text cleanly
            if filename.endswith('.htm') or filename.endswith('.html') or response.content_type == 'text/html':
                soup = BeautifulSoup(content, 'html.parser')
                # Try to find the main content article if it's a Fed press release
                main_div = soup.find('div', {'id': 'article'})
                if main_div:
                    text_content = main_div.get_text(separator='\n', strip=True)
                else:
                    text_content = soup.get_text(separator='\n', strip=True)
                    
                filename = filename.replace('.html', '.txt').replace('.htm', '.txt')
                file_path = os.path.join(RAW_DIR, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
            else:
                # Save as raw (e.g., PDF)
                with open(file_path, "wb") as f:
                    f.write(content)
                    
    return file_path

def process_single_document(file_path: str, meeting_date: str, hawkish_score: float = 0.0, topics: str = "Unknown"):
    """Run the downloaded document through the existing RAG pipeline."""
    logger.info(f"Processing document: {file_path}")
    
    source_name = os.path.basename(file_path)
    
    # 1. Chunking
    if file_path.endswith('.pdf'):
        chunks = extract_and_chunk_pdf(file_path)
    else:
        chunks = extract_and_chunk_txt(file_path)
        
    if not chunks:
        logger.warning(f"No text extracted from {file_path}")
        return
        
    # 2. Embeddings
    logger.info(f"Extracted {len(chunks)} chunks. Generating embeddings...")
    embeddings_data = generate_embeddings(
        chunks=chunks,
        source_document=source_name,
        meeting_date=meeting_date,
        hawkish_score=hawkish_score,
        topics=topics
    )
    
    # 3. Vector DB Ingestion
    logger.info("Ingesting into Vector Store...")
    store = VectorStore()
    store.add_embeddings(embeddings_data)
    
    logger.info(f"Successfully processed and ingested {source_name}")

async def check_rss_feed():
    """Poll the RSS feed, check database for delta updates, and process new items."""
    logger.info(f"Checking RSS feed: {FED_RSS_URL}")
    try:
        feed = feedparser.parse(FED_RSS_URL)
        
        new_items = 0
        for entry in feed.entries:
            url = entry.link
            title = entry.title
            
            # Use published parsed or current time as fallback
            if hasattr(entry, 'published'):
                pub_date = entry.published
            else:
                pub_date = datetime.now().isoformat()
                
            # Check delta
            if is_document_ingested(url):
                continue
                
            logger.info(f"New Document Found! [{title}]")
            
            # Basic checksum of URL and title
            checksum = hashlib.md5(f"{url}{title}".encode("utf-8")).hexdigest()
            
            try:
                # Download
                file_path = await download_document(url, title)
                
                # Try to extract a clean date string for metadata
                # RSS dates are usually like "Wed, 13 Dec 2023 14:00:00 GMT"
                date_str = pub_date[:16] if pub_date else "Unknown"
                
                # Analyze sentiment
                from backend.financial_analyzer import analyze_document_sentiment
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    sentiment = analyze_document_sentiment(text_content)
                    hawkish_score = sentiment["hawkish_score"]
                    topics = sentiment["topics"]
                except Exception as e:
                    logger.error(f"Failed to analyze sentiment for {url}: {e}")
                    hawkish_score = 0.0
                    topics = "Unknown"
                
                # Process into ChromaDB
                process_single_document(file_path, meeting_date=date_str, hawkish_score=hawkish_score, topics=topics)
                
                # Mark as successfully ingested
                mark_document_ingested(url, title, pub_date, checksum, hawkish_score, topics)
                new_items += 1
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                
        if new_items == 0:
            logger.info("No new documents found.")
        else:
            logger.info(f"Ingestion cycle complete. Processed {new_items} new documents.")
            
    except Exception as e:
        logger.error(f"Error checking RSS feed: {e}")

def run_worker_cycle():
    """Synchronous wrapper to run the async feed checker."""
    # Move to root dir if needed
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
    ensure_dirs()
    asyncio.run(check_rss_feed())

if __name__ == "__main__":
    logger.info("Starting Federal Reserve Ingestion Worker...")
    
    # Run once immediately on startup
    run_worker_cycle()
    
    # Schedule to run every 15 minutes
    scheduler = BlockingScheduler()
    scheduler.add_job(run_worker_cycle, 'interval', minutes=15)
    
    logger.info("Scheduler active. Waiting for next cycle...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Ingestion Worker stopped.")

import os
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

def fetch_fomc_minutes(max_downloads=2):
    """
    Scrape the Federal Reserve FOMC calendar for recent meeting minutes and download them.
    """
    logger.info(f"Fetching FOMC calendar from {FOMC_URL}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(FOMC_URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find links that are likely Minutes PDFs
        # Usually they have text "Minutes" and link to an htm or pdf.
        minute_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower()
            if "minutes" in text or "minutes" in href.lower():
                if href.endswith('.pdf') or href.endswith('.htm'):
                    full_url = urljoin(FOMC_URL, href)
                    if full_url not in minute_links:
                        minute_links.append(full_url)
                        
        logger.info(f"Found {len(minute_links)} potential minute links.")
        
        downloaded = 0
        for link in minute_links[:max_downloads]:
            try:
                # If it's an HTM link, we might want to extract text, but let's prefer PDFs if we can find them,
                # or just download the HTML as txt. For simplicity, we download the raw file.
                filename = link.split('/')[-1]
                if not filename.endswith('.pdf') and not filename.endswith('.htm'):
                    filename = f"fomc_minutes_{downloaded}.htm"
                    
                file_path = os.path.join(RAW_DIR, filename)
                
                if os.path.exists(file_path):
                    logger.info(f"File already exists: {filename}")
                    continue
                    
                logger.info(f"Downloading: {link}")
                res = requests.get(link, headers=headers)
                res.raise_for_status()
                
                with open(file_path, "wb") as f:
                    f.write(res.content)
                    
                logger.info(f"Saved to {file_path}")
                downloaded += 1
                time.sleep(1) # Be polite
                
            except Exception as e:
                logger.error(f"Failed to download {link}: {e}")
                
        if downloaded == 0:
            logger.info("No new documents downloaded.")
        else:
            logger.info(f"Successfully downloaded {downloaded} new documents.")
            
    except Exception as e:
        logger.error(f"Failed to scrape FOMC page: {e}")
        logger.info("Falling back to downloading a sample document...")
        _download_fallback_sample()

def _download_fallback_sample():
    """Fallback if scraping fails."""
    sample_url = "https://www.federalreserve.gov/monetarypolicy/files/fomcminutes20240131.pdf"
    file_path = os.path.join(RAW_DIR, "fomcminutes20240131.pdf")
    
    if os.path.exists(file_path):
        logger.info("Fallback sample already exists.")
        return
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(sample_url, headers=headers)
        res.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(res.content)
        logger.info(f"Saved fallback sample to {file_path}")
    except Exception as e:
        logger.error(f"Fallback download also failed: {e}")

if __name__ == "__main__":
    ensure_dirs()
    fetch_fomc_minutes()

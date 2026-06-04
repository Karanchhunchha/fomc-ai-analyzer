import fitz  # PyMuPDF
import re
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Section patterns for FOMC and general Resumes
SECTION_PATTERNS = [
    r'Staff Review of the Economic Situation',
    r'Staff Review of the Financial Situation',
    r'Staff Forecast',
    r'Committee Policy Action',
    r'Participants[\'\u2019] Views',
    r'Developments in Financial Markets',
    r'Experience',
    r'Professional Experience',
    r'Work History',
    r'Employment',
    r'Education',
    r'Academic Background',
    r'Skills',
    r'Technical Skills',
    r'Core Competencies',
    r'Projects',
    r'Academic Projects',
    r'Summary',
    r'Professional Summary',
    r'Objective',
    r'Certifications',
    r'Achievements',
    r'Awards',
    r'Publications'
]

def clean_text_segment(text: str) -> str:
    """Perform basic text cleaning for in-memory processing."""
    if not text:
        return ""
    # Normalize whitespaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove soft hyphens
    text = text.replace('\xad', '')
    # Normalize unicode quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    return text.strip()

def detect_section(text: str, current_section: str) -> str:
    """Detect if a new section starts in the given text block."""
    for pat in SECTION_PATTERNS:
        regex = re.compile(rf'\b{pat}\b', re.IGNORECASE)
        if regex.search(text):
            title_name = pat.replace(r"[\'\u2019]", "'").title()
            if "Participants" in title_name:
                title_name = "Participants' Views"
            return title_name
    return current_section

def extract_and_chunk_pdf(file_path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page using PyMuPDF (fitz).
    Chunks text within each page to preserve page number mapping.
    """
    logger.info(f"Extracting PDF with PyMuPDF: {file_path}")
    doc = fitz.open(file_path)
    chunks = []
    chunk_index = 0
    current_section = "Overview"
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_text = page.get_text("text")
        
        # Clean page text
        cleaned_page_text = clean_text_segment(page_text)
        if not cleaned_page_text:
            continue
            
        # Detect section change on page
        current_section = detect_section(cleaned_page_text, current_section)
        
        # Chunk text on this page
        start = 0
        page_len = len(cleaned_page_text)
        
        while start < page_len:
            end = min(start + chunk_size, page_len)
            
            # Adjust end to sentence end if possible
            if end < page_len:
                # Look for sentence end in the overlap window or nearby
                sub_text = cleaned_page_text[start:end]
                sentence_end = -1
                for m in re.finditer(r'[^.!?]+[.!?]+(?=\s|$)', sub_text):
                    sentence_end = m.end()
                
                if sentence_end != -1 and sentence_end > (chunk_size - overlap):
                    end = start + sentence_end
                else:
                    # Fallback to space boundary
                    last_space = sub_text.rfind(" ")
                    if last_space != -1 and last_space > (chunk_size - overlap):
                        end = start + last_space
                        
            chunk_text = cleaned_page_text[start:end].strip()
            if chunk_text:
                # Generate semantic summary (first sentence of the chunk)
                first_sent_match = re.match(r'^([^.!?]+[.!?]+)', chunk_text)
                if first_sent_match:
                    semantic_summary = first_sent_match.group(1).strip()
                else:
                    semantic_summary = chunk_text[:120].strip() + "..."
                    
                if len(semantic_summary) > 150:
                    semantic_summary = semantic_summary[:147] + "..."
                    
                chunks.append({
                    "text": chunk_text,
                    "section_name": current_section,
                    "semantic_summary": semantic_summary,
                    "chunk_index": chunk_index,
                    "page_number": page_num
                })
                chunk_index += 1
                
            # Move forward with overlap and safety checks to prevent infinite loops
            if end >= page_len:
                break
            next_start = end - overlap
            if next_start <= start or next_start >= end:
                start = end
            else:
                start = next_start
                
    doc.close()
    logger.info(f"PyMuPDF extracted {len(chunks)} chunks from {file_path}")
    return chunks

def extract_and_chunk_txt(file_path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Extract and chunk standard TXT document, defaulting page_number to 1."""
    logger.info(f"Extracting TXT: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="cp1252") as f:
            text = f.read()
            
    cleaned_text = clean_text_segment(text)
    
    # Use standard chunking, but append page_number = 1
    from backend.chunk_text import create_chunks
    base_chunks = create_chunks(cleaned_text, chunk_size=chunk_size, overlap=overlap)
    
    chunks = []
    for item in base_chunks:
        item["page_number"] = 1
        chunks.append(item)
        
    return chunks

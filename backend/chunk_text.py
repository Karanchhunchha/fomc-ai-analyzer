import json
import os
import re

def create_chunks(text, chunk_size=1000, overlap=200):
    """
    Split text into overlapping section-aware chunks.
    Returns a list of dictionaries with metadata (text, section_name, semantic_summary, chunk_index).
    """
    # Common section headings for FOMC and general Resumes
    section_patterns = [
        # FOMC headings
        r'Staff Review of the Economic Situation',
        r'Staff Review of the Financial Situation',
        r'Staff Forecast',
        r'Committee Policy Action',
        r'Participants[\'\u2019] Views',
        r'Developments in Financial Markets',
        # Resume headings
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
    
    sections_by_pos = []
    
    for pat in section_patterns:
        # Match as a phrase with word boundaries (works with newline-free strings)
        regex = re.compile(rf'\b{pat}\b', re.IGNORECASE)
        for m in regex.finditer(text):
            title_name = pat.replace(r"[\'\u2019]", "'").title()
            if "Participants" in title_name:
                title_name = "Participants' Views"
            sections_by_pos.append((m.start(), title_name))
            
    # Sort sections by their starting character position
    sections_by_pos.sort(key=lambda x: x[0])
    
    # Ensure there is an Overview at the start
    if not sections_by_pos or sections_by_pos[0][0] > 0:
        sections_by_pos.insert(0, (0, "Overview"))
        
    def get_section_at_pos(pos):
        active_sec = "Overview"
        for start_pos, name in sections_by_pos:
            if pos >= start_pos:
                active_sec = name
            else:
                break
        return active_sec

    # Split the entire text into sentences to preserve sentence boundaries
    sentence_ends = [m.end() for m in re.finditer(r'[^.!?]+[.!?]+(?=\s|$)', text)]
    
    chunks = []
    start = 0
    prev_end = 0
    text_length = len(text)
    chunk_index = 0
    
    # If no sentence boundaries are found, fallback to standard character split
    if not sentence_ends:
        sentence_ends = [i for i in range(chunk_size, text_length, chunk_size)]
        if text_length not in sentence_ends:
            sentence_ends.append(text_length)
            
    current_sentence_idx = 0
    
    while start < text_length:
        target_end = start + chunk_size
        end = text_length
        
        # Find the last sentence end that fits within target_end
        best_end = -1
        for i in range(current_sentence_idx, len(sentence_ends)):
            s_end = sentence_ends[i]
            if s_end <= target_end:
                if s_end > prev_end:
                    best_end = s_end
                    current_sentence_idx = i
            else:
                break
                
        if best_end != -1:
            end = best_end
        else:
            # Fallback to space boundary
            end = min(target_end, text_length)
            if end < text_length:
                last_space = text.rfind(" ", start, end)
                if last_space != -1 and last_space > start:
                    end = last_space
        
        # Ensure we always make forward progress
        if end <= prev_end:
            end = min(prev_end + chunk_size, text_length)
            
        chunk_text = text[start:end].strip()
        if chunk_text:
            section_name = get_section_at_pos(start)
            
            # Generate semantic summary (first sentence of the chunk)
            first_sent_match = re.match(r'^([^.!?]+[.!?]+)', chunk_text)
            if first_sent_match:
                semantic_summary = first_sent_match.group(1).strip()
            else:
                semantic_summary = chunk_text[:120].strip() + "..."
                
            # If summary is too long, truncate it
            if len(semantic_summary) > 150:
                semantic_summary = semantic_summary[:147] + "..."
                
            chunks.append({
                "text": chunk_text,
                "section_name": section_name,
                "semantic_summary": semantic_summary,
                "chunk_index": chunk_index
            })
            chunk_index += 1
            
        if end >= text_length:
            break
            
        # Move the start position forward, accounting for overlap with safety checks
        prev_end = end
        next_start = end - overlap
        if next_start <= start or next_start >= end:
            start = end
        else:
            start = next_start
    
    return chunks

def process_and_save_chunks(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    chunks = create_chunks(text, chunk_size=1000, overlap=200)
    
    # Save as JSON for easy consumption by the embedding step
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4, ensure_ascii=False)
        
    print(f"Created {len(chunks)} chunks.")
    print(f"Saved chunks to {output_path}")

if __name__ == "__main__":
    INPUT_FILE = "data/processed/fomc_text_cleaned.txt"
    OUTPUT_FILE = "data/chunks/fomc_chunks.json"
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    if os.path.exists(INPUT_FILE):
        process_and_save_chunks(INPUT_FILE, OUTPUT_FILE)
    else:
        print(f"Input file not found: {INPUT_FILE}")

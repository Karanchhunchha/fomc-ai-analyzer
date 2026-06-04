import re

def clean_raw_text(text: str) -> str:
    # Split text into lines to process line by line
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
            
        # Filter out common header/footer patterns
        # Example footers: "Minutes of the Federal Open Market Committee    15" 
        # or "14    January 27–28, 2026"
        if re.search(r'^Minutes of the Federal Open Market Committee\s*\d*$', line, re.IGNORECASE):
            continue
            
        if re.search(r'^\d+\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d+–\d+,\s*\d+$', line):
            continue
            
        if re.search(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d+–\d+,\s*\d+\s*\d+$', line):
            continue

        # Append valid lines
        cleaned_lines.append(line)
        
    # Join the lines back together with a single space
    cleaned_text = " ".join(cleaned_lines)
    
    # Normalize excessive spacing
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def clean_fomc_text(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    cleaned_text = clean_raw_text(text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
        
    print(f"Cleaned text saved to {output_path}")
    print(f"Total characters: {len(cleaned_text)}")

if __name__ == "__main__":
    INPUT_FILE = "data/fomc_text.txt"
    OUTPUT_FILE = "data/processed/fomc_text_cleaned.txt"
    
    import os
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    clean_fomc_text(INPUT_FILE, OUTPUT_FILE)

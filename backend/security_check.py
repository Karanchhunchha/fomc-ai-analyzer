import os
import re
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Basic patterns to look for. (sk-, AIza, Bearer, etc.)
PATTERNS = [
    r'(?i)gemini_api_key\s*=\s*[\'"][^\'"]+[\'"]',
    r'AIza[0-9A-Za-z-_]{35}',
    r'sk-[a-zA-Z0-9]{48}',
]

def check_file(filepath):
    """Scan a single file for sensitive patterns."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in PATTERNS:
                if re.search(pattern, content):
                    logger.error(f"SECURITY ALERT: Potential secret found in {filepath} matching pattern: {pattern}")
                    return True
    except Exception as e:
        logger.warning(f"Could not read {filepath}: {e}")
    return False

def scan_project(root_dir="."):
    """Scan the project directory, skipping gitignored/irrelevant folders."""
    exclude_dirs = {'.git', 'venv', '__pycache__', 'chroma_db', 'node_modules', 'logs', '.next'}
    found_secrets = False
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for file in filenames:
            # Skip binary and environment files
            if file.endswith(('.pyc', '.pdf', '.png', '.jpg', '.env')):
                continue
            
            filepath = os.path.join(dirpath, file)
            if check_file(filepath):
                found_secrets = True
                
    if found_secrets:
        logger.error("CRITICAL: Secrets found during scan. DO NOT COMMIT.")
        sys.exit(1)
    else:
        logger.info("Security check passed. No exposed secrets found.")

if __name__ == "__main__":
    scan_project()

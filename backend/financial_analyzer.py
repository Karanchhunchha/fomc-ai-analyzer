import logging
import json
from google.generativeai import GenerativeModel
from backend.config import config

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    def __init__(self):
        self.model = GenerativeModel(config.GEMINI_MODEL_NAME)
        self.use_openrouter = bool(config.OPENROUTER_API_KEY)
        if self.use_openrouter:
            from openai import OpenAI
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=config.OPENROUTER_API_KEY,
                max_retries=0
            )
        
    def analyze_text(self, text: str) -> dict:
        """
        Analyzes a piece of financial text to determine its Hawkish/Dovish sentiment
        and extracts key macroeconomic topics.
        """
        # Truncate text if it's too long for a quick analysis
        if len(text) > 10000:
            text = text[:10000] + "..."
            
        prompt = f"""
        You are a specialized Federal Reserve macroeconomic analyst.
        Analyze the following text and extract:
        1. A "hawkish_score": A float between -1.0 (extremely dovish/accommodative) and +1.0 (extremely hawkish/restrictive). If neutral, 0.0.
        2. "topics": A comma-separated string of the main macroeconomic topics discussed (e.g., "Inflation, Labor Market, Interest Rates").
        
        Respond ONLY with a valid JSON object in this exact format, with no markdown formatting or extra text:
        {{
            "hawkish_score": 0.5,
            "topics": "Inflation, Monetary Policy"
        }}
        
        Text to analyze:
        {text}
        """
        
        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                # Clean up the response in case it has markdown code blocks
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                    
                result = json.loads(raw_text.strip())
                return {
                    "hawkish_score": float(result.get("hawkish_score", 0.0)),
                    "topics": str(result.get("topics", ""))
                }
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
                    if attempt < max_retries - 1:
                        logger.warning(f"Gemini Rate limited. Waiting {retry_delay}s...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                logger.error(f"Gemini failed: {e}. Trying OpenRouter fallback...")
                break
                
        # Try OpenRouter if Gemini failed
        if self.use_openrouter:
            try:
                logger.info(f"Calling OpenRouter fallback ({config.OPENROUTER_MODEL_NAME}) for sentiment analysis...")
                response = self.openrouter_client.chat.completions.create(
                    model=config.OPENROUTER_MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}]
                )
                raw_text = response.choices[0].message.content.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                    
                result = json.loads(raw_text.strip())
                return {
                    "hawkish_score": float(result.get("hawkish_score", 0.0)),
                    "topics": str(result.get("topics", ""))
                }
            except Exception as or_err:
                logger.error(f"OpenRouter sentiment analysis fallback failed: {or_err}")
                
        return {"hawkish_score": 0.0, "topics": "Unknown"}

analyzer = FinancialAnalyzer()

def analyze_document_sentiment(text: str) -> dict:
    return analyzer.analyze_text(text)

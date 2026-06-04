# AI-assisted: Prompt generation templates, LLM model fallbacks, 429 rate limit backoff retry loops, 
# and SSE streaming event payload formatters were co-developed with AI assistance.

import os
import logging
import json
import time
import re
from datetime import datetime
from google.generativeai import configure, GenerativeModel
from backend.semantic_search import SemanticSearcher
from backend.config import config

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.searcher = SemanticSearcher()
        self.use_openrouter = bool(config.OPENROUTER_API_KEY)
        
        logger.info(f"Initializing Gemini client with model: {config.GEMINI_MODEL_NAME}")
        configure(api_key=config.GEMINI_API_KEY)
        self.model = GenerativeModel(config.GEMINI_MODEL_NAME)
        
        if self.use_openrouter:
            logger.info("Initializing OpenRouter fallback client")
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=config.OPENROUTER_API_KEY,
            )
        
    def classify_mode(self, query):
        """Classify the user's query intent into one of 5 modes."""
        query_lower = query.lower()
        
        # Resume Mode detection
        resume_keywords = ["resume", "cv", "candidate", "skills", "experience", "hire", "recruiter", "job", "education", "applicant", "work history", "specializes", "portfolio"]
        if any(w in query_lower for w in resume_keywords):
            return "resume"
            
        # Compare Mode detection
        compare_keywords = ["compare", "contrast", "difference", "versus", "vs", "similarities", "comparison"]
        if any(w in query_lower for w in compare_keywords):
            return "compare"
            
        # Summary Mode detection
        summary_keywords = ["summarize", "summary", "overview", "tldr", "tl;dr", "brief", "compress", "key takeaways", "synopsis"]
        if any(w in query_lower for w in summary_keywords):
            return "summary"
            
        # Study Mode detection
        study_keywords = ["explain", "notes", "tutorial", "how to", "what is", "why did", "study", "concept", "academic", "teach me"]
        if any(w in query_lower for w in study_keywords):
            return "study"
            
        return "research"

    def generate_prompt(self, query, search_results, mode):
        """Build a mode-specific strict prompt forcing the LLM to only use the provided context with metadata."""
        context_blocks = []
        for i, text in enumerate(search_results['text']):
            meta = search_results['metadata'][i]
            source = meta.get('source_document', 'Unknown')
            date = meta.get('meeting_date', 'Unknown')
            section = meta.get('section_name', 'Overview')
            summary = meta.get('semantic_summary', '')
            context_blocks.append(
                f"Excerpt {i+1} [Source: {source} | Date: {date} | Section: {section} | Summary: {summary}]:\n{text}"
            )
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        # Mode-specific instructions and identity injection
        mode_instructions = {
            "research": """You are "CK Intelligence" — a premium financial and macroeconomic research analyst.
Your task is to write a cohesive, analytical answer synthesizing the provided excerpts to answer the user's question.
- Keep your tone objective, professional, and precise, resembling senior central bank watchers or institutional research analysts.
- Structure your answer with clear headings or analytical paragraphs. Focus on policy stances, economic data trends, and consensus outlooks.""",
            
            "resume": """You are "CK Resume Intelligence" — a senior technical recruiter and talent advisor.
Your task is to analyze candidate information in the excerpts to provide a clear talent profile assessment.
- Highlight technical stacks, coding skills, backend languages, experience level, and key project metrics.
- Keep your tone professional, structured, and focused on evaluation, candidate strengths, and areas of fit.
- Present skills and work highlights in a clear, organized format suitable for hiring managers.""",
            
            "study": """You are "CK Study Companion" — an expert academic tutor and educator.
Your task is to explain the concepts or information in the excerpts in an educational, easy-to-understand format.
- Break down complex technical terminology or economic terms (like quantitative easing, inflation persistence, rate curves).
- Use clear bullet points, brief definitions, and logical explanations to form comprehensive study notes.
- Keep your tone clear, encouraging, and highly informative.""",
            
            "summary": """You are "CK Summarizer" — an executive research synthesizer.
Your task is to provide a highly compressed, high-level executive summary of the provided excerpts.
- Condense the main facts, decisions, and outcomes into key takeaways.
- Avoid unnecessary detail; present a compact, strategic summary with bullet points highlighting the core messages.
- Keep the summary brief, clear, and actionable.""",
            
            "compare": """You are "CK Comparative Intelligence" — a senior policy advisor and strategic analyst.
Your task is to compare and contrast the information, documents, candidates, or policy stances mentioned across the excerpts.
- Clearly identify similarities and key differences (e.g., changes in inflation outlook between meeting dates, differences in technical skills between resumes).
- Structure your answer as a comparative analysis with side-by-side notes or comparative bullet points.
- Highlight evolution over time or relative strengths."""
        }
        
        selected_instruction = mode_instructions.get(mode, mode_instructions["research"])
        
        prompt = f"""{selected_instruction}

CRITICAL INSTRUCTIONS:
- You MUST answer ONLY using the facts and information directly found in the provided context excerpts.
- If the retrieved context does not contain relevant information to confidently answer the question, you MUST return exactly: "The retrieved documents do not contain enough relevant information to answer this confidently."
- Do NOT speculate, extrapolate, or use outside technical, economic, or general knowledge.
- Write a natural, flowing response. Avoid repeating chunks verbatim or sounding like a robotic list.
- For statements of fact or claims, cite the corresponding Excerpt number(s) (e.g., "[Excerpt 1]"). Do not spam citations; cite only where direct, concrete evidence supports the claim.

CONTEXT EXCERPTS:
{context_str}

USER QUESTION:
{query}

ANSWER:"""
        return prompt
        
    def query_stream(self, user_query, top_k=config.TOP_K_RETRIEVAL, mode="auto"):
        """
        Execute the full RAG pipeline as a generator for Server-Sent Events (SSE).
        """
        start_time = time.time()
        
        # Helper to format SSE safely
        def sse(event, data):
            # Always JSON encode to handle newlines in text chunks cleanly
            encoded_data = json.dumps(data)
            return f"event: {event}\ndata: {encoded_data}\n\n"
            
        yield sse("status", "Analyzing query intent...")
        
        # Determine query mode
        if not mode or mode == "auto":
            mode = self.classify_mode(user_query)
        logger.info(f"RAG Pipeline processing query in mode '{mode}': '{user_query}'")
        
        yield sse("status", "Retrieving semantic evidence...")
        
        # 1. Retrieve semantic context
        search_results = self.searcher.search(user_query, top_k=top_k)
        
        # 2. Extract similarity scores and check threshold
        has_results = bool(search_results['text'])
        highest_score = search_results['similarity_scores'][0] if has_results else 0.0
        
        fallback_response = "The retrieved documents do not contain enough relevant information to answer this confidently."
        
        # Apply mode and file-aware confidence thresholds
        threshold = config.MIN_SIMILARITY_THRESHOLD
        if search_results.get('file_scoped'):
            threshold = 0.10  # Extremely low threshold for explicit file-scoped query
            logger.info(f"File-scoped search active. Lowering similarity threshold to {threshold}")
        elif mode in ["resume", "summary"]:
            threshold = 0.20
            
        fallback_triggered = False
        if not has_results or highest_score < threshold:
            fallback_triggered = True
            logger.warning(f"Confidence threshold not met. Returning fallback.")
            yield sse("status", "Confidence threshold not met.")
            yield sse("chunk", fallback_response)
            yield sse("done", {"citations": [], "sources": [], "confidence": 0.0})
            return
            
        yield sse("status", "Reranking relevant context...")
        
        unique_citations = list(set(search_results['citations']))
        doc_ids = sorted(unique_citations)
        
        # --- Cache Interception ---
        from backend.database import get_cached_query, cache_query
        try:
            cached_res = get_cached_query(user_query, doc_ids)
            if cached_res:
                logger.info("Cache hit! Streaming cached response.")
                yield sse("status", "Retrieving cached answer...")
                
                yield sse("metadata", {
                    "citations": cached_res["metadata"].get("citations", unique_citations),
                    "sources": cached_res["metadata"].get("sources", search_results['metadata']),
                    "similarity_scores": cached_res["metadata"].get("similarity_scores", search_results['similarity_scores']),
                    "confidence": cached_res["metadata"].get("confidence", float(highest_score))
                })
                
                # Stream words to UI with a slight delay
                cached_text = cached_res["response_text"]
                words = re.split(r'(\s+)', cached_text)
                for word in words:
                    if word:
                        yield sse("chunk", word)
                        time.sleep(0.005) # 5ms delay
                
                yield sse("done", {"status": "success", "cached": True})
                return
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
        # --------------------------
        
        # Send metadata early so UI can show evidence cards
        yield sse("metadata", {
            "citations": unique_citations,
            "sources": search_results['metadata'],
            "similarity_scores": search_results['similarity_scores'],
            "confidence": float(highest_score)
        })
        
        # 3. Construct prompt
        prompt = self.generate_prompt(user_query, search_results, mode)
        
        yield sse("status", "Generating grounded answer...")
        
        # 4. Generate response using Gemini 1.5 Flash primarily, fallback to OpenRouter
        success = False
        answer = ""
        max_retries = 3
        retry_delay = 4 # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Calling Gemini API stream (attempt {attempt})...")
                response = self.model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        answer += chunk.text
                        yield sse("chunk", chunk.text)
                success = True
                break
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str
                
                if is_rate_limit and attempt < max_retries:
                    if attempt == 1:
                        yield sse("status", "CK Intelligence is temporarily waiting for model availability...")
                    else:
                        yield sse("status", "Retrying grounded synthesis...")
                    logger.warning(f"Gemini API rate limited (429). Waiting {retry_delay}s to retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Gemini generation failed: {e}. Trying OpenRouter fallback...")
                    break
                    
        if not success:
            if self.use_openrouter:
                for or_attempt in range(1, 3):
                    try:
                        yield sse("status", f"Connecting to OpenRouter Llama... (Attempt {or_attempt})")
                        fallback_model = config.OPENROUTER_MODEL_NAME
                        response = self.client.chat.completions.create(
                            model=fallback_model,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True
                        )
                        for chunk in response:
                            if chunk.choices[0].delta.content:
                                text = chunk.choices[0].delta.content
                                answer += text
                                yield sse("chunk", text)
                        success = True
                        break
                    except Exception as e2:
                        err_str = str(e2).lower()
                        logger.error(f"OpenRouter fallback failed on attempt {or_attempt}: {e2}")
                        if "429" in err_str and or_attempt < 2:
                            yield sse("status", "Kimi is rate-limited upstream. Waiting to retry...")
                            time.sleep(5)
                        else:
                            # Forward the error message to the UI
                            yield sse("status", f"OpenRouter Error: {str(e2)}")
                            answer += f"\n\n[OpenRouter API Error: {str(e2)}]"
                            break
            else:
                logger.error("No OpenRouter fallback configured.")
                
        if not success:
            err_msg = "\n[An error occurred while generating the response.]"
            yield sse("chunk", err_msg)
            answer += err_msg
            
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log to file
        query_log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "query": user_query,
            "mode": mode,
            "highest_similarity_score": float(highest_score),
            "threshold": threshold,
            "fallback_triggered": fallback_triggered,
            "execution_time_ms": execution_time_ms,
            "confidence": float(highest_score),
            "answer": answer
        }
        self._write_log(query_log_data)
        
        # Cache successful generated answers
        if success and not fallback_triggered:
            try:
                cache_query(
                    query=user_query,
                    doc_ids=doc_ids,
                    response_text=answer,
                    metadata={
                        "citations": unique_citations,
                        "sources": search_results['metadata'],
                        "similarity_scores": search_results['similarity_scores'],
                        "confidence": float(highest_score)
                    }
                )
                logger.info("Response successfully cached.")
            except Exception as e:
                logger.error(f"Failed to cache response: {e}")
                
        yield sse("done", {"status": "success"})

    def _write_log(self, log_data):
        """Append log to JSON lines file."""
        try:
            os.makedirs(config.LOGS_DIR, exist_ok=True)
            with open(config.QUERY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            logger.info(f"Query logged to {config.QUERY_LOG_FILE}")
        except Exception as e:
            logger.error(f"Failed to write query log: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Needs GEMINI_API_KEY set in environment
    if os.path.basename(os.getcwd()) == "backend":
        os.chdir("..")
        
    rag = RAGPipeline()
    res = rag.query("What was the monetary policy outlook?")
    print("\n--- RAG Response ---")
    print(res["answer"])
    print(f"\nCitations: {res['citations']}")
    print(f"Confidence: {res['confidence']}")

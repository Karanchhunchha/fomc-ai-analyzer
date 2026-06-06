import logging
from typing import Dict, List, Any
from backend.agent_orchestrator import BaseAgent
from backend.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class FOMCAgent(BaseAgent):
    """
    Specialized agent for FOMC document analysis.
    Handles queries about Federal Reserve policy, meeting minutes, and monetary policy decisions.
    """
    
    def __init__(self):
        super().__init__(
            name="fomc_agent",
            description="Specialized agent for FOMC document analysis and monetary policy research"
        )
        self.rag_pipeline = None
        logger.info("FOMC Agent initialized")
    
    def _get_rag_pipeline(self):
        """Lazy load RAG pipeline."""
        if self.rag_pipeline is None:
            self.rag_pipeline = RAGPipeline()
        return self.rag_pipeline
    
    def get_capabilities(self) -> List[str]:
        return [
            "fomc_meeting_analysis",
            "policy_stance_tracking",
            "interest_rate_analysis",
            "inflation_outlook",
            "labor_market_analysis",
            "economic_forecast_interpretation",
            "cross_meeting_comparison",
            "sentiment_analysis"
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process FOMC-related queries using the RAG pipeline.
        
        Args:
            input_data: Dictionary containing:
                - query: User query string
                - mode: Query mode (auto, research, summary, compare, study)
                - top_k: Number of results to retrieve
                
        Returns:
            Dictionary containing analysis results
        """
        query = input_data.get("query", "")
        mode = input_data.get("mode", "auto")
        top_k = input_data.get("top_k", 5)
        
        if not query:
            return {
                "error": "No query provided",
                "status": "failed"
            }
        
        logger.info(f"FOMC Agent processing query: '{query}' in mode '{mode}'")
        
        try:
            # Use RAG pipeline to get answer
            rag = self._get_rag_pipeline()
            stream = rag.query_stream(query, top_k=top_k, mode=mode)
            
            # Collect streaming response
            answer = ""
            metadata = {}
            for sse_chunk in stream:
                if "event: chunk" in sse_chunk:
                    try:
                        import json
                        lines = sse_chunk.split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                chunk_data = json.loads(line[6:])
                                if isinstance(chunk_data, str):
                                    answer += chunk_data
                    except Exception as e:
                        logger.warning(f"Error parsing SSE chunk: {e}")
                elif "event: done" in sse_chunk:
                    try:
                        import json
                        lines = sse_chunk.split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                metadata = json.loads(line[6:])
                    except Exception:
                        pass
            
            # Get additional context for analysis
            search_results = rag.searcher.search(query, top_k=top_k)
            
            return {
                "answer": answer,
                "query": query,
                "mode": mode,
                "sources": search_results.get("citations", []),
                "similarity_scores": search_results.get("similarity_scores", []),
                "metadata": metadata,
                "agent_used": self.name,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"FOMC Agent failed to process query: {e}")
            return {
                "error": str(e),
                "query": query,
                "agent_used": self.name,
                "status": "failed"
            }
    
    def analyze_policy_stance(self, meeting_date: str = None) -> Dict[str, Any]:
        """
        Analyze the policy stance from FOMC meetings.
        
        Args:
            meeting_date: Optional specific meeting date to analyze
            
        Returns:
            Dictionary containing policy stance analysis
        """
        query = f"What was the policy stance at the FOMC meeting"
        if meeting_date:
            query += f" on {meeting_date}"
        else:
            query += " in the most recent meeting"
        
        return self.process({
            "query": query,
            "mode": "research",
            "top_k": 5
        })
    
    def compare_meetings(self, date1: str, date2: str) -> Dict[str, Any]:
        """
        Compare policy stances between two FOMC meetings.
        
        Args:
            date1: First meeting date
            date2: Second meeting date
            
        Returns:
            Dictionary containing comparison analysis
        """
        query = f"Compare the FOMC policy decisions and economic outlook between {date1} and {date2}"
        
        return self.process({
            "query": query,
            "mode": "compare",
            "top_k": 10
        })
    
    def track_inflation_narrative(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Track the evolution of inflation narrative across FOMC meetings.
        
        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
            
        Returns:
            Dictionary containing inflation narrative analysis
        """
        query = "How has the FOMC's view on inflation evolved across recent meetings"
        if start_date and end_date:
            query += f" between {start_date} and {end_date}"
        
        return self.process({
            "query": query,
            "mode": "research",
            "top_k": 8
        })

import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)

# Mapping of conversational terms to formal FOMC/central banking terminology
QUERY_MAPPINGS = {
    # Interest rate terms
    "cut interest rates": ["lower the federal funds rate", "reduce the target range", "easing monetary policy", "rate reduction"],
    "raise interest rates": ["increase the federal funds rate", "tighten monetary policy", "rate hike", "policy tightening"],
    "interest rates": ["federal funds rate", "policy rate", "target range", "monetary policy stance"],
    
    # Labor market terms
    "labor market": ["employment", "labor market conditions", "job gains", "labor demand", "unemployment rate", "payroll employment"],
    "jobs": ["employment", "payroll employment", "job gains", "labor market"],
    "unemployment": ["unemployment rate", "labor market slack", "employment conditions"],
    
    # Inflation terms
    "inflation": ["inflation pressures", "price stability", "inflation expectations", "price levels", "pce inflation", "cpi"],
    "prices": ["inflation", "price pressures", "price stability"],
    
    # Economic growth terms
    "economy": ["economic activity", "economic growth", "economic outlook", "gdp growth"],
    "growth": ["economic growth", "economic activity", "expansion"],
    
    # Policy stance terms
    "hawkish": ["restrictive stance", "tightening", "policy firming"],
    "dovish": ["accommodative stance", "easing", "policy accommodation"],
    
    # Risk terms
    "risks": ["economic risks", "downside risks", "upside risks", "uncertainties"],
}

# FOMC-specific terminology patterns
FOMC_PATTERNS = [
    r"cut interest rates",
    r"raise interest rates", 
    r"lower rates",
    r"hike rates",
    r"labor market",
    r"job market",
    r"inflation",
    r"economic growth",
    r"monetary policy",
    r"federal funds rate",
]

def expand_query_with_synonyms(query: str) -> str:
    """
    Expand a conversational query with formal FOMC terminology.
    
    Args:
        query: Original user query
        
    Returns:
        Expanded query with additional formal terminology
    """
    query_lower = query.lower()
    expanded_terms = []
    
    # Check each mapping
    for conversational_term, formal_terms in QUERY_MAPPINGS.items():
        if conversational_term in query_lower:
            # Add formal terms to the expansion
            expanded_terms.extend(formal_terms)
    
    # If no mappings found, return original query
    if not expanded_terms:
        return query
    
    # Construct expanded query
    expanded_query = f"{query} {' '.join(expanded_terms)}"
    logger.info(f"Query expanded: '{query}' -> '{expanded_query}'")
    return expanded_query

def rewrite_query_to_formal(query: str) -> str:
    """
    Rewrite conversational query to formal policy language.
    
    Args:
        query: Original conversational query
        
    Returns:
        Rewritten query in formal policy language
    """
    query_lower = query.lower()
    
    # Direct replacements for common patterns
    replacements = {
        "cut interest rates": "reduce the target range for the federal funds rate",
        "raise interest rates": "increase the target range for the federal funds rate",
        "lower rates": "reduce the federal funds rate",
        "hike rates": "increase the federal funds rate",
        "cut rates": "reduce the federal funds rate",
        "labor market": "labor market conditions",
        "job market": "labor market conditions",
        "jobs": "employment",
    }
    
    rewritten = query_lower
    for conversational, formal in replacements.items():
        if conversational in rewritten:
            rewritten = rewritten.replace(conversational, formal)
            logger.info(f"Query rewritten: '{query}' -> '{rewritten}'")
            break
    
    return rewritten

def enhance_query_for_search(query: str) -> str:
    """
    Main entry point for query enhancement.
    Combines synonym expansion with formal rewriting.
    
    Args:
        query: Original user query
        
    Returns:
        Enhanced query optimized for FOMC document search
    """
    # Step 1: Rewrite to formal language
    formal_query = rewrite_query_to_formal(query)
    
    # Step 2: Expand with synonyms
    expanded_query = expand_query_with_synonyms(formal_query)
    
    return expanded_query

# FOMC-specific keyword boost terms for hybrid search
FOMC_BOOST_TERMS = [
    "federal funds rate",
    "target range",
    "monetary policy",
    "inflation",
    "employment",
    "labor market",
    "economic outlook",
    "policy stance",
    "committee",
    "participants",
]

def get_query_boost_terms(query: str) -> List[str]:
    """
    Extract boost terms from query for hybrid search weighting.
    
    Args:
        query: User query
        
    Returns:
        List of terms that should receive higher weight in search
    """
    boost_terms = []
    query_lower = query.lower()
    
    for term in FOMC_BOOST_TERMS:
        if term in query_lower:
            boost_terms.append(term)
    
    return boost_terms

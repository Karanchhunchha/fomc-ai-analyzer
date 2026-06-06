import math
import re
from collections import Counter
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class BM25:
    """
    BM25 ranking algorithm for keyword-based search.
    Combines term frequency (TF), inverse document frequency (IDF), and document length normalization.
    """
    
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with a corpus of documents.
        
        Args:
            corpus: List of document strings
            k1: Term frequency saturation parameter (typically 1.2-2.0)
            b: Length normalization parameter (typically 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.corpus_size = len(corpus)
        
        # Preprocess corpus
        self.doc_lengths = [len(doc.split()) for doc in corpus]
        self.avg_doc_length = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Build vocabulary and document frequencies
        self.doc_freqs = []
        self.idf = {}
        self._build_index()
        
    def _build_index(self):
        """Build inverted index and compute IDF scores."""
        # Count document frequencies for each term
        vocab = set()
        for doc in self.corpus:
            tokens = self._tokenize(doc)
            vocab.update(tokens)
        
        # Compute IDF for each term
        for term in vocab:
            # Count how many documents contain this term
            containing_docs = sum(1 for doc in self.corpus if term in self._tokenize(doc))
            # IDF = log((N - df + 0.5) / (df + 0.5))
            idf = math.log((self.corpus_size - containing_docs + 0.5) / (containing_docs + 0.5) + 1)
            self.idf[term] = idf
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric characters."""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def score(self, query: str, doc_index: int) -> float:
        """
        Compute BM25 score for a query against a specific document.
        
        Args:
            query: Search query string
            doc_index: Index of document in corpus
            
        Returns:
            BM25 score
        """
        if doc_index >= len(self.corpus):
            return 0.0
            
        doc = self.corpus[doc_index]
        doc_length = self.doc_lengths[doc_index]
        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(doc)
        
        # Count term frequency in document
        tf_counts = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term in tf_counts:
                tf = tf_counts[term]
                # BM25 formula
                idf = self.idf.get(term, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search corpus with BM25 ranking.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (doc_index, score) tuples sorted by score descending
        """
        scores = [(i, self.score(query, i)) for i in range(self.corpus_size)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def combine_scores(vector_scores: List[float], bm25_scores: List[float], 
                   alpha: float = 0.7) -> List[float]:
    """
    Combine vector similarity scores with BM25 scores using linear interpolation.
    
    Args:
        vector_scores: List of vector similarity scores (0-1 range)
        bm25_scores: List of BM25 scores (unnormalized)
        alpha: Weight for vector scores (0-1), bm25 gets (1-alpha)
        
    Returns:
        List of combined scores
    """
    # Normalize BM25 scores to 0-1 range
    if bm25_scores:
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        normalized_bm25 = [s / max_bm25 for s in bm25_scores]
    else:
        normalized_bm25 = [0.0] * len(vector_scores)
    
    # Combine scores
    combined = [alpha * v + (1 - alpha) * b for v, b in zip(vector_scores, normalized_bm25)]
    return combined

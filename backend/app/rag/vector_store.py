import math
import re
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    In-Memory Vector Database with TF-IDF / Token Embedding similarity calculation,
    metadata filtering, and source citation extraction.
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text into lowercase words."""
        return re.findall(r'\w+', text.lower())

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        tf = {}
        total = len(tokens) or 1
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for token in tf:
            tf[token] = tf[token] / total
        return tf

    def _build_index(self):
        """Build IDF weights across stored document chunks."""
        N = len(self.documents)
        if N == 0:
            return
        
        doc_freq = {}
        vocab = set()
        
        for doc in self.documents:
            tokens = set(doc["tokens"])
            vocab.update(tokens)
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab))}
        self.idf = {term: math.log((N + 1) / (df + 1)) + 1.0 for term, df in doc_freq.items()}
        
        # Compute vector representation for each document
        for doc in self.documents:
            tf = self._compute_tf(doc["tokens"])
            vector = {}
            norm_sq = 0.0
            for term, freq in tf.items():
                weight = freq * self.idf.get(term, 1.0)
                vector[term] = weight
                norm_sq += weight * weight
            doc["vector"] = vector
            doc["magnitude"] = math.sqrt(norm_sq) or 1.0

    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        Add documents to store.
        Each doc dict expects:
        - text: str
        - id: str/int
        - metadata: dict (section_number, title, fine, points, category, jurisdiction)
        """
        for doc in docs:
            tokens = self.tokenize(doc["text"])
            self.documents.append({
                "id": doc.get("id", len(self.documents) + 1),
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "tokens": tokens,
                "vector": {},
                "magnitude": 1.0
            })
        self._build_index()

    def search(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search vector store using cosine similarity and return top matching chunks with scores & metadata.
        """
        if not self.documents:
            return []

        query_tokens = self.tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        
        query_vec = {}
        q_norm_sq = 0.0
        for term, freq in query_tf.items():
            if term in self.idf:
                weight = freq * self.idf[term]
                query_vec[term] = weight
                q_norm_sq += weight * weight
        q_magnitude = math.sqrt(q_norm_sq) or 1.0

        results = []
        for doc in self.documents:
            # Metadata filtering if requested
            if category_filter and doc["metadata"].get("category") != category_filter:
                continue

            # Dot product
            dot_product = 0.0
            doc_vec = doc["vector"]
            for term, weight in query_vec.items():
                if term in doc_vec:
                    dot_product += weight * doc_vec[term]

            score = dot_product / (q_magnitude * doc["magnitude"])
            
            # Boost score if query keywords directly match title or section number
            title = doc["metadata"].get("title", "").lower()
            section = doc["metadata"].get("section_number", "").lower()
            for token in query_tokens:
                if len(token) > 3 and token in title:
                    score += 0.15
                if token in section:
                    score += 0.25

            if score > 0.01:
                results.append({
                    "score": round(score, 4),
                    "id": doc["id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"]
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# Global Vector Store Instance
vector_store = VectorStore()

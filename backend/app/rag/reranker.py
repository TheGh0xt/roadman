from typing import List, Dict, Any

class Reranker:
    """
    Reranker module to score and re-rank candidate documents retrieved from vector store
    based on exact statutory keyword matches, penal code coverage, and semantic alignment.
    """
    @staticmethod
    def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        query_lower = query.lower()
        scored_candidates = []

        for item in candidates:
            base_score = item.get("score", 0.5)
            text = item.get("text", "").lower()
            metadata = item.get("metadata", {})
            
            penalty_bonus = 0.0
            # If query explicitly asks about fines or points, prioritize chunks that contain fine/points metadata
            if any(w in query_lower for w in ["fine", "cost", "point", "penalty", "ticket", "prison", "ban", "jail"]):
                if metadata.get("fine") or metadata.get("points"):
                    penalty_bonus += 0.2
                if "fine" in text or "points" in text or "penalty" in text:
                    penalty_bonus += 0.15

            # If user asks specific rule e.g. "red light", "phone", "speeding", check title match
            title = metadata.get("title", "").lower()
            if any(w in title for w in query_lower.split() if len(w) > 3):
                penalty_bonus += 0.1

            final_score = base_score + penalty_bonus
            item_copy = dict(item)
            item_copy["rerank_score"] = round(final_score, 4)
            scored_candidates.append(item_copy)

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]

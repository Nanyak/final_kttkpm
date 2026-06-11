"""
Hybrid RAG Retriever — FAISS semantic search + Neo4j graph context.

Retrieval flow:
  1. FAISS        → semantically similar products for the text query
  2. Neo4j graph  → products related to user's interaction history
                    + SIMILAR-edge expansion of top FAISS hits
  3. Merge        → weighted combination, re-ranked
  4. Context      → formatted product descriptions for LLM prompt
"""
import logging
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines FAISS semantic retrieval with Neo4j graph signals for
    richer product context and recommendation scores.

    Parameters
    ----------
    faiss_weight : float
        Weight applied to FAISS cosine similarity scores (default 0.6).
    graph_weight : float
        Weight applied to Neo4j interaction / collaborative scores (default 0.4).
    """

    def __init__(self, faiss_weight: float = 0.6, graph_weight: float = 0.4):
        self.faiss_weight = faiss_weight
        self.graph_weight = graph_weight

    # ── core retrieval ────────────────────────────────────────────────────────

    def retrieve(
        self,
        query:   str,
        user_id: Optional[int] = None,
        top_k:   int = 20,
    ) -> List[Tuple[int, float]]:
        """
        Return [(product_id, hybrid_score)] sorted descending.

        Combines:
        - FAISS semantic search on `query`
        - Neo4j graph scores for `user_id`  (if provided)
        - SIMILAR-edge expansion of top FAISS hits
        """
        from rag.retriever import get_retriever
        from graph.queries import get_user_graph_scores, get_product_context_pids

        faiss_scores: Dict[int, float] = {}
        if query:
            try:
                retriever = get_retriever()
                if not retriever:
                    raise RuntimeError('FAISS index is not available')
                faiss_hits   = retriever.search(query, top_k=top_k)
                faiss_scores = {pid: score for pid, score in faiss_hits}

                # Expand: SIMILAR edges from top FAISS products
                top_faiss_pids = [pid for pid, _ in faiss_hits[:5]]
                for pid, score in get_product_context_pids(top_faiss_pids, limit=top_k):
                    if pid not in faiss_scores:
                        faiss_scores[pid] = score * 0.5   # discounted expansion
            except Exception as exc:
                logger.warning('FAISS retrieval failed: %s', exc)

        graph_scores: Dict[int, float] = {}
        if user_id:
            try:
                graph_scores = get_user_graph_scores(user_id, limit=top_k)
            except Exception as exc:
                logger.warning('Graph retrieval failed: %s', exc)

        # Normalise each source to [0, 1] before merging
        faiss_scores = _normalise(faiss_scores)
        graph_scores = _normalise(graph_scores)

        all_pids = set(faiss_scores) | set(graph_scores)
        merged: Dict[int, float] = {}
        for pid in all_pids:
            fs = faiss_scores.get(pid, 0.0)
            gs = graph_scores.get(pid, 0.0)
            # When only one source fires, scale down to avoid over-promotion
            if fs == 0.0 or gs == 0.0:
                merged[pid] = max(fs * self.faiss_weight, gs * self.graph_weight)
            else:
                merged[pid] = self.faiss_weight * fs + self.graph_weight * gs

        ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    # ── context building ──────────────────────────────────────────────────────

    def build_context(self, hits: List[Tuple[int, float]]) -> str:
        """
        Format retrieved products for injection into the LLM prompt.
        """
        from rag.retriever import get_retriever
        retriever = get_retriever()
        lines     = []
        for rank, (pid, score) in enumerate(hits, 1):
            text = retriever.get_text(pid) if retriever else f'Product {pid}'
            lines.append(f'{rank}. [ID:{pid}] {text}  (score:{score:.3f})')
        return '\n'.join(lines)

    def get_context(
        self,
        query:   str,
        user_id: Optional[int] = None,
        top_k:   int = 5,
    ) -> str:
        """
        Return a formatted product context string for injection into the LLM prompt.
        """
        return self.build_context(self.retrieve(query, user_id=user_id, top_k=top_k))

    def get_context_and_scores(
        self,
        query:   str,
        user_id: Optional[int] = None,
        top_k:   int = 10,
    ) -> Tuple[str, Dict[int, float]]:
        """
        Returns (context_string, {product_id: score}) in one call.
        Used by the chatbot view.
        """
        hits      = self.retrieve(query, user_id=user_id, top_k=top_k)
        scores    = {pid: score for pid, score in hits}
        context   = self.build_context(hits[:min(5, top_k)])
        return context, scores

    def get_scores_only(
        self,
        query: str,
        top_k: int = 20,
        user_id: Optional[int] = None,
    ) -> Dict[int, float]:
        """
        Normalised RAG scores. Includes graph context when user_id is provided.
        Used by ai_service via the /api/rag/scores/ endpoint.
        """
        hits = self.retrieve(query=query, user_id=user_id, top_k=top_k)
        scores = {pid: score for pid, score in hits}
        return _normalise(scores)


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalise(scores: Dict[int, float]) -> Dict[int, float]:
    if not scores:
        return {}
    mx = max(scores.values())
    return {k: v / mx for k, v in scores.items()} if mx > 0 else scores


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRetriever:
    from django.conf import settings
    return HybridRetriever(
        faiss_weight=settings.FAISS_WEIGHT,
        graph_weight=settings.GRAPH_WEIGHT,
    )

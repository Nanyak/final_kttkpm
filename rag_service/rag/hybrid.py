"""
Hybrid RAG Retriever — dense FAISS + sparse TF-IDF + Neo4j graph context.

Retrieval flow:
  1. FAISS        → semantically similar products for the text query
  2. TF-IDF       → exact lexical matches for names, brands, and model numbers
  3. Neo4j graph  → products related to user's interaction history
                    + SIMILAR-edge expansion of top retrieval hits
  4. RRF          → rank-fuse dense + sparse retrieval
  5. Merge        → combine retrieval score with graph score, re-ranked
  6. Context      → formatted product descriptions for LLM prompt
"""
import logging
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines FAISS semantic retrieval, TF-IDF lexical retrieval, and Neo4j
    graph signals for richer product context and recommendation scores.

    Parameters
    ----------
    dense_weight : float
        Weight applied to FAISS cosine similarity scores.
    sparse_weight : float
        Weight applied to TF-IDF lexical ranks.
    graph_weight : float
        Weight applied to Neo4j interaction / collaborative scores.
    rrf_k : int
        Reciprocal Rank Fusion constant. Higher values dampen rank differences.
    """

    def __init__(
        self,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.25,
        graph_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.graph_weight = graph_weight
        self.rrf_k = rrf_k

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
        - TF-IDF sparse search on `query`
        - Neo4j graph scores for `user_id`  (if provided)
        - SIMILAR-edge expansion of top dense/sparse hits
        """
        from rag.retriever import get_retriever
        from graph.queries import get_user_graph_scores, get_product_context_pids
        from rag.query_intent import filter_relevant_hits, parse_query_intent

        retrieval_scores: Dict[int, float] = {}
        dense_hits: List[Tuple[int, float]] = []
        sparse_hits: List[Tuple[int, float]] = []
        intent = parse_query_intent(query or '')
        if query:
            try:
                retriever = get_retriever()
                if not retriever:
                    raise RuntimeError('retrieval indexes are not available')
                dense_hits = retriever.search(query, top_k=top_k)
                sparse_hits = retriever.sparse_search(query, top_k=top_k)
                retrieval_scores = _weighted_rrf(
                    rankings=[
                        (dense_hits, self.dense_weight),
                        (sparse_hits, self.sparse_weight),
                    ],
                    k=self.rrf_k,
                )

                # Expand: SIMILAR edges from top dense and sparse products.
                top_seed_pids = []
                for pid, _ in dense_hits[:3] + sparse_hits[:3]:
                    if pid not in top_seed_pids:
                        top_seed_pids.append(pid)
                expansion_hits = get_product_context_pids(top_seed_pids, limit=top_k)
                expansion_scores = _normalise({pid: score for pid, score in expansion_hits})
                for pid, score in expansion_scores.items():
                    retrieval_scores.setdefault(pid, score * 0.25)
            except Exception as exc:
                logger.warning('Dense/sparse retrieval failed: %s', exc)

        graph_scores: Dict[int, float] = {}
        if user_id:
            try:
                graph_scores = get_user_graph_scores(user_id, limit=top_k)
            except Exception as exc:
                logger.warning('Graph retrieval failed: %s', exc)

        # RRF yields retrieval ranks; graph scores are independently normalised.
        retrieval_scores = _normalise(retrieval_scores)
        graph_scores = _normalise(graph_scores)

        all_pids = set(retrieval_scores) | set(graph_scores)
        merged: Dict[int, float] = {}
        retrieval_weight = self.dense_weight + self.sparse_weight
        total_weight = retrieval_weight + self.graph_weight
        if total_weight <= 0:
            total_weight = 1.0

        for pid in all_pids:
            rs = retrieval_scores.get(pid, 0.0)
            gs = graph_scores.get(pid, 0.0)
            merged[pid] = (
                retrieval_weight * rs +
                self.graph_weight * gs
            ) / total_weight

        ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        if intent.has_constraints:
            ranked = self._apply_query_constraints(ranked, intent)
        return ranked[:top_k]

    def _apply_query_constraints(self, hits, intent):
        from rag.query_intent import filter_relevant_hits
        from rag.retriever import get_retriever

        try:
            retriever = get_retriever()
            if not retriever:
                return hits
            metadata = {pid: retriever.get_metadata(pid) for pid, _ in hits}
            constrained = filter_relevant_hits(hits, metadata, intent)
            return constrained or hits
        except Exception as exc:
            logger.warning('Query constraint ranking failed: %s', exc)
            return hits

    # ── context building ──────────────────────────────────────────────────────

    def build_context(self, hits: List[Tuple[int, float]]) -> str:
        """
        Format retrieved products for injection into the LLM prompt.
        """
        from rag.retriever import get_retriever
        retriever = get_retriever()
        lines     = []
        for rank, (pid, score) in enumerate(hits, 1):
            metadata = retriever.get_metadata(pid) if retriever else {}
            if metadata:
                price = metadata.get('price')
                price_text = f"{price:,.0f} VND" if isinstance(price, (int, float)) else ''
                details = [
                    metadata.get('name') or f'Product {pid}',
                    metadata.get('category_root'),
                    ' > '.join(metadata.get('category_path') or []),
                    metadata.get('category'),
                    price_text,
                    metadata.get('brand'),
                    metadata.get('model_number'),
                    metadata.get('author'),
                    metadata.get('genre'),
                    metadata.get('language'),
                    metadata.get('audience'),
                    metadata.get('season'),
                    metadata.get('material'),
                    metadata.get('connectivity'),
                    metadata.get('warranty_period'),
                    metadata.get('description'),
                ]
                text = ' | '.join(str(item) for item in details if item)
            else:
                text = retriever.get_text(pid) if retriever else f'Product {pid}'
            lines.append(f'{rank}. [ID:{pid}] {text}')
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

        Context = optional KB block (policies/FAQs) + product block.
        """
        hits      = self.retrieve(query, user_id=user_id, top_k=top_k)
        scores    = {pid: score for pid, score in hits}
        product_context = self.build_context(hits[:min(5, top_k)])

        # Prepend relevant knowledge-base entries when found.
        kb_context = ''
        try:
            from rag.kb_retriever import get_kb_retriever
            kb = get_kb_retriever()
            if kb:
                kb_hits = kb.search(query)
                if kb_hits:
                    kb_context = kb.format_context(kb_hits)
        except Exception as exc:
            logger.warning('KB retrieval failed: %s', exc)

        if kb_context and product_context:
            context = kb_context + '\n\n[Product Results]\n' + product_context
        elif kb_context:
            context = kb_context
        else:
            context = product_context

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


def _weighted_rrf(rankings: List[Tuple[List[Tuple[int, float]], float]], k: int = 60) -> Dict[int, float]:
    """
    Weighted Reciprocal Rank Fusion.

    Input scores are ignored; only rank positions matter. This keeps dense
    cosine scores and sparse TF-IDF scores from needing artificial calibration.
    """
    fused: Dict[int, float] = {}
    k = max(1, k)
    for hits, weight in rankings:
        if weight <= 0:
            continue
        for rank, (pid, _) in enumerate(hits, start=1):
            fused[pid] = fused.get(pid, 0.0) + weight / (k + rank)
    return fused


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRetriever:
    from django.conf import settings
    return HybridRetriever(
        dense_weight=settings.DENSE_WEIGHT,
        sparse_weight=settings.SPARSE_WEIGHT,
        graph_weight=settings.GRAPH_WEIGHT,
        rrf_k=settings.RRF_K,
    )

"""
Hybrid Recommendation Engine

final_score = w1 * sequence_model_score + w2 * graph_score + w3 * rag_score

Each source returns a {product_id: normalised_float} dict.
Products are unioned; missing sources contribute 0.
"""
from typing import Any, Dict, List, Optional

from django.conf import settings

from .sequence_model_service import get_sequence_model_scores
from .graph_service          import get_graph_scores
from .rag_client             import get_rag_scores


def recommend(
    user_id: int,
    query: Optional[str] = None,
    top_n: int = None,
    w1: float = None,
    w2: float = None,
    w3: float = None,
) -> List[Dict[str, Any]]:
    """
    Returns top-N products with their hybrid score and source breakdown.

    Parameters
    ----------
    user_id : int
    query   : optional text query (used for RAG; falls back to user history keywords)
    top_n   : number of results (default: settings.TOP_N)
    w1/w2/w3: weight overrides (default: sequence-model/graph/RAG weights)
    """
    top_n = top_n or settings.TOP_N
    w1    = w1    if w1 is not None else settings.SEQUENCE_MODEL_WEIGHT
    w2    = w2    if w2 is not None else settings.GRAPH_WEIGHT
    w3    = w3    if w3 is not None else settings.RAG_WEIGHT

    # normalise weights so they sum to 1
    total = w1 + w2 + w3
    if total > 0:
        w1, w2, w3 = w1 / total, w2 / total, w3 / total

    # ── fetch scores from each source ────────────────────────
    rag_query = query or _build_user_query(user_id)

    sequence_scores = get_sequence_model_scores(user_id, top_k=top_n * 3)
    graph_scores    = get_graph_scores(user_id, top_k=top_n * 3)
    rag_scores      = get_rag_scores(rag_query, top_k=top_n * 3, user_id=user_id)

    # ── union all product ids ─────────────────────────────────
    all_pids = set(sequence_scores) | set(graph_scores) | set(rag_scores)

    ranked = []
    for pid in all_pids:
        ss = sequence_scores.get(pid, 0.0)
        gs = graph_scores.get(pid, 0.0)
        rs = rag_scores.get(pid, 0.0)
        final = w1 * ss + w2 * gs + w3 * rs
        ranked.append({
            'product_id':            pid,
            'final_score':           round(final, 4),
            'sequence_model_score':  round(ss, 4),
            'graph_score':           round(gs, 4),
            'rag_score':             round(rs, 4),
            # Deprecated alias kept so older clients do not break.
            'lstm_score':            round(ss, 4),
        })

    ranked.sort(key=lambda x: x['final_score'], reverse=True)
    top = ranked[:top_n]

    # ── enrich with product metadata ──────────────────────────
    return _enrich(top)


def _build_user_query(user_id: int) -> str:
    """Derive a text query from the user's most-interacted product categories."""
    from apps.behavior.models import UserBehavior
    recent = (UserBehavior.objects
              .filter(user_id=user_id)
              .order_by('-timestamp')
              .select_related('product')
              .values_list('product__category', 'product__name')[:10])
    if not recent:
        return ''
    categories = list({cat for cat, _ in recent if cat})
    names      = [name for _, name in recent][:3]
    return ' '.join(categories + names)


def _enrich(items: List[Dict]) -> List[Dict]:
    from apps.behavior.models import Product
    pids     = [i['product_id'] for i in items]
    products = {p.product_id: p
                for p in Product.objects.filter(product_id__in=pids)}
    for item in items:
        p = products.get(item['product_id'])
        if p:
            item['name']        = p.name
            item['category']    = p.category
            item['price']       = p.price
            item['description'] = p.description
        else:
            item['name']        = f"Product {item['product_id']}"
            item['category']    = ''
            item['price']       = 0.0
            item['description'] = ''
    return items

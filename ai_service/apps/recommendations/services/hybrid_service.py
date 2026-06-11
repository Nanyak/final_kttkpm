"""
Hybrid Recommendation Engine

final_score = w1 * sequence_model_score + w2 * graph_score + w3 * rag_score

Each source returns a {product_id: normalised_float} dict.
Products are unioned; missing sources contribute 0.

Cold-start: when a user has no history the engine falls back to site-wide
popularity scores so the response is never empty.
"""
from typing import Any, Dict, List, Optional

from django.conf import settings

from .sequence_model_service import get_sequence_model_scores
from .graph_service          import get_graph_scores
from .rag_client             import get_rag_scores

_SCORE_THRESHOLD = 0.05   # minimum score to label a source as "contributing"
_MAX_PER_CATEGORY = 3     # max items from one category before diversity kicks in


def recommend(
    user_id: int,
    query: Optional[str] = None,
    top_n: int = None,
    w1: float = None,
    w2: float = None,
    w3: float = None,
) -> List[Dict[str, Any]]:
    """
    Returns top-N products with hybrid score, source breakdown, and reason label.

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

    total = w1 + w2 + w3
    if total > 0:
        w1, w2, w3 = w1 / total, w2 / total, w3 / total

    # ── fetch scores from each source ────────────────────────
    rag_query = query or _build_user_query(user_id)

    sequence_scores = get_sequence_model_scores(user_id, top_k=top_n * 3)
    graph_scores    = get_graph_scores(user_id, top_k=top_n * 3)
    rag_scores      = get_rag_scores(rag_query, top_k=top_n * 3, user_id=user_id)

    # ── cold-start fallback ───────────────────────────────────
    # When the user has no interaction history and the graph is empty,
    # substitute site-wide popularity so we always return something useful.
    is_cold_start = not sequence_scores and not graph_scores
    if is_cold_start:
        sequence_scores = _get_popular_scores(top_n * 3)

    # ── union and score all candidates ───────────────────────
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
            'lstm_score':            round(ss, 4),   # deprecated alias
            '_ss': ss, '_gs': gs, '_rs': rs,         # raw floats for reason labelling
            '_cold_start': is_cold_start,
        })

    ranked.sort(key=lambda x: x['final_score'], reverse=True)

    # ── enrich, then diversify ────────────────────────────────
    # Fetch 2× candidates so diversity filter still returns top_n results.
    candidates = _enrich(ranked[:top_n * 2])
    top = _diversify(candidates, top_n)

    # ── attach human-readable reason and strip internal keys ─
    for item in top:
        item['reason'] = _reason(item)
        item.pop('_ss', None)
        item.pop('_gs', None)
        item.pop('_rs', None)
        item.pop('_cold_start', None)

    return top


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_user_query(user_id: int) -> str:
    """Derive a text query from the user's most-interacted product categories."""
    from apps.behavior.models import UserBehavior
    recent = list(
        UserBehavior.objects
        .filter(user_id=user_id)
        .order_by('-timestamp')
        .select_related('product')
        .values_list('product__category', 'product__name')[:10]
    )
    if not recent:
        return ''
    categories = list({cat for cat, _ in recent if cat})
    names      = [name for _, name in recent if name][:3]
    return ' '.join(categories + names)


def _get_popular_scores(top_k: int) -> Dict[int, float]:
    """Site-wide popularity fallback: normalised weighted interaction counts."""
    from django.db.models import Sum
    from apps.behavior.models import UserBehavior

    qs = (
        UserBehavior.objects
        .values('product__product_id')
        .annotate(total_weight=Sum('weight'))
        .order_by('-total_weight')[:top_k]
    )
    scores = {
        row['product__product_id']: float(row['total_weight'])
        for row in qs
        if row['product__product_id'] is not None
    }
    if scores:
        mx = max(scores.values())
        if mx > 0:
            scores = {k: v / mx for k, v in scores.items()}
    return scores


def _enrich(items: List[Dict]) -> List[Dict]:
    from apps.behavior.models import Product
    pids     = [i['product_id'] for i in items]
    products = {p.product_id: p for p in Product.objects.filter(product_id__in=pids)}
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


def _diversify(items: List[Dict], top_n: int) -> List[Dict]:
    """
    Re-rank to avoid more than _MAX_PER_CATEGORY results from any single category.
    Items demoted by diversity are appended at the end if slots remain.
    """
    category_counts: Dict[str, int] = {}
    result, overflow = [], []
    for item in items:
        cat = item.get('category') or 'unknown'
        if category_counts.get(cat, 0) < _MAX_PER_CATEGORY:
            result.append(item)
            category_counts[cat] = category_counts.get(cat, 0) + 1
        else:
            overflow.append(item)
        if len(result) >= top_n:
            break

    for item in overflow:
        if len(result) >= top_n:
            break
        result.append(item)

    return result


def _reason(item: Dict) -> str:
    """Return a short, user-facing explanation for why this product was recommended."""
    if item.get('_cold_start'):
        return 'Popular with shoppers'
    ss = item.get('_ss', 0.0)
    gs = item.get('_gs', 0.0)
    rs = item.get('_rs', 0.0)
    # Pick the dominant source
    sources = [('sequence', ss), ('graph', gs), ('rag', rs)]
    dominant = max(sources, key=lambda x: x[1])
    if dominant[1] < _SCORE_THRESHOLD:
        return 'Recommended for you'
    if dominant[0] == 'sequence':
        return 'Based on your browsing history'
    if dominant[0] == 'graph':
        return 'Customers like you also viewed'
    return 'Matches your interests'

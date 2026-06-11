"""
Neo4j queries used by the RAG hybrid retriever.
Reads the same graph written by ai_service's setup_graph / behavior recording.
"""
from typing import Dict, List, Tuple

from .client import get_driver

# ── Context enrichment queries ────────────────────────────────────────────────

RELATED_PRODUCTS_QUERY = """
    MATCH (p:Product {product_id: $pid})-[r:SIMILAR]->(s:Product)
    RETURN s.product_id AS product_id, r.score AS score
    ORDER BY score DESC
    LIMIT $limit
"""

USER_INTERACTION_QUERY = """
    MATCH (u:User {user_id: $uid})-[r]->(p:Product)
    WHERE type(r) IN ['VIEW', 'CLICK', 'ADD_CART', 'BUY']
    WITH p,
         SUM(CASE type(r)
               WHEN 'BUY'      THEN 4.0
               WHEN 'ADD_CART' THEN 3.0
               WHEN 'CLICK'    THEN 2.0
               ELSE                 1.0
             END * r.count) AS interaction_score
    ORDER BY interaction_score DESC
    LIMIT 5
    MATCH (p)-[:SIMILAR]->(rec:Product)
    WHERE NOT EXISTS {
        MATCH (u2:User {user_id: $uid})-[:BUY]->(rec)
    }
    RETURN DISTINCT rec.product_id AS product_id,
           MAX(interaction_score)  AS score
    ORDER BY score DESC
    LIMIT $limit
"""

COLLAB_QUERY = """
    MATCH (u:User {user_id: $uid})-[:BUY|ADD_CART]->(p:Product)
          <-[:BUY|ADD_CART]-(other:User)
          -[:BUY|ADD_CART]->(rec:Product)
    WHERE NOT EXISTS {
        MATCH (u2:User {user_id: $uid})-[]->(rec)
    }
    RETURN rec.product_id AS product_id,
           COUNT(DISTINCT other) AS score
    ORDER BY score DESC
    LIMIT $limit
"""

CATEGORY_PRODUCTS_QUERY = """
    MATCH (p:Product {product_id: $pid})
    MATCH (related:Product)
    WHERE related.category = p.category AND related.product_id <> $pid
    RETURN related.product_id AS product_id, 0.5 AS score
    LIMIT $limit
"""


def get_user_graph_scores(user_id: int, limit: int = 20) -> Dict[int, float]:
    """
    Combine interaction-based and collaborative-filtering scores
    from the Neo4j graph for a given user.
    Returns {product_id: normalised_score}.
    """
    scores: Dict[int, float] = {}
    try:
        with get_driver().session() as session:
            for pid, score in session.run(USER_INTERACTION_QUERY, uid=user_id, limit=limit):
                scores[pid] = scores.get(pid, 0.0) + float(score) * 0.6

            for pid, score in session.run(COLLAB_QUERY, uid=user_id, limit=limit):
                scores[pid] = scores.get(pid, 0.0) + float(score) * 0.4
    except Exception:
        return {}

    if scores:
        mx = max(scores.values())
        if mx > 0:
            scores = {k: v / mx for k, v in scores.items()}

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit])


def get_product_context_pids(product_ids: List[int], limit: int = 10) -> List[Tuple[int, float]]:
    """
    Given a list of seed product_ids (e.g. from FAISS hits),
    expand via SIMILAR edges to find related products.
    Returns [(product_id, score)].
    """
    expanded: Dict[int, float] = {}
    try:
        with get_driver().session() as session:
            for pid in product_ids[:5]:
                for rec_pid, score in session.run(RELATED_PRODUCTS_QUERY, pid=pid, limit=limit):
                    expanded[rec_pid] = max(expanded.get(rec_pid, 0.0), float(score))
    except Exception:
        return []

    return sorted(expanded.items(), key=lambda x: x[1], reverse=True)[:limit]

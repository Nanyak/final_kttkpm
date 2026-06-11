"""
Graph inference service — wraps graph.queries with graceful fallback.
"""
from typing import Dict

from graph.queries import combine_graph_scores


def get_graph_scores(user_id: int, top_k: int = 20) -> Dict[int, float]:
    """
    Returns {product_id: normalised_score} from the Knowledge Graph.
    Falls back to empty dict if Neo4j is unavailable.
    """
    try:
        return combine_graph_scores(user_id, limit=top_k)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning('Graph query failed: %s', exc)
        return {}

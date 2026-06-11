"""
RAG scores proxy — calls rag_service over HTTP to get RAG / graph-RAG
scores for the hybrid recommendation formula.

  hybrid = w_dl * dl_score + w_graph * graph_score + w_rag * rag_score

Falls back to empty dict (graceful degradation) if rag_service is
unreachable or returns an error.
"""
import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 3.0   # seconds — keep low so a slow rag_service doesn't block recs


def get_rag_scores(query: str, top_k: int = 20, user_id: int = None) -> Dict[int, float]:
    """
    Returns {product_id: normalised_score} from rag_service retrieval.
    """
    from django.conf import settings

    url = f'{settings.RAG_SERVICE_URL}/api/rag/scores/'
    try:
        resp = requests.get(
            url,
            params={
                'query': query or '',
                'top_k': top_k,
                **({'user_id': user_id} if user_id is not None else {}),
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get('scores', {})
        return {int(k): float(v) for k, v in raw.items()}
    except requests.exceptions.Timeout:
        logger.warning('RAG service timed out (query=%r)', query)
        return {}
    except Exception as exc:
        logger.warning('RAG service unavailable: %s', exc)
        return {}

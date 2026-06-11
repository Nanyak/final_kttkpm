"""
Chatbot endpoint — Hybrid RAG (FAISS + Neo4j) + LLM.

POST /api/ai/chatbot/
{
    "query":   "tai nghe chong on",
    "user_id": 42,           # optional — enables graph-personalised context
    "history": [             # optional — last N turns for multi-turn dialogue
        {"role": "user",      "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}

Flow
----
1. HybridRetriever.get_context_and_scores()
      FAISS semantic search  (query → similar products)
   +  Neo4j graph context    (user history → related products)
   →  merged context string + {product_id: score}

2. LLM generation (OpenAI / fallback template)
      system prompt + product context + conversation history + user query
   →  natural-language answer

3. Enrich product scores with metadata and return ranked list
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from rag.hybrid    import get_hybrid_retriever
from rag.generator import generate_answer, generate_fallback


class ChatbotView(APIView):

    def post(self, request):
        query   = request.data.get('query', '').strip()
        user_id = request.data.get('user_id')
        history = request.data.get('history', [])

        if not query:
            return Response(
                {'error': 'query is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if history and not isinstance(history, list):
            return Response(
                {'error': 'history must be a list'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 1. Hybrid retrieval ──────────────────────────────────
        try:
            uid = int(user_id) if user_id not in (None, '') else None
        except (TypeError, ValueError):
            return Response(
                {'error': 'user_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        retriever = get_hybrid_retriever()
        context, product_scores = retriever.get_context_and_scores(
            query=query, user_id=uid, top_k=settings.TOP_K,
        )

        # ── 2. LLM generation ────────────────────────────────────
        api_key = settings.OPENAI_API_KEY
        if api_key:
            try:
                answer = generate_answer(
                    query=query, context=context,
                    api_key=api_key, model=settings.OPENAI_MODEL,
                    history=history,
                )
            except Exception:
                answer = generate_fallback(query, context)
        else:
            answer = generate_fallback(query, context)

        # ── 3. Enrich top products with metadata ─────────────────
        recommended = _enrich(product_scores, top_n=5)

        return Response({
            'query':        query,
            'answer':       answer,
            'context_used': context,
            'recommended':  recommended,
        })


def _enrich(scores: dict, top_n: int = 5) -> list:
    """
    Attach product metadata to the top-N scored products by calling
    product_service API.  Falls back to bare product_id if the call fails.
    """
    import logging
    from django.conf import settings
    from rag.product_api import fetch_products_by_ids

    top_pids   = sorted(scores, key=scores.get, reverse=True)[:top_n]
    meta: dict = {}

    try:
        from rag.retriever import get_retriever
        retriever = get_retriever()
        if retriever:
            meta = {pid: retriever.get_metadata(pid) for pid in top_pids}
    except Exception:
        meta = {}

    try:
        meta.update(fetch_products_by_ids(settings.PRODUCT_SERVICE_URL, top_pids))
    except Exception as exc:
        logging.getLogger(__name__).warning('Could not enrich from product_service: %s', exc)

    result = []
    for pid in top_pids:
        p = meta.get(pid, {})
        result.append({
            'product_id':   pid,
            'hybrid_score': round(scores[pid], 4),
            'name':         p.get('name',          f'Product {pid}'),
            'category':     p.get('category_name') or p.get('category', ''),
            'price':        p.get('base_price') or p.get('price', 0.0),
            'description':  p.get('description',   ''),
        })
    return result

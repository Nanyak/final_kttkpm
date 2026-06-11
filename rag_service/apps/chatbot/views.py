"""
Chatbot endpoint — Hybrid RAG (dense FAISS + sparse TF-IDF + Neo4j) + LLM.

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
   +  TF-IDF lexical search  (query → exact product/brand/model matches)
   +  short-session user history
   +  Neo4j graph context    (user history → related products)
   →  merged context string + {product_id: score}

2. LLM generation (OpenAI / fallback template)
      system prompt + product context + conversation history + user query
   →  natural-language answer

3. Enrich product scores with metadata and return ranked list
"""
import re
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
        retrieval_query = _build_session_retrieval_query(query, history)
        context, product_scores = retriever.get_context_and_scores(
            query=retrieval_query, user_id=uid, top_k=settings.TOP_K,
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
                answer = generate_fallback(query, context, history=history)
        else:
            answer = generate_fallback(query, context, history=history)

        # ── 3. Build recommended cards from the same context lines shown in the answer ──
        q_lower = query.lower()
        wants_cheaper = any(kw in q_lower for kw in (
            'cheaper', 'less expensive', 'lower price', 'more affordable', 'budget',
            'rẻ hơn', 're hon', 'giá thấp hơn', 'ít tiền hơn',
        ))
        display_pids = _pids_from_context(context, wants_cheaper=wants_cheaper, top_n=3)
        recommended  = _enrich_ordered(display_pids, product_scores)

        return Response({
            'query':        query,
            'answer':       answer,
            'context_used': context,
            'recommended':  recommended,
        })


def _pids_from_context(context: str, wants_cheaper: bool = False, top_n: int = 3) -> list:
    """
    Extract product IDs from context in display order.
    Deduplicates by pid, sorts by price ascending when wants_cheaper.
    This ensures card order matches the text answer exactly.
    """
    items = []
    seen  = set()
    for line in context.split('\n'):
        m = re.search(r'\[ID:(\d+)\]', line)
        if not m:
            continue
        pid = int(m.group(1))
        if pid in seen:
            continue
        seen.add(pid)
        price = float('inf')
        if wants_cheaper:
            pm = re.search(r'(\d[\d,]+)\s*VND', line, re.IGNORECASE)
            if pm:
                try:
                    price = float(pm.group(1).replace(',', ''))
                except ValueError:
                    pass
        items.append((pid, price))

    if wants_cheaper:
        items.sort(key=lambda x: x[1])

    return [pid for pid, _ in items[:top_n]]


def _enrich_ordered(pids: list, scores: dict) -> list:
    """
    Attach metadata to a specific ordered list of product IDs.
    Cards are returned in the same order as pids.
    """
    import logging
    from rag.product_api import fetch_products_by_ids

    meta: dict = {}
    try:
        from rag.retriever import get_retriever
        retriever = get_retriever()
        if retriever:
            meta = {pid: retriever.get_metadata(pid) for pid in pids}
    except Exception:
        meta = {}

    try:
        meta.update(fetch_products_by_ids(settings.PRODUCT_SERVICE_URL, pids))
    except Exception as exc:
        logging.getLogger(__name__).warning('Could not enrich from product_service: %s', exc)

    result = []
    for pid in pids:
        p = meta.get(pid, {})
        result.append({
            'product_id':   pid,
            'hybrid_score': round(scores.get(pid, 0.0), 4),
            'name':         p.get('name',          f'Product {pid}'),
            'category':     p.get('category_name') or p.get('category', ''),
            'price':        p.get('base_price') or p.get('price', 0.0),
            'description':  p.get('description',   ''),
        })
    return result


def _build_session_retrieval_query(query: str, history: list, max_turns: int = 3) -> str:
    """
    Build short-term retrieval memory from recent user turns.

    The frontend already sends per-widget message history. The backend remains
    stateless, but retrieval should still see recent constraints like
    "winter jacket" when the next message says "for women".
    """
    if not history:
        return query

    user_turns = []
    for item in history:
        if not isinstance(item, dict) or item.get('role') != 'user':
            continue
        content = str(item.get('content', '')).strip()
        if content:
            user_turns.append(content[:180])

    recent = user_turns[-max_turns:]
    if not recent:
        return query
    return ' '.join(recent + [query])

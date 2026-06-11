"""
RAG scores endpoint — called internally by ai_service to get
RAG / graph-RAG scores for the hybrid recommendation formula:

    hybrid = rrf(dense_rank, sparse_rank) + graph_score

GET /api/rag/scores/?query=<str>&top_k=<int>[&user_id=<int>]
Returns: {"scores": {"product_id": score, ...}}

This endpoint is NOT exposed to the public frontend — it is an
internal service-to-service call from ai_service.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rag.hybrid import get_hybrid_retriever


class RAGScoresView(APIView):

    def get(self, request):
        query = request.GET.get('query', '').strip()
        try:
            top_k = max(1, min(int(request.GET.get('top_k', 20)), 100))
        except (TypeError, ValueError):
            return Response({'error': 'top_k must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.GET.get('user_id')
        try:
            user_id = int(user_id) if user_id not in (None, '') else None
        except (TypeError, ValueError):
            return Response({'error': 'user_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        if not query and user_id is None:
            return Response({'scores': {}})

        retriever = get_hybrid_retriever()
        scores    = retriever.get_scores_only(query=query, user_id=user_id, top_k=top_k)

        # JSON keys must be strings
        return Response({'scores': {str(k): v for k, v in scores.items()}})

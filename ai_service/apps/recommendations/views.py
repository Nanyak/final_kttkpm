from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.hybrid_service import recommend


class RecommendView(APIView):
    """
    GET /api/ai/recommend/?user_id=<int>[&query=<str>&top_n=<int>&w1=&w2=&w3=]

    Returns personalised product recommendations using:
      active sequence model + Knowledge Graph + RAG (semantic)
    combined as: final_score = w1*sequence_model + w2*graph + w3*rag
    """

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        query = request.query_params.get('query', '')
        top_n = int(request.query_params.get('top_n', 0)) or None

        # optional weight overrides
        def _w(key):
            v = request.query_params.get(key)
            return float(v) if v else None

        results = recommend(
            user_id=user_id,
            query=query or None,
            top_n=top_n,
            w1=_w('w1'), w2=_w('w2'), w3=_w('w3'),
        )

        return Response({
            'user_id':  user_id,
            'count':    len(results),
            'results':  results,
        })

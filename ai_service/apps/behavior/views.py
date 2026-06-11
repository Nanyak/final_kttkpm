from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserBehaviorSerializer


class TrackBehaviorView(APIView):
    """POST /api/ai/track — ingest a single user behaviour event."""

    def post(self, request):
        ser = UserBehaviorSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        behavior = ser.save()
        return Response(
            {'message': 'Behavior tracked', 'behavior_id': behavior.id},
            status=status.HTTP_201_CREATED,
        )


class TrackBehaviorBatchView(APIView):
    """POST /api/ai/track/batch/ — ingest multiple behaviour events at once."""

    _MAX_BATCH = 500

    def post(self, request):
        events = request.data
        if not isinstance(events, list):
            return Response(
                {'error': 'Request body must be a JSON array of events'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not events:
            return Response({'saved': 0, 'errors': []})
        if len(events) > self._MAX_BATCH:
            return Response(
                {'error': f'Batch size exceeds maximum of {self._MAX_BATCH}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_ids, errors = [], []
        for i, event in enumerate(events):
            ser = UserBehaviorSerializer(data=event)
            if ser.is_valid():
                saved_ids.append(ser.save().id)
            else:
                errors.append({'index': i, 'errors': ser.errors})

        http_status = status.HTTP_201_CREATED if saved_ids else status.HTTP_400_BAD_REQUEST
        return Response(
            {'saved': len(saved_ids), 'behavior_ids': saved_ids, 'errors': errors},
            status=http_status,
        )


class UserBehaviorHistoryView(APIView):
    """GET /api/ai/track/history/?user_id=<int>[&limit=<int>] — recent events for a user."""

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = min(int(request.query_params.get('limit', 50)), 200)
        except (TypeError, ValueError):
            limit = 50

        from .models import UserBehavior
        qs = list(
            UserBehavior.objects
            .filter(user_id=user_id)
            .select_related('product')
            .order_by('-timestamp')[:limit]
        )
        return Response({
            'user_id': user_id,
            'count': len(qs),
            'history': [
                {
                    'product_id':   b.product.product_id,
                    'product_name': b.product.name,
                    'action':       b.action,
                    'weight':       b.weight,
                    'timestamp':    b.timestamp.isoformat(),
                }
                for b in qs
            ],
        })

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

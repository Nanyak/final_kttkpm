from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Shipment
from .serializers import ShipmentSerializer, CalculateFeeSerializer
from .services import (
    get_user_from_token, calculate_shipping_fee, update_shipment_status,
)


def ok(data, http=status.HTTP_200_OK):
    return Response({'status': 'success', 'data': data}, status=http)


def err(message, http=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'data': {'message': message}}, status=http)


def require_auth(request):
    user = get_user_from_token(request)
    if not user:
        return None, err('Unauthorized', status.HTTP_401_UNAUTHORIZED)
    return user, None


def require_internal(request):
    return request.META.get('HTTP_X_INTERNAL_TOKEN', '') == settings.INTERNAL_SERVICE_TOKEN


class ShipmentListCreateView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        qs = Shipment.objects.filter(user_id=user['id']).prefetch_related('tracking_events')
        return ok(ShipmentSerializer(qs, many=True).data)

    def post(self, request):
        if not require_internal(request):
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        serializer = ShipmentSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        shipment = serializer.save()
        from .services import publish_event, EXCHANGE_SHIPMENT
        publish_event(EXCHANGE_SHIPMENT, 'shipment.created', {
            'shipment_id': shipment.id,
            'tracking_number': shipment.tracking_number,
            'order_id': shipment.order_id,
            'user_id': shipment.user_id,
        })
        return ok(ShipmentSerializer(shipment).data, status.HTTP_201_CREATED)


class ShipmentDetailView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        shipment = get_object_or_404(Shipment, pk=pk)
        if shipment.user_id != user['id'] and user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        return ok(ShipmentSerializer(shipment).data)


class ShipmentTrackPublicView(APIView):
    def get(self, request, tracking_number):
        shipment = get_object_or_404(Shipment, tracking_number=tracking_number)
        return ok(ShipmentSerializer(shipment).data)


class ShipmentStatusUpdateView(APIView):
    def patch(self, request, pk):
        if not require_internal(request):
            user, error = require_auth(request)
            if error:
                return error
            if user.get('role') != 'admin':
                return err('Forbidden', status.HTTP_403_FORBIDDEN)
        shipment = get_object_or_404(Shipment, pk=pk)
        new_status = request.data.get('status')
        if new_status not in dict(Shipment.STATUS_CHOICES):
            return err('Invalid status')
        shipment = update_shipment_status(
            shipment, new_status,
            location=request.data.get('location', ''),
            description=request.data.get('description', ''),
        )
        return ok(ShipmentSerializer(shipment).data)


class CalculateFeeView(APIView):
    def post(self, request):
        serializer = CalculateFeeSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        d = serializer.validated_data
        fee = calculate_shipping_fee(d['weight_kg'], d['origin_province'],
                                     d['destination_province'], d.get('service_type', 'standard'))
        return ok({'shipping_fee': str(fee), 'currency': 'VND'})


class AdminShipmentListView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        if user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        qs = Shipment.objects.all().prefetch_related('tracking_events')
        return ok(ShipmentSerializer(qs, many=True).data)

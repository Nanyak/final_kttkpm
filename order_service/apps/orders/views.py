from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Order
from .serializers import OrderSerializer, CreateOrderSerializer
from .services import get_user_from_token, create_order_from_cart, cancel_order


def ok(data, http=status.HTTP_200_OK):
    return Response({'status': 'success', 'data': data}, status=http)


def err(message, http=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'data': {'message': message}}, status=http)


def require_auth(request):
    user = get_user_from_token(request)
    if not user:
        return None, err('Unauthorized', status.HTTP_401_UNAUTHORIZED)
    return user, None


class OrderListCreateView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        orders = Order.objects.filter(user_id=user['id']).prefetch_related('items')
        return ok(OrderSerializer(orders, many=True).data)

    def post(self, request):
        user, error = require_auth(request)
        if error:
            return error
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        try:
            order = create_order_from_cart(user, serializer.validated_data,
                                           request.META.get('HTTP_AUTHORIZATION', ''))
        except ValueError as e:
            return err(str(e))
        except Exception as e:
            return err(str(e), status.HTTP_502_BAD_GATEWAY)
        return ok(OrderSerializer(order).data, status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        order = get_object_or_404(Order, pk=pk)
        if order.user_id != user['id'] and user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        return ok(OrderSerializer(order).data)

    def patch(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        if user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status')
        payment_status = request.data.get('payment_status')
        notes = request.data.get('notes')
        if new_status:
            if new_status not in dict(Order.STATUS_CHOICES):
                return err('Invalid status')
            order.status = new_status
        if payment_status:
            if payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
                return err('Invalid payment_status')
            order.payment_status = payment_status
        if notes is not None:
            order.notes = notes
        order.save()
        return ok(OrderSerializer(order).data)


class OrderCancelView(APIView):
    def post(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        order = get_object_or_404(Order, pk=pk)
        if order.user_id != user['id']:
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        try:
            order = cancel_order(order)
        except ValueError as e:
            return err(str(e))
        return ok(OrderSerializer(order).data)


class OrderStatusInternalView(APIView):
    def patch(self, request, pk):
        token = request.META.get('HTTP_X_INTERNAL_TOKEN', '')
        if token != settings.INTERNAL_SERVICE_TOKEN:
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status')
        payment_status = request.data.get('payment_status')
        if new_status:
            if new_status not in dict(Order.STATUS_CHOICES):
                return err('Invalid status')
            order.status = new_status
        if payment_status:
            if payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
                return err('Invalid payment_status')
            order.payment_status = payment_status
        order.save()
        return ok(OrderSerializer(order).data)


class AdminOrderListView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        if user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        orders = Order.objects.all().prefetch_related('items')
        return ok(OrderSerializer(orders, many=True).data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from .services import get_user_from_token, get_or_create_active_cart, add_item_to_cart


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
    token = request.META.get('HTTP_X_INTERNAL_TOKEN', '')
    return token == settings.INTERNAL_SERVICE_TOKEN


class MyCartView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        cart = get_or_create_active_cart(user['id'])
        return ok(CartSerializer(cart).data)

    def delete(self, request):
        user, error = require_auth(request)
        if error:
            return error
        cart = get_or_create_active_cart(user['id'])
        cart.items.all().delete()
        return ok({'cleared': True})


class MyCartItemListView(APIView):
    def post(self, request):
        user, error = require_auth(request)
        if error:
            return error
        try:
            product_id = int(request.data.get('product_id'))
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return err('product_id and quantity are required integers')
        if quantity <= 0:
            return err('Quantity must be positive')
        cart = get_or_create_active_cart(user['id'])
        try:
            item = add_item_to_cart(cart, product_id, quantity)
        except ValueError as e:
            return err(str(e))
        except RuntimeError as e:
            return err(str(e), status.HTTP_503_SERVICE_UNAVAILABLE)
        return ok(CartItemSerializer(item).data, status.HTTP_201_CREATED)


class MyCartItemDetailView(APIView):
    def patch(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        cart = get_or_create_active_cart(user['id'])
        item = get_object_or_404(CartItem, pk=pk, cart=cart)
        if 'quantity' in request.data:
            try:
                qty = int(request.data['quantity'])
            except (TypeError, ValueError):
                return err('Invalid quantity')
            if qty <= 0:
                item.delete()
                return ok({'deleted': True})
            item.quantity = qty
            item.save()
        return ok(CartItemSerializer(item).data)

    def delete(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        cart = get_or_create_active_cart(user['id'])
        item = get_object_or_404(CartItem, pk=pk, cart=cart)
        item.delete()
        return ok({'deleted': True}, status.HTTP_204_NO_CONTENT)


class CartDetailInternalView(APIView):
    def get(self, request, pk):
        if not require_internal(request):
            user, error = require_auth(request)
            if error:
                return error
            cart = get_object_or_404(Cart, pk=pk)
            if cart.user_id != user['id']:
                return err('Forbidden', status.HTTP_403_FORBIDDEN)
        else:
            cart = get_object_or_404(Cart, pk=pk)
        return ok(CartSerializer(cart).data)

    def patch(self, request, pk):
        if not require_internal(request):
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        cart = get_object_or_404(Cart, pk=pk)
        new_status = request.data.get('status')
        if new_status not in dict(Cart.STATUS_CHOICES):
            return err('Invalid status')
        cart.status = new_status
        cart.save()
        return ok(CartSerializer(cart).data)

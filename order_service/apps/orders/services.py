from decimal import Decimal
import jwt
import requests
from django.conf import settings
from django.db import transaction
from .models import Order, OrderItem
from .messaging import publish_event, EXCHANGE_ORDER


def get_user_from_token(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get('type') != 'access':
        return None
    return {'id': payload.get('user_id'), 'email': payload.get('email'), 'role': payload.get('role')}


def fetch_active_cart(user_id, auth_header):
    headers = {'Authorization': auth_header, 'Host': 'localhost'}
    url = f'{settings.CART_SERVICE_URL}/api/carts/me/'
    resp = requests.get(url, headers=headers, timeout=5)
    resp.raise_for_status()
    body = resp.json()
    return body.get('data', body)


def mark_cart_converted(cart_id):
    headers = {'X-Internal-Token': settings.INTERNAL_SERVICE_TOKEN, 'Host': 'localhost'}
    url = f'{settings.CART_SERVICE_URL}/api/carts/{cart_id}/'
    try:
        requests.patch(url, json={'status': 'converted'}, headers=headers, timeout=5)
    except requests.RequestException:
        pass


def reduce_product_stock(product_id, quantity):
    url = f'{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/reduce-stock/'
    resp = requests.patch(url, json={'quantity': quantity}, headers={'Host': 'localhost'}, timeout=5)
    if not resp.ok:
        raise ValueError(f'Failed to reduce stock for product {product_id}')


@transaction.atomic
def create_order_from_cart(user, payload, auth_header):
    cart = fetch_active_cart(user['id'], auth_header)
    items = cart.get('items', [])
    if not items:
        raise ValueError('Cart is empty')

    subtotal = Decimal('0')
    order = Order.objects.create(
        user_id=user['id'],
        status='pending',
        shipping_fee=payload.get('shipping_fee', 0) or 0,
        discount_amount=payload.get('discount_amount', 0) or 0,
        shipping_address=payload['shipping_address'],
        payment_method=payload['payment_method'],
        payment_status='pending',
        notes=payload.get('notes', ''),
    )
    for it in items:
        unit_price = Decimal(str(it['unit_price']))
        qty = int(it['quantity'])
        OrderItem.objects.create(
            order=order,
            product_id=it['product_id'],
            product_name=it['product_name'],
            product_sku=str(it.get('product_id')),
            unit_price=unit_price,
            quantity=qty,
            discount_per_item=Decimal('0'),
        )
        subtotal += unit_price * qty
        try:
            reduce_product_stock(it['product_id'], qty)
        except ValueError:
            raise

    order.subtotal = subtotal
    order.total_amount = subtotal + Decimal(str(order.shipping_fee)) - Decimal(str(order.discount_amount))
    order.save()

    mark_cart_converted(cart['id'])

    publish_event(EXCHANGE_ORDER, 'order.created', {
        'order_id': order.id,
        'order_number': str(order.order_number),
        'user_id': order.user_id,
        'total_amount': str(order.total_amount),
        'payment_method': order.payment_method,
        'shipping_address': order.shipping_address,
        'items': [
            {'product_id': i.product_id, 'product_name': i.product_name,
             'unit_price': str(i.unit_price), 'quantity': i.quantity}
            for i in order.items.all()
        ],
    })
    return order


def cancel_order(order):
    if order.status in ('shipped', 'delivered', 'cancelled'):
        raise ValueError(f'Cannot cancel order in status {order.status}')
    order.status = 'cancelled'
    order.save()
    publish_event(EXCHANGE_ORDER, 'order.cancelled', {
        'order_id': order.id,
        'order_number': str(order.order_number),
        'user_id': order.user_id,
    })
    return order

import jwt
import requests
from django.conf import settings
from .models import Cart, CartItem


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
    return {
        'id': payload.get('user_id'),
        'email': payload.get('email'),
        'role': payload.get('role'),
    }


def fetch_product(product_id):
    url = f'{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/'
    try:
        # Override Host header: Docker service names with underscores (e.g. "product_service")
        # fail Django's strict RFC 1034/1035 hostname validation in split_domain_port(),
        # causing DisallowedHost even when ALLOWED_HOSTS contains '*'.
        resp = requests.get(url, timeout=5, headers={'Host': 'localhost'})
    except requests.RequestException as e:
        raise RuntimeError(f'Product service unavailable: {e}')
    if resp.status_code == 404:
        raise ValueError('Product not found')
    if not resp.ok:
        raise RuntimeError(f'Product service error: {resp.status_code}')
    body = resp.json()
    return body.get('data', body)


def get_or_create_active_cart(user_id):
    cart, _ = Cart.objects.get_or_create(user_id=user_id, status='active')
    return cart


def add_item_to_cart(cart, product_id, quantity):
    product = fetch_product(product_id)
    if not product.get('is_active', True):
        raise ValueError('Product is not active')
    if product.get('stock_quantity', 0) < quantity:
        raise ValueError('Insufficient stock')
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_id=product_id,
        defaults={
            'product_name': product['name'],
            'unit_price': product['base_price'],
            'quantity': quantity,
        },
    )
    if not created:
        item.quantity += quantity
        item.unit_price = product['base_price']
        item.product_name = product['name']
        item.save()
    return item

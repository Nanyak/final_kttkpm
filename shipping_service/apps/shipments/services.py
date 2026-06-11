from decimal import Decimal
from datetime import timedelta
import jwt
import requests
from django.conf import settings
from django.utils import timezone
from .models import Shipment, ShipmentTracking
from .messaging import publish_event, EXCHANGE_SHIPMENT


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


def calculate_shipping_fee(weight_kg, origin_province, destination_province, service_type='standard'):
    weight = Decimal(str(weight_kg))
    base = Decimal('20000')
    if origin_province.lower() != destination_province.lower():
        base += Decimal('15000')
    if weight > Decimal('1'):
        base += (weight - Decimal('1')) * Decimal('5000')
    multipliers = {'standard': Decimal('1'), 'express': Decimal('1.5'), 'same_day': Decimal('2.5')}
    base *= multipliers.get(service_type, Decimal('1'))
    return base.quantize(Decimal('1'))


def fetch_order(order_id):
    headers = {'X-Internal-Token': settings.INTERNAL_SERVICE_TOKEN}
    url = f'{settings.ORDER_SERVICE_URL}/api/orders/{order_id}/'
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.ok:
            return resp.json().get('data', {})
    except requests.RequestException:
        pass
    return None


def auto_create_shipment_from_payment(event_data):
    order_id = event_data.get('order_id')
    user_id = event_data.get('user_id')
    if not order_id or Shipment.objects.filter(order_id=order_id).exists():
        return
    order = fetch_order(order_id)
    addr = (order or {}).get('shipping_address', {}) or {}
    shipment = Shipment.objects.create(
        order_id=order_id,
        user_id=user_id or (order or {}).get('user_id', 0),
        carrier='ghn',
        service_type='standard',
        status='pending',
        recipient_name=addr.get('recipient_name', 'N/A'),
        recipient_phone=addr.get('phone_number', ''),
        origin_address={'province': 'Hanoi', 'address': 'Warehouse Hanoi'},
        destination_address=addr,
        shipping_fee=Decimal(str((order or {}).get('shipping_fee', 0))),
        weight_kg=Decimal('1'),
        estimated_delivery=timezone.now() + timedelta(days=3),
    )
    ShipmentTracking.objects.create(
        shipment=shipment,
        status='pending',
        location='Warehouse Hanoi',
        description='Shipment created, awaiting pickup',
    )
    publish_event(EXCHANGE_SHIPMENT, 'shipment.created', {
        'shipment_id': shipment.id,
        'tracking_number': shipment.tracking_number,
        'order_id': shipment.order_id,
        'user_id': shipment.user_id,
        'carrier': shipment.carrier,
    })
    return shipment


def update_shipment_status(shipment, new_status, location='', description=''):
    shipment.status = new_status
    if new_status == 'picked_up' and not shipment.shipped_at:
        shipment.shipped_at = timezone.now()
    if new_status == 'delivered' and not shipment.delivered_at:
        shipment.delivered_at = timezone.now()
    shipment.save()
    ShipmentTracking.objects.create(
        shipment=shipment,
        status=new_status,
        location=location,
        description=description or f'Status updated to {new_status}',
    )
    publish_event(EXCHANGE_SHIPMENT, f'shipment.{new_status}', {
        'shipment_id': shipment.id,
        'tracking_number': shipment.tracking_number,
        'order_id': shipment.order_id,
        'status': new_status,
    })
    return shipment

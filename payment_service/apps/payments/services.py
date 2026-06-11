import random
import uuid
import jwt
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment, PaymentRefund
from .messaging import publish_event, EXCHANGE_PAYMENT


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


def process_payment(payment):
    """Simulate payment gateway processing.
    For COD always 'pending' (collected on delivery -> manual completion).
    For other methods: 90% success rate.
    """
    if payment.method == 'cod':
        payment.status = 'pending'
        payment.gateway_response = {'gateway': 'cod', 'message': 'Will collect on delivery'}
        payment.save()
        return payment

    success = random.random() < 0.9
    payment.transaction_id = f'TXN-{uuid.uuid4().hex[:16].upper()}'
    if success:
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        payment.gateway_response = {'gateway': payment.method, 'code': '00', 'message': 'Success'}
        payment.save()
        publish_event(EXCHANGE_PAYMENT, 'payment.completed', {
            'payment_id': payment.id,
            'payment_code': payment.payment_code,
            'order_id': payment.order_id,
            'user_id': payment.user_id,
            'amount': str(payment.amount),
            'method': payment.method,
            'transaction_id': payment.transaction_id,
        })
    else:
        payment.status = 'failed'
        payment.failure_reason = 'Gateway declined transaction'
        payment.gateway_response = {'gateway': payment.method, 'code': '99', 'message': 'Declined'}
        payment.save()
        publish_event(EXCHANGE_PAYMENT, 'payment.failed', {
            'payment_id': payment.id,
            'order_id': payment.order_id,
            'user_id': payment.user_id,
            'reason': payment.failure_reason,
        })
    return payment


def create_refund(payment, amount, reason):
    if payment.status != 'completed':
        raise ValueError('Only completed payments can be refunded')
    if Decimal(str(amount)) > payment.amount:
        raise ValueError('Refund amount exceeds payment amount')
    refund = PaymentRefund.objects.create(
        payment=payment,
        refund_amount=amount,
        reason=reason,
        status='completed',
        refund_transaction_id=f'REF-{uuid.uuid4().hex[:16].upper()}',
        processed_at=timezone.now(),
    )
    payment.status = 'refunded'
    payment.save()
    publish_event(EXCHANGE_PAYMENT, 'payment.refunded', {
        'payment_id': payment.id,
        'order_id': payment.order_id,
        'refund_id': refund.id,
        'amount': str(amount),
    })
    return refund

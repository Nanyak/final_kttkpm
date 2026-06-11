from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer, PaymentRefundSerializer
from .services import get_user_from_token, process_payment, create_refund


def ok(data, http=status.HTTP_200_OK):
    return Response({'status': 'success', 'data': data}, status=http)


def err(message, http=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'data': {'message': message}}, status=http)


def require_auth(request):
    user = get_user_from_token(request)
    if not user:
        return None, err('Unauthorized', status.HTTP_401_UNAUTHORIZED)
    return user, None


class PaymentListCreateView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        qs = Payment.objects.filter(user_id=user['id']).prefetch_related('refunds')
        return ok(PaymentSerializer(qs, many=True).data)

    def post(self, request):
        user, error = require_auth(request)
        if error:
            return error
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        data = serializer.validated_data
        payment = Payment.objects.create(
            order_id=data['order_id'],
            user_id=user['id'],
            amount=data['amount'],
            method=data['method'],
            currency=data.get('currency', 'VND'),
            status='processing',
        )
        payment = process_payment(payment)
        return ok(PaymentSerializer(payment).data, status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        payment = get_object_or_404(Payment, pk=pk)
        if payment.user_id != user['id'] and user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        return ok(PaymentSerializer(payment).data)


class PaymentReceiptView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        payment = get_object_or_404(Payment, pk=pk)
        if payment.user_id != user['id'] and user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        receipt = {
            'payment_code': payment.payment_code,
            'order_id': payment.order_id,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'method': payment.method,
            'status': payment.status,
            'transaction_id': payment.transaction_id,
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
        }
        return ok(receipt)


class PaymentRefundView(APIView):
    def post(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        payment = get_object_or_404(Payment, pk=pk)
        if payment.user_id != user['id'] and user.get('role') != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        try:
            amount = Decimal(str(request.data.get('refund_amount', payment.amount)))
        except Exception:
            return err('Invalid refund_amount')
        reason = request.data.get('reason', '')
        if not reason:
            return err('reason is required')
        try:
            refund = create_refund(payment, amount, reason)
        except ValueError as e:
            return err(str(e))
        return ok(PaymentRefundSerializer(refund).data, status.HTTP_201_CREATED)


class VNPayWebhookView(APIView):
    """Handle VNPay IPN/webhook callbacks. Simplified — production verifies signature."""
    def post(self, request):
        data = request.data
        txn_ref = data.get('vnp_TxnRef') or data.get('payment_code')
        response_code = str(data.get('vnp_ResponseCode', ''))
        try:
            payment = Payment.objects.get(payment_code=txn_ref)
        except Payment.DoesNotExist:
            return err('Payment not found', status.HTTP_404_NOT_FOUND)
        if payment.status == 'completed':
            return ok({'message': 'Already completed'})
        if response_code == '00':
            from django.utils import timezone
            from .messaging import publish_event, EXCHANGE_PAYMENT
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.transaction_id = data.get('vnp_TransactionNo', '')
            payment.gateway_response = dict(data)
            payment.save()
            publish_event(EXCHANGE_PAYMENT, 'payment.completed', {
                'payment_id': payment.id,
                'order_id': payment.order_id,
                'user_id': payment.user_id,
                'amount': str(payment.amount),
                'method': payment.method,
                'transaction_id': payment.transaction_id,
            })
        else:
            from .messaging import publish_event, EXCHANGE_PAYMENT
            payment.status = 'failed'
            payment.failure_reason = f'VNPay error code: {response_code}'
            payment.gateway_response = dict(data)
            payment.save()
            publish_event(EXCHANGE_PAYMENT, 'payment.failed', {
                'payment_id': payment.id,
                'order_id': payment.order_id,
                'user_id': payment.user_id,
                'reason': payment.failure_reason,
            })
        return ok({'RspCode': '00', 'Message': 'Confirm Success'})

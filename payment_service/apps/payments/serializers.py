from rest_framework import serializers
from .models import Payment, PaymentRefund


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = '__all__'
        read_only_fields = ['payment', 'created_at', 'processed_at',
                            'refund_transaction_id', 'status']


class PaymentSerializer(serializers.ModelSerializer):
    refunds = PaymentRefundSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_code', 'status', 'transaction_id',
                            'gateway_response', 'failure_reason', 'paid_at',
                            'created_at', 'updated_at']


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)
    currency = serializers.CharField(default='VND')

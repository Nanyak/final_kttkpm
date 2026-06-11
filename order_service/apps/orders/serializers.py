from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['order']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'ordered_at', 'updated_at',
                            'subtotal', 'total_amount']


class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.DictField()
    payment_method = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)
    shipping_fee = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)

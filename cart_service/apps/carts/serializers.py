from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product_id', 'product_name', 'unit_price',
                  'quantity', 'added_at', 'subtotal']
        read_only_fields = ['cart', 'added_at']

    def get_subtotal(self, obj):
        return float(obj.unit_price) * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'status', 'created_at', 'updated_at',
                  'items', 'total_amount', 'total_items']

    def get_total_amount(self, obj):
        return sum(float(i.unit_price) * i.quantity for i in obj.items.all())

    def get_total_items(self, obj):
        return sum(i.quantity for i in obj.items.all())

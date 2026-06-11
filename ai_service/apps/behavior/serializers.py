from rest_framework import serializers
from .models import UserBehavior, Product


class UserBehaviorSerializer(serializers.Serializer):
    user_id    = serializers.IntegerField()
    product_id = serializers.IntegerField()
    action     = serializers.ChoiceField(choices=['view', 'click', 'add_to_cart', 'purchase'])
    timestamp  = serializers.DateTimeField(required=False)

    ACTION_WEIGHT = {'view': 1.0, 'click': 2.0, 'add_to_cart': 3.0, 'purchase': 4.0}

    def validate_action(self, value):
        return value.lower()

    def save(self):
        from django.utils import timezone
        data = self.validated_data
        product, _ = Product.objects.get_or_create(
            product_id=data['product_id'],
            defaults={'name': f"Product {data['product_id']}"}
        )
        behavior = UserBehavior.objects.create(
            user_id=data['user_id'],
            product=product,
            action=data['action'],
            timestamp=data.get('timestamp') or timezone.now(),
            weight=self.ACTION_WEIGHT[data['action']],
        )
        return behavior


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ['product_id', 'name', 'description', 'category', 'price']

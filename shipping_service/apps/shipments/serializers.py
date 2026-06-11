from rest_framework import serializers
from .models import Shipment, ShipmentTracking


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = '__all__'
        read_only_fields = ['shipment', 'recorded_at']


class ShipmentSerializer(serializers.ModelSerializer):
    tracking_events = ShipmentTrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ['tracking_number', 'created_at', 'updated_at',
                            'shipped_at', 'delivered_at']


class CalculateFeeSerializer(serializers.Serializer):
    weight_kg = serializers.DecimalField(max_digits=8, decimal_places=2)
    origin_province = serializers.CharField()
    destination_province = serializers.CharField()
    service_type = serializers.ChoiceField(choices=Shipment.SERVICE_TYPES, default='standard')

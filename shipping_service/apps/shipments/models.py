import uuid
from django.db import models


def gen_tracking_number():
    return f'TRK{uuid.uuid4().hex[:14].upper()}'


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out For Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('returned', 'Returned'),
    ]
    CARRIER_CHOICES = [
        ('ghn', 'Giao Hang Nhanh'),
        ('ghtk', 'Giao Hang Tiet Kiem'),
        ('vnpost', 'Vietnam Post'),
        ('jt', 'J&T Express'),
    ]
    SERVICE_TYPES = [
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('same_day', 'Same Day'),
    ]

    tracking_number = models.CharField(max_length=50, unique=True, default=gen_tracking_number, editable=False)
    order_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES, default='ghn')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    origin_address = models.JSONField(default=dict)
    destination_address = models.JSONField(default=dict)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipments'
        ordering = ['-created_at']


class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=20)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shipment_tracking'
        ordering = ['-recorded_at']

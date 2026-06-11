from django.db import models


class Product(models.Model):
    product_id   = models.IntegerField(unique=True)
    name         = models.CharField(max_length=255)
    description  = models.TextField(default='')
    category     = models.CharField(max_length=100, default='')
    price        = models.FloatField(default=0.0)
    encoded_id   = models.IntegerField(null=True, blank=True)  # index in LSTM vocab

    class Meta:
        db_table = 'ai_products'

    def __str__(self):
        return f"{self.product_id} – {self.name}"


class UserBehavior(models.Model):
    ACTION_CHOICES = [
        ('view',        'View'),
        ('click',       'Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase',    'Purchase'),
    ]

    user_id    = models.IntegerField(db_index=True)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name='behaviors', to_field='product_id')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp  = models.DateTimeField()
    weight     = models.FloatField(default=1.0)  # view=1, click=2, cart=3, purchase=4

    class Meta:
        db_table  = 'ai_user_behavior'
        ordering  = ['user_id', 'timestamp']
        indexes   = [models.Index(fields=['user_id', 'timestamp'])]

    def __str__(self):
        return f"User {self.user_id} → {self.action} → Product {self.product_id}"

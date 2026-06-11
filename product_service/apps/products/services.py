from django.db import transaction
from .models import Product


def reduce_product_stock(product_id, quantity):
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        if product.stock_quantity < quantity:
            raise ValueError(f'Insufficient stock for product {product_id}')
        product.stock_quantity -= quantity
        product.save()
        return product


def restore_product_stock(product_id, quantity):
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity
        product.save()
        return product

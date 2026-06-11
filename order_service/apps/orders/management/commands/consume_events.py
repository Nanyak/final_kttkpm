from django.core.management.base import BaseCommand
from apps.orders.messaging import consume_events


class Command(BaseCommand):
    help = 'Consume RabbitMQ events for order_service'

    def handle(self, *args, **options):
        consume_events()

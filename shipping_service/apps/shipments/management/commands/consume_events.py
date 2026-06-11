from django.core.management.base import BaseCommand
from apps.shipments.messaging import consume_events


class Command(BaseCommand):
    help = 'Consume RabbitMQ events for shipping_service'

    def handle(self, *args, **options):
        consume_events()

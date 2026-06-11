import json
import logging
import pika
from django.conf import settings

logger = logging.getLogger(__name__)


def _connect():
    creds = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=creds,
    )
    return pika.BlockingConnection(params)


def publish_event(exchange, routing_key, data):
    try:
        conn = _connect()
        channel = conn.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(data, default=str).encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json'),
        )
        conn.close()
    except Exception as e:
        logger.exception('Failed to publish event %s/%s: %s', exchange, routing_key, e)


def consume_events():
    logger.info('Cart service has no events to consume.')

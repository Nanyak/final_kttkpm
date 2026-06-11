import json
import logging
import pika
from django.conf import settings

logger = logging.getLogger(__name__)

EXCHANGE_PAYMENT = 'payment_events'
EXCHANGE_SHIPMENT = 'shipment_events'


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
    from .services import auto_create_shipment_from_payment

    conn = _connect()
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE_PAYMENT, exchange_type='topic', durable=True)
    queue = channel.queue_declare(queue='shipping_service_queue', durable=True).method.queue
    channel.queue_bind(queue=queue, exchange=EXCHANGE_PAYMENT, routing_key='payment.completed')

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            if method.routing_key == 'payment.completed':
                auto_create_shipment_from_payment(data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.exception('Error processing event: %s', e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue, on_message_callback=callback)
    logger.info('Shipping service consuming events...')
    channel.start_consuming()

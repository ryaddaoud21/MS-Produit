import json
import threading

import pika

from API.models import db, Product
from .pika_config import get_rabbitmq_connection

# Consommateur RabbitMQ pour la mise à jour du stock
def consume_stock_update():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='stock_update', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='stock_update', queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            produit_id = message.get('produit_id')
            quantite = message.get('quantite', 1)  # Par défaut, retirer 1 du stock

            # Logique pour mettre à jour le stock du produit
            product = Product.query.get(produit_id)
            if product and product.stock >= quantite:
                product.stock -= quantite
                db.session.commit()
                print(f"Stock updated for product {produit_id}. New stock: {product.stock}")
            else:
                print(f"Stock update failed for product {produit_id}. Not enough stock or product not found.")
        except Exception as e:
            print(f"Error processing stock update: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

# Consommateur RabbitMQ pour les notifications de commande
def consume_order_notifications():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='order_notifications', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='order_notifications', queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"Received order notification: {message}")
            # Logique pour traiter la notification de commande ici
        except Exception as e:
            print(f"Error processing order notification: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()



def publish_message(exchange_name, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    # Déclarez l'échange
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

    # Publiez le message
    channel.basic_publish(
        exchange=exchange_name,
        routing_key='',
        body=json.dumps(message)
    )

    connection.close()

# Lancer les threads pour consommer les messages RabbitMQ
def start_rabbitmq_consumers():
    threading.Thread(target=consume_stock_update, daemon=True).start()
    threading.Thread(target=consume_order_notifications, daemon=True).start()

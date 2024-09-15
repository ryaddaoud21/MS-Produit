import json
import threading
from flask import jsonify
from API.models import Product
from API.produits import produits_blueprint
from API.services.pika_config import get_rabbitmq_connection
from produit_api import db


@produits_blueprint.route('/notifications', methods=['GET'])
def get_notifications():
    notifications = {
        "product_notifications": product_notifications,
        "order_notifications": order_notifications
    }
    return jsonify(notifications), 200


# A global variable to store notifications
product_notifications = []
order_notifications = []


# Consommateur RabbitMQ pour la mise à jour du stock
def consume_stock_updates():
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
            quantite = message.get('quantite', 1)  # Défault à 1 si non spécifié

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

# Consommateur RabbitMQ pour d'autres notifications de commande
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





# Lancer les threads pour consommer les messages RabbitMQ
def start_rabbitmq_consumers(app):
    threading.Thread(target=consume_stock_updates, args=(app,), daemon=True).start()
    threading.Thread(target=consume_order_notifications, args=(app,), daemon=True).start()
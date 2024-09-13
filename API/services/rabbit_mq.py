import json
import threading
import pika
from API.models import db, Product
from .pika_config import get_rabbitmq_connection
from flask import Flask, jsonify

# A global variable to store notifications
from ..produits import products_blueprint

order_notifications = []

# Route to get all notifications
@products_blueprint.route('/notifications', methods=['GET'])
def get_notifications():
    return jsonify(order_notifications), 200



# Consommateur RabbitMQ pour la mise à jour du stock
def consume_stock_update(app):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='stock_update', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='stock_update', queue=queue_name)

    def callback(ch, method, properties, body):
        with app.app_context():  # Explicitly push the app context
            try:
                message = json.loads(body)
                produit_id = message.get('produit_id')
                quantite = message.get('quantite', 1)  # Default to 1 if not specified

                # Logique pour mettre à jour le stock du produit
                product = Product.query.get(produit_id)
                if product and product.stock >= quantite:
                    product.stock -= quantite
                    db.session.commit()
                    print(f"Stock updated for product {produit_id}. New stock: {product.stock}")
                    formatted_message = f"Stock updated for product {produit_id}. New stock: {product.stock}"
                    order_notifications.append(formatted_message)

                else:
                    print(f"Stock update failed for product {produit_id}. Not enough stock or product not found.")
            except Exception as e:
                print(f"Error processing stock update: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


# Consommateur RabbitMQ pour d'autres notifications de commande
def consume_order_notifications(app):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='order_notifications', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='order_notifications', queue=queue_name)

    def callback(ch, method, properties, body):
        with app.app_context():  # Explicitly push the app context
            try:
                message = json.loads(body)
                formatted_message = f"Received order notification: {message}"

                # Store the formatted notification
                order_notifications.append(formatted_message)
                print(f"Received order notification: {message}")
                # Logique pour traiter la notification de commande ici
            except Exception as e:
                print(f"Error processing order notification: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()



# Lancer les threads pour consommer les messages RabbitMQ
def start_rabbitmq_consumers(app):
    threading.Thread(target=consume_stock_update, args=(app,), daemon=True).start()
    threading.Thread(target=consume_order_notifications, args=(app,), daemon=True).start()
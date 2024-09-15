import json
import threading
import pika
from API.models import db, Product
from .pika_config import get_rabbitmq_connection
from flask import Flask, jsonify

# A global variable to store notifications

order_notifications = []





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


def verify_token(token):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='auth_requests')

    # Formater le message de requête de vérification
    request_message = f"Demande de vérification de jeton envoyée : {token}"
    print(request_message)
    order_notifications.append(request_message)

    message = {'token': token}
    channel.basic_publish(exchange='', routing_key='auth_requests', body=json.dumps(message))

    # Écouter la réponse
    print("En attente de la réponse de vérification de jeton...")
    response = None

    for method_frame, properties, body in channel.consume('auth_responses', inactivity_timeout=1):
        if body:
            response = json.loads(body)
            # Formater le message de réponse reçue
            response_message = (
                f"Réponse reçue : Authentifié = {response.get('authenticated')}, "
                f"Rôle = {response.get('role')}"
            )
            print(response_message)
            order_notifications.append(response_message)
            break

    if not response:
        no_response_message = "Aucune réponse reçue pour la vérification du jeton."
        print(no_response_message)
        order_notifications.append(no_response_message)

    connection.close()

    if response.get('authenticated', False):
        formatted_message = f"Utilisateur authentifié avec succès, rôle : {response.get('role')}"
    else:
        formatted_message = "Échec de l'authentification de l'utilisateur"

    # Stocker la notification formatée
    order_notifications.append(formatted_message)

    return response.get('authenticated', False), response.get('role')



# Lancer les threads pour consommer les messages RabbitMQ
def start_rabbitmq_consumers(app):
    threading.Thread(target=verify_token, args=(app,), daemon=True).start()
    threading.Thread(target=consume_stock_update, args=(app,), daemon=True).start()
    threading.Thread(target=consume_order_notifications, args=(app,), daemon=True).start()
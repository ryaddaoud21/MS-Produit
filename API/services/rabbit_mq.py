import json
import threading

import pika
from flask import jsonify
from API.services.pika_config import get_rabbitmq_connection

# A global variable to store notifications
product_notifications = []

# RabbitMQ consumer for product stock updates
def consume_stock_updates():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='stock_update', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='stock_update', queue=queue_name)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        formatted_message = f"Received stock update: {message}"

        # Store the formatted notification
        product_notifications.append(formatted_message)
        # Logic to update stock notification
        print(f"Received stock update for product: {message}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


def verify_token(token):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='auth_requests')

    # Formater le message de requête de vérification
    request_message = f"Demande de vérification de jeton envoyée : {token}"
    print(request_message)
    product_notifications.append(request_message)

    message = {'token': token}
    channel.basic_publish(exchange='', routing_key='auth_requests', body=json.dumps(message))

    # Écouter la réponse
    print("En attente de la réponse de vérification de jeton...")
    response = None

    for method_frame, properties, body in channel.consume('auth_responses', inactivity_timeout=1):
        if body:
            response = json.loads(body)
            response_message = (
                f"Réponse reçue : Authentifié = {response.get('authenticated')}, "
                f"Rôle = {response.get('role')}"
            )
            print(response_message)
            product_notifications.append(response_message)
            break

    if not response:
        no_response_message = "Aucune réponse reçue pour la vérification du jeton."
        print(no_response_message)
        product_notifications.append(no_response_message)

    connection.close()

    if response.get('authenticated', False):
        formatted_message = f"Utilisateur authentifié avec succès, rôle : {response.get('role')}"
    else:
        formatted_message = "Échec de l'authentification de l'utilisateur"

    product_notifications.append(formatted_message)

    return response.get('authenticated', False), response.get('role')

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
    threading.Thread(target=verify_token, args=(app,), daemon=True).start()
    threading.Thread(target=consume_stock_updates, args=(app,), daemon=True).start()
    threading.Thread(target=consume_order_notifications, args=(app,), daemon=True).start()
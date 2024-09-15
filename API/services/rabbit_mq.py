import json
import threading
from API.services.pika_config import get_rabbitmq_connection




# A global variable to store notifications
product_notifications = []
order_notifications = []
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
    threading.Thread(target=consume_stock_updates, args=(app,), daemon=True).start()
    threading.Thread(target=consume_order_notifications, args=(app,), daemon=True).start()
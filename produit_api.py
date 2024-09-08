import threading
from prometheus_client import generate_latest, Counter, Summary, start_http_server
from flask import Flask, jsonify
from API.models import db
from API.auth import auth_blueprint
from API.produits import products_blueprint
from API.services.rabbit_mq import consume_order_notifications, consume_stock_update, start_rabbitmq_consumers
from API.config import Config


app = Flask(__name__)
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(products_blueprint, url_prefix='/')


if __name__ == '__main__':
    start_rabbitmq_consumers(app)

    # Lancer le serveur HTTP pour Prometheus sur le port 8000
    start_http_server(8000)
    app.run(host='0.0.0.0', port=5002)

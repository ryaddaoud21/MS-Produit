from flask import Flask, jsonify
from prometheus_client import multiprocess, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from threading import Thread
from API.models import db  # db est déjà initialisé ici
from API.produits import produits_blueprint
from API.auth import auth_blueprint
from API.services.rabbit_mq import consume_stock_updates
from API.config import Config

app = Flask(__name__)

# Charger la configuration
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(produits_blueprint, url_prefix='/')

# Route pour les métriques Prometheus
@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    # Lancer le consommateur RabbitMQ dans un thread séparé
    Thread(target=consume_stock_updates, daemon=True).start()
    app.run(host='0.0.0.0', port=5002)

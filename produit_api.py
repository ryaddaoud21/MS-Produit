from flask import Flask
from API.config import Config
from API.models import db
from API.produits import produits_blueprint
from API.services.rabbit_mq import start_rabbitmq_consumers
import threading
from prometheus_client import multiprocess, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer le blueprint des produits
app.register_blueprint(produits_blueprint)


@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}



if __name__ == '__main__':
    # Démarrer RabbitMQ dans un thread séparé
    threading.Thread(target=start_rabbitmq_consumers, args=(app,), daemon=True).start()
    # Lancer le serveur Flask
    app.run(host='0.0.0.0', port=5002)
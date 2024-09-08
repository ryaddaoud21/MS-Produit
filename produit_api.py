from flask import Flask
from API.models import db
from API.auth import auth_blueprint
from API.produits import products_blueprint
from API.services.rabbit_mq import start_rabbitmq_consumers
from API.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(products_blueprint, url_prefix='/')

if __name__ == '__main__':
    # Lancer les consommateurs RabbitMQ dans des threads séparés
    start_rabbitmq_consumers()
    app.run(host='0.0.0.0', port=5002)

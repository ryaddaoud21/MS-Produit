import threading
from prometheus_client import generate_latest, Counter, Summary, start_http_server
from flask import Flask, jsonify
from API.models import db
from API.auth import auth_blueprint
from API.produits import products_blueprint
from API.services.rabbit_mq import start_rabbitmq_consumers
from API.config import Config
from prometheus_client import multiprocess, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

app.config.from_object(Config)
#app.config['DEBUG'] = True

# Initialize the database
db.init_app(app)
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(products_blueprint, url_prefix='/')

# Register the blueprints
#app.register_blueprint(clients_blueprint)
#app.register_blueprint(auth_blueprint)


@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

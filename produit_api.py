from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from API.models import db
from API.produits import produits_blueprint
from API.auth import auth_blueprint
from threading import Thread
from API.services.rabbit_mq import consume_stock_updates
from API.config import Config
from prometheus_client import multiprocess, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

app.config.from_object(Config)

# Initialize the database
db.init_app(app)
db = SQLAlchemy(app)

app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(produits_blueprint, url_prefix='/')


@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}




if __name__ == '__main__':
    Thread(target=consume_stock_updates, daemon=True).start()
    app.run(host='0.0.0.0', port=5002)

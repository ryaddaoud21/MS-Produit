import threading

from flask import Flask
from API.models import db
from API.auth import auth_blueprint
from API.produits import products_blueprint
from API.services.rabbit_mq import consume_order_notifications, consume_stock_update
from API.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(products_blueprint, url_prefix='/')

if __name__ == '__main__':
    threading.Thread(target=consume_stock_update, daemon=True).start()
    threading.Thread(target=consume_order_notifications, daemon=True).start()
    app.run(host='0.0.0.0', port=5002)

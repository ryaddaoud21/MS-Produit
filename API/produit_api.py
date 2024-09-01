from flask import Flask, jsonify, request, make_response
from functools import wraps
import secrets
from flask_sqlalchemy import SQLAlchemy
import threading
import pika
import json
from .pika_config import  get_rabbitmq_connection

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/product_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)


# Modèle de la base de données pour les produits
class Product(db.Model):
    __tablename__ = 'produits'  # Nom de la table dans MySQL

    id = db.Column('ProduitID', db.Integer, primary_key=True)
    nom = db.Column('Nom', db.String(255), nullable=False)
    description = db.Column('Description', db.Text)
    prix = db.Column('Prix', db.Numeric(10, 2), nullable=False)
    stock = db.Column('Stock', db.Integer, nullable=False)
    categorie = db.Column('Categorie', db.String(255))

    def __repr__(self):
        return f'<Product {self.nom}>'


# Simulated token storage (In a real application, use a database or other secure storage)
valid_tokens = {}


# Function to generate a secure token
def generate_token():
    return secrets.token_urlsafe(32)


# Decorator to require a valid token
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        received_token = token.split('Bearer ')[1]
        user = next((u for u, t in valid_tokens.items() if t["token"] == received_token), None)

        if not user:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        request.user = user
        request.role = valid_tokens[user]['role']

        return f(*args, **kwargs)

    return decorated_function


# Decorator to require admin role
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)

    return decorated_function


# Endpoint to login and generate a token
@app.route('/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({"msg": "Username and password required"}), 400

    username = request.json['username']
    password = request.json['password']

    # Simple user validation (hardcoded users)
    users = {
        "admin": {"password": "password", "role": "admin"},
        "user1": {"password": "userpass", "role": "user"},
    }

    if username in users and users[username]['password'] == password:
        token = generate_token()
        valid_tokens[username] = {"token": token, "role": users[username]['role']}
        return jsonify({"token": token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401


# Endpoint to logout and invalidate the token
@app.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization').split('Bearer ')[1]
    user = next((u for u, t in valid_tokens.items() if t["token"] == token), None)
    if user:
        del valid_tokens[user]
        return jsonify({"msg": "Successfully logged out"}), 200
    return make_response(jsonify({"error": "Unauthorized"}), 401)


# Endpoint to get all products
@app.route('/products', methods=['GET'])
@token_required
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix": str(p.prix),
        "stock": p.stock,
        "categorie": p.categorie
    } for p in products])


# Endpoint to get a specific product by ID
@app.route('/products/<int:id>', methods=['GET'])
@token_required
def get_product(id):
    product = Product.query.get(id)
    if product:
        return jsonify({
            "id": product.id,
            "nom": product.nom,
            "description": product.description,
            "prix": str(product.prix),
            "stock": product.stock,
            "categorie": product.categorie
        })
    return jsonify({'message': 'Product not found'}), 404


# Endpoint to create a new product (admin only)
@app.route('/products', methods=['POST'])
@token_required
@admin_required
def create_product():
    data = request.json
    new_product = Product(
        nom=data['nom'],
        description=data.get('description'),
        prix=data['prix'],
        stock=data['stock'],
        categorie=data.get('categorie')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"id": new_product.id, "nom": new_product.nom}), 201


# Endpoint to update a product (admin only)
@app.route('/products/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_product(id):
    product = Product.query.get(id)
    if product:
        data = request.json
        product.nom = data.get('nom', product.nom)
        product.description = data.get('description', product.description)
        product.prix = data.get('prix', product.prix)
        product.stock = data.get('stock', product.stock)
        product.categorie = data.get('categorie', product.categorie)
        db.session.commit()
        return jsonify({"id": product.id, "nom": product.nom})
    return jsonify({'message': 'Product not found'}), 404


# Endpoint to delete a product (admin only)
@app.route('/products/<int:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted'})
    return jsonify({'message': 'Product not found'}), 404


def consume_order_notifications():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='order_notifications', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='order_notifications', queue=queue_name)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        # Logique pour traiter la commande, vérifier la disponibilité du produit, etc.
        print(f"Received order notification: {message}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


if __name__ == '__main__':
    # Lancer l'écoute des messages RabbitMQ dans un thread séparé
    threading.Thread(target=consume_order_notifications, daemon=True).start()

    # Lancer le serveur Flask
    app.run(debug=True, port=5002)

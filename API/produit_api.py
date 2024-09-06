from flask import Flask, jsonify, request, make_response
from functools import wraps
import secrets
from flask_sqlalchemy import SQLAlchemy
import threading
import pika
import json
from .pika_config import get_rabbitmq_connection
from sqlalchemy.exc import SQLAlchemyError

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@mysql-db/produit_db'
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

# Stockage simulé des tokens
valid_tokens = {}

# Fonction pour générer un token sécurisé
def generate_token():
    return secrets.token_urlsafe(32)

# Décorateur pour exiger un token valide
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

# Décorateur pour exiger le rôle d'administrateur
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)

    return decorated_function

# Endpoint pour se connecter et générer un token
@app.route('/login', methods=['POST'])
def login():
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        return jsonify({"msg": "Username and password required"}), 400

    username = request.json['username']
    password = request.json['password']

    # Validation simple des utilisateurs (utilisateurs codés en dur)
    users = {
        "admin": {"password": "password", "role": "admin"},
        "user1": {"password": "userpass", "role": "user"},
    }

    if username in users and users[username]['password'] == password:
        token = generate_token()
        valid_tokens[username] = {"token": token, "role": users[username]['role']}
        return jsonify({"token": token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# Endpoint pour se déconnecter et invalider le token
@app.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization').split('Bearer ')[1]
    user = next((u for u, t in valid_tokens.items() if t["token"] == token), None)
    if user:
        del valid_tokens[user]
        return jsonify({"msg": "Successfully logged out"}), 200
    return make_response(jsonify({"error": "Unauthorized"}), 401)

# Endpoint pour récupérer tous les produits
@app.route('/products', methods=['GET'])
@token_required
def get_products():
    try:
        products = Product.query.all()
        return jsonify([{
            "id": p.id,
            "nom": p.nom,
            "description": p.description,
            "prix": str(p.prix),
            "stock": p.stock,
            "categorie": p.categorie
        } for p in products])
    except SQLAlchemyError as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint pour récupérer un produit spécifique par ID
@app.route('/products/<int:id>', methods=['GET'])
@token_required
def get_product(id):
    try:
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
    except SQLAlchemyError as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint pour créer un nouveau produit (admin uniquement)
@app.route('/products', methods=['POST'])
@token_required
@admin_required
def create_product():
    data = request.json
    try:
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
    except SQLAlchemyError as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint pour mettre à jour un produit (admin uniquement)
@app.route('/products/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_product(id):
    product = Product.query.get(id)
    if product:
        data = request.json
        try:
            product.nom = data.get('nom', product.nom)
            product.description = data.get('description', product.description)
            product.prix = data.get('prix', product.prix)
            product.stock = data.get('stock', product.stock)
            product.categorie = data.get('categorie', product.categorie)
            db.session.commit()
            return jsonify({"id": product.id, "nom": product.nom})
        except SQLAlchemyError as e:
            return make_response(jsonify({"error": str(e)}), 500)
    return jsonify({'message': 'Product not found'}), 404

# Endpoint pour supprimer un produit (admin uniquement)
@app.route('/products/<int:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(id):
    product = Product.query.get(id)
    if product:
        try:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Product deleted'})
        except SQLAlchemyError as e:
            return make_response(jsonify({"error": str(e)}), 500)
    return jsonify({'message': 'Product not found'}), 404

# Consommateur RabbitMQ pour la mise à jour du stock
def consume_stock_update():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='stock_update', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='stock_update', queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            produit_id = message.get('produit_id')
            quantite = message.get('quantite', 1)  # Défault à 1 si non spécifié

            # Logique pour mettre à jour le stock du produit
            product = Product.query.get(produit_id)
            if product and product.stock >= quantite:
                product.stock -= quantite
                db.session.commit()
                print(f"Stock updated for product {produit_id}. New stock: {product.stock}")
            else:
                print(f"Stock update failed for product {produit_id}. Not enough stock or product not found.")
        except Exception as e:
            print(f"Error processing stock update: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

# Consommateur RabbitMQ pour d'autres notifications de commande
def consume_order_notifications():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='order_notifications', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='order_notifications', queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"Received order notification: {message}")
            # Logique pour traiter la notification de commande ici
        except Exception as e:
            print(f"Error processing order notification: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    # Lancer l'écoute des messages RabbitMQ dans un thread séparé
    threading.Thread(target=consume_stock_update, daemon=True).start()
    threading.Thread(target=consume_order_notifications, daemon=True).start()
    # Lancer le serveur

    app.run(host='0.0.0.0', port=5002)

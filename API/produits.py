from flask import Blueprint, jsonify, request
from API.models import db, Product
from prometheus_client import Counter, Summary

# Création du blueprint pour les routes des produits
produits_blueprint = Blueprint('produits', __name__)

# Variables pour le monitoring Prometheus
REQUEST_COUNT = Counter('product_requests_total', 'Total number of requests for products')
REQUEST_LATENCY = Summary('product_processing_seconds', 'Time spent processing product requests')


# Route pour obtenir tous les produits (GET)
@produits_blueprint.route('/products', methods=['GET'])
@REQUEST_LATENCY.time()
def get_products():
    REQUEST_COUNT.inc()  # Incrémenter le compteur de requêtes
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix": str(p.prix),
        "stock": p.stock,
        "categorie": p.categorie
    } for p in products]), 200

# Route pour obtenir un produit par ID (GET)
@produits_blueprint.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    return jsonify({
        "id": product.id,
        "nom": product.nom,
        "description": product.description,
        "prix": str(product.prix),
        "stock": product.stock,
        "categorie": product.categorie
    }), 200

# Route pour créer un nouveau produit (POST)
@produits_blueprint.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Product(
        nom=data['nom'],
        description=data['description'],
        prix=data['prix'],
        stock=data['stock'],
        categorie=data['categorie']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"id": new_product.id, "nom": new_product.nom}), 201

# Route pour mettre à jour un produit par ID (PUT)
@produits_blueprint.route('/products/<int:id>', methods=['PUT'])
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

# Route pour supprimer un produit par ID (DELETE)
@produits_blueprint.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
    return jsonify({'message': 'Product not found'}), 404

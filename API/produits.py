from flask import Blueprint, jsonify, request, make_response
from API.models import db, Product
from API.auth import token_required
from sqlalchemy.exc import SQLAlchemyError
from prometheus_client import Counter, Summary, generate_latest

# Prometheus metrics
PRODUCT_REQUESTS = Counter('product_requests_total', 'Total number of requests for products')
PRODUCT_PROCESSING_TIME = Summary('product_processing_seconds', 'Time spent processing product requests')

products_blueprint = Blueprint('products', __name__)


# Endpoint for Prometheus metrics
@products_blueprint.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200

# Endpoint pour récupérer tous les produits
@products_blueprint.route('/products', methods=['GET'])
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
@products_blueprint.route('/products/<int:id>', methods=['GET'])
@token_required
@PRODUCT_PROCESSING_TIME.time()  # Mesurer le temps de traitement de cette requête

def get_product(id):
    PRODUCT_REQUESTS.inc()  # Incrémenter le compteur pour chaque requête sur /products
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
@products_blueprint.route('/products', methods=['POST'])
@token_required
#@admin_required
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
@products_blueprint.route('/products/<int:id>', methods=['PUT'])
@token_required
#@admin_required
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
@products_blueprint.route('/products/<int:id>', methods=['DELETE'])
@token_required
#@admin_required
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

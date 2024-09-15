# API/produits.py

from flask import Blueprint, jsonify, request, make_response
from API.models import Product, db
from API.auth import token_required, admin_required
from sqlalchemy.exc import SQLAlchemyError

produits_blueprint = Blueprint('produits', __name__)

@produits_blueprint.route('/products', methods=['GET'])
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

@produits_blueprint.route('/products/<int:id>', methods=['GET'])
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

@produits_blueprint.route('/products', methods=['POST'])
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

@produits_blueprint.route('/products/<int:id>', methods=['PUT'])
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

@produits_blueprint.route('/products/<int:id>', methods=['DELETE'])
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

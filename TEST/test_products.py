import pytest
from unittest.mock import patch
from flask import Flask
from API.models import db, Product
from API.produits import products_blueprint
from API.auth import auth_blueprint
from API.config import Config

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Utiliser SQLite en mémoire pour les tests
    app.config['TESTING'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(products_blueprint)
    app.register_blueprint(auth_blueprint)

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    return response.json['token']

@pytest.fixture
def user_token(client):
    response = client.post('/login', json={'username': 'user1', 'password': 'userpass'})
    return response.json['token']

# Test pour récupérer tous les produits
def test_get_products(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/products', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Test pour créer un produit
def test_create_product(client, admin_token):
    product_data = {
        "nom": "Produit 1",
        "description": "Description du produit 1",
        "prix": "100.00",
        "stock": 10,
        "categorie": "Catégorie 1"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post('/products', json=product_data, headers=headers)
    assert response.status_code == 201, "Product creation failed"
    assert 'id' in response.json, "Expected 'id' in response"


# Test de mise à jour d'un produit
def test_update_product(client, admin_token):
    product_data = {
        "nom": "Produit 1",
        "description": "Description du produit 1",
        "prix": "100.00",
        "stock": 10,
        "categorie": "Catégorie 1"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/products', json=product_data, headers=headers)

    updated_data = {
        "nom": "Produit mis à jour",
        "prix": "150.00"
    }

    product_id = create_response.json['id']
    response = client.put(f'/products/{product_id}', json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json['nom'] == "Produit mis à jour"
    assert response.json['id'] == product_id

# Test de suppression d'un produit
def test_delete_product(client, admin_token):
    product_data = {
        "nom": "Produit à supprimer",
        "description": "Description du produit",
        "prix": "100.00",
        "stock": 10,
        "categorie": "Catégorie 1"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/products', json=product_data, headers=headers)

    product_id = create_response.json['id']
    delete_response = client.delete(f'/products/{product_id}', headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json['message'] == 'Product deleted'

# Test de tentative de suppression d'un produit par un utilisateur non admin
def test_delete_product_non_admin(client, admin_token, user_token):
    # Créer le produit en tant qu'administrateur
    product_data = {
        "nom": "Produit à supprimer",
        "description": "Description du produit",
        "prix": "100.00",
        "stock": 10,
        "categorie": "Catégorie 1"
    }
    headers_admin = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/products', json=product_data, headers=headers_admin)

    # Vérifier que le produit a bien été créé
    product_id = create_response.json.get('id', None)
    assert product_id is not None, "Product ID should exist"

    # Essayer de supprimer le produit avec un utilisateur non administrateur
    headers_user = {'Authorization': f'Bearer {user_token}'}
    delete_response = client.delete(f'/products/{product_id}', headers=headers_user)

    # Vérifier que la suppression est refusée
    assert delete_response.status_code == 403
    assert delete_response.json['error'] == 'Forbidden'

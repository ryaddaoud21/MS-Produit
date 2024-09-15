import json
import pytest
from unittest.mock import patch
from flask import Flask
from API.models import db, Product
from API.produits import produits_blueprint
from API.auth import auth_blueprint
from API.config import Config

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Utiliser une base de données en mémoire pour les tests
    app.config['TESTING'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(produits_blueprint)
    app.register_blueprint(auth_blueprint)

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    # Obtenir un token d'authentification pour l'admin
    response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    return response.json['token']

@pytest.fixture
def user_token(client):
    # Obtenir un token d'authentification pour un utilisateur standard
    response = client.post('/login', json={'username': 'user1', 'password': 'userpass'})
    return response.json['token']


def test_get_all_products(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/products', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_create_product(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    product_data = {
        'nom': 'New Product',
        'description': 'Test description',
        'prix': 50.0,
        'stock': 10,
        'categorie': 'Electronics'
    }
    response = client.post('/products', json=product_data, headers=headers)
    assert response.status_code == 201
    assert 'id' in response.json
    assert response.json['nom'] == 'New Product'


def test_update_product(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    # Créer un produit
    product_data = {
        'nom': 'Old Product',
        'description': 'Old description',
        'prix': 30.0,
        'stock': 5,
        'categorie': 'Books'
    }
    create_response = client.post('/products', json=product_data, headers=headers)
    product_id = create_response.json['id']

    # Mettre à jour le produit
    updated_data = {'nom': 'Updated Product', 'prix': 40.0}
    update_response = client.put(f'/products/{product_id}', json=updated_data, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json['nom'] == 'Updated Product'
    assert update_response.json['prix'] == 40.0


def test_delete_product(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    # Créer un produit
    product_data = {
        'nom': 'To Delete',
        'description': 'To be deleted',
        'prix': 20.0,
        'stock': 2,
        'categorie': 'Furniture'
    }
    create_response = client.post('/products', json=product_data, headers=headers)
    product_id = create_response.json['id']

    # Supprimer le produit
    delete_response = client.delete(f'/products/{product_id}', headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json['message'] == 'Product deleted successfully'


def test_get_product_by_id(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    # Créer un produit
    product_data = {
        'nom': 'Find Me',
        'description': 'Find this product',
        'prix': 100.0,
        'stock': 15,
        'categorie': 'Computers'
    }
    create_response = client.post('/products', json=product_data, headers=headers)
    product_id = create_response.json['id']

    # Récupérer le produit par son ID
    response = client.get(f'/products/{product_id}', headers=headers)
    assert response.status_code == 200
    assert response.json['nom'] == 'Find Me'


def test_get_product_not_found(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/products/999', headers=headers)
    assert response.status_code == 404
    assert response.json['message'] == 'Product not found'

'''
def test_delete_product_non_admin(client, admin_token, user_token):
    headers_admin = {'Authorization': f'Bearer {admin_token}'}
    headers_user = {'Authorization': f'Bearer {user_token}'}

    # Créer un produit avec un token admin
    product_data = {
        'nom': 'Admin Product',
        'description': 'Created by Admin',
        'prix': 75.0,
        'stock': 8,
        'categorie': 'Tools'
    }
    create_response = client.post('/products', json=product_data, headers=headers_admin)
    product_id = create_response.json['id']

    # Tentative de suppression par un utilisateur non-admin
    delete_response = client.delete(f'/products/{product_id}', headers=headers_user)
    assert delete_response.status_code == 403
    assert delete_response.json['error'] == 'Forbidden' 
 
'''
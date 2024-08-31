import unittest
import json
from API.produit_api import app, db, Product

class ProductTestCase(unittest.TestCase):

    def setUp(self):
        # Configure l'application pour les tests
        self.app = app.test_client()
        self.app.testing = True

        # Configure la base de données pour utiliser SQLite en mémoire
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

        # Ajouter un produit de test
        product = Product(nom="Test Product", description="Description du produit", prix=99.99, stock=10, categorie="Test")
        db.session.add(product)
        db.session.commit()

        # Charger le produit pour l'utiliser dans les tests
        self.product1 = Product.query.filter_by(nom="Test Product").first()

        # Créer un jeton admin pour les tests
        self.admin_token = self.get_token("admin", "password")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def get_token(self, username, password):
        response = self.app.post('/login', json={
            'username': username,
            'password': password
        })
        data = json.loads(response.data)
        return data.get('token')

    def test_login_valid(self):
        token = self.get_token("admin", "password")
        self.assertIsNotNone(token)

    def test_login_invalid(self):
        response = self.app.post('/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)

    def test_get_all_products(self):
        response = self.app.get('/products', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nom'], 'Test Product')

    def test_get_product_by_id(self):
        # Recharger l'instance du produit depuis la base de données pour éviter DetachedInstanceError
        product = Product.query.get(self.product1.id)
        response = self.app.get(f'/products/{product.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['nom'], 'Test Product')

    def test_create_product(self):
        response = self.app.post('/products', json={
            'nom': 'New Product',
            'description': 'New product description',
            'prix': 49.99,
            'stock': 20,
            'categorie': 'New Category'
        }, headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['nom'], 'New Product')

    def test_update_product(self):
        # Recharger l'instance du produit depuis la base de données pour éviter DetachedInstanceError
        product = Product.query.get(self.product1.id)
        response = self.app.put(f'/products/{product.id}', json={
            'nom': 'Updated Product'
        }, headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['nom'], 'Updated Product')

    def test_delete_product(self):
        # Recharger l'instance du produit depuis la base de données pour éviter DetachedInstanceError
        product = Product.query.get(self.product1.id)
        response = self.app.delete(f'/products/{product.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        response = self.app.get(f'/products/{product.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()

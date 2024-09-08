from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'produits'

    id = db.Column('ProduitID', db.Integer, primary_key=True)
    nom = db.Column('Nom', db.String(255), nullable=False)
    description = db.Column('Description', db.Text)
    prix = db.Column('Prix', db.Numeric(10, 2), nullable=False)
    stock = db.Column('Stock', db.Integer, nullable=False)
    categorie = db.Column('Categorie', db.String(255))

    def __repr__(self):
        return f'<Product {self.nom}>'

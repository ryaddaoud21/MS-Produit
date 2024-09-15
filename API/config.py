import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root@mysql-db/produit_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    os.environ['SQLALCHEMY_WARN_20'] = '1'
    os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'
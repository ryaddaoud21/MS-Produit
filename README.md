
# MS-Produit

## Microservice Produit

### Description

Le microservice `Produit` gère les informations sur les produits. Il permet de créer, lire, mettre à jour et supprimer des produits dans une base de données MySQL. Ce service s'intègre avec RabbitMQ pour la gestion des notifications et des mises à jour de stock. En outre, il expose des métriques pour la surveillance via Prometheus et Grafana.

### Architecture
![Ajouter un sous-titre (2)](https://github.com/user-attachments/assets/834bf629-3612-43d5-aefa-bddfe14acf5e)

Le microservice `MS-Produit` fait partie d'une architecture microservices plus large, qui comprend également :

- **MS-Client** : Microservice pour la gestion des clients.
- **MS-Commande** : Microservice pour la gestion des commandes.
- **RabbitMQ** : Service de messagerie pour la communication entre les microservices.
- **Prometheus** : Outil de surveillance pour collecter les métriques des microservices.
- **Grafana** : Plateforme d'analyse et de visualisation des métriques Prometheus.
- **MySQL** : Base de données pour les microservices `Client`, `Produit` et `Commande`.

### Prérequis

Avant de commencer, assurez-vous que vous avez installé les éléments suivants :

- **Docker** : Utilisé pour exécuter les conteneurs.
- **Docker Compose** : Utilisé pour orchestrer plusieurs conteneurs Docker.
- **Prometheus** : Utilisé pour surveiller les performances des microservices.
- **Grafana** : Utilisé pour visualiser les métriques collectées par Prometheus.
- **Git** : Pour cloner les dépôts de microservices.

### Installation et Démarrage avec Docker Compose

1. **Clonez le dépôt du microservice Produit :**

   ```bash
   git clone https://github.com/ryaddaoud21/MS-Produit.git
   cd MS-Produit
   ```

2. **Récupérer le fichier `docker-compose.yml` pour l'architecture complète :**
   Clonez le dépôt du microservice : https://github.com/ryaddaoud21/microservices-deployment
   Ce fichier orchestrera tous les services nécessaires, y compris Prometheus, Grafana, RabbitMQ, MySQL et les microservices.

   ```bash
   docker-compose up -d
   ```

3. **Vérifiez que les services sont bien démarrés :**

   ```bash
   docker-compose ps
   ```

4. **Tester le microservice :**

   Pour exécuter les tests unitaires dans ce projet, utilisez la commande suivante :

   ```bash
   python -m unittest discover -s TEST | pytest
   ```

### Endpoints

- **GET** `/products` : Récupère la liste de tous les produits.
- **GET** `/products/<id>` : Récupère les détails d'un produit spécifique.
- **POST** `/products` : Crée un nouveau produit (réservé aux administrateurs).
- **PUT** `/products/<id>` : Met à jour les informations d'un produit (réservé aux administrateurs).
- **DELETE** `/products/<id>` : Supprime un produit (réservé aux administrateurs).

### Surveillance et Visualisation

- **Prometheus** collecte les métriques du microservice.
- **Grafana** visualise ces métriques pour surveiller la performance et les ressources du microservice.

### Structure du Projet

```
MS-Produit/
├── .github/                # Configurations spécifiques à GitHub
│   ├── produit.yml       # Fichiers yml pour le pipeline CI
│   ├── produit_app.yml       # Fichiers yml pour le pipeline CD

├── .idea/                  # Configurations IDE (par exemple, PyCharm)
├── API/
│   ├── __pycache__/        # Fichiers Python compilés
│   ├── services/
│   │   ├── pika_config.py  # Configuration de la connexion RabbitMQ
│   │   ├── rabbitmq_consumer.py # Service consommateur RabbitMQ pour les événements produits
│   ├── produits.py         # Endpoints de l'API pour la gestion des produits
│   ├── config.py           # Configuration de Flask et du service
│   ├── models.py           # Modèles de base de données liés aux produits
├── TEST/
│   ├── __pycache__/        # Fichiers Python compilés pour les tests
│   ├── __init__.py         # Initialisation de la suite de tests
│   ├── conftest.py         # Configuration pour le framework de tests (pytest)
│   ├── test_products.py    # Tests pour les fonctionnalités liées aux produits
│   ├── test_auth.py
├── .gitignore              # Fichiers et répertoires à ignorer dans le contrôle de version
├── Dockerfile              # Configuration Docker pour la conteneurisation du service
├── README.md               # Documentation du service MS-produit
├── produit_api.py          # Point d'entrée pour exécuter l'application Flask
├── requirements.txt        # Dépendances Python pour le projet
```



# Utiliser une image Python comme base
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le contenu du répertoire local dans le conteneur
COPY . /app

# Installer les dépendances à partir du fichier requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port sur lequel l'application Flask s'exécutera
EXPOSE 5002 8000

# Commande pour démarrer l'application Flask
CMD ["waitress-serve", "--port=5002", "produit_api:app"]

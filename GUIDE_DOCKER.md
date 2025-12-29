# 🐳 Guide Docker - Plateforme BRVM

## 📦 Fichiers Docker Existants

✅ **Dockerfile** - Image de l'application Django
✅ **docker-compose.yml** - Orchestration complète (MongoDB + Django + Airflow)
✅ **docker-entrypoint.sh** - Script de démarrage automatique
✅ **.dockerignore** - Fichiers à exclure

## 🚀 Démarrage Rapide

### Option 1️⃣ : Tout en un (Recommandé)

```bash
# 1. Construire les images
docker-compose build

# 2. Démarrer tous les services
docker-compose up -d

# 3. Vérifier les logs
docker-compose logs -f web
```

**Services démarrés** :
- MongoDB : Port 27018
- Django Web : Port 8003
- Airflow Scheduler : Collecte automatique horaire

### Option 2️⃣ : Service par service

```bash
# MongoDB uniquement
docker-compose up -d mongodb

# Django Web
docker-compose up -d web

# Airflow
docker-compose up -d airflow-scheduler
```

## 📋 Commandes Utiles

### Gestion des conteneurs

```bash
# Voir les conteneurs actifs
docker-compose ps

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ Perte de données)
docker-compose down -v

# Redémarrer un service
docker-compose restart web

# Voir les logs
docker-compose logs web
docker-compose logs mongodb
docker-compose logs airflow-scheduler
```

### Accès aux conteneurs

```bash
# Shell dans le conteneur Django
docker-compose exec web bash

# Shell dans MongoDB
docker-compose exec mongodb mongosh

# Exécuter une commande Django
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py createsuperuser
```

### Collecte de données

```bash
# Lancer collecte manuelle BRVM
docker-compose exec web python collecter_quotidien_intelligent.py

# Vérifier les données
docker-compose exec web python show_complete_data.py

# Générer recommandations
docker-compose exec web python lancer_analyse_ia_rapide.py
```

## 🔧 Configuration (.env)

Créez un fichier `.env` à la racine :

```env
# MongoDB
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=VotreMotDePasseSecurise123
MONGODB_NAME=centralisation_db

# Django
DJANGO_SECRET_KEY=votre-cle-secrete-django-tres-longue-et-aleatoire
DJANGO_DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com

# Optionnel
BRVM_API_URL=
WORLDBANK_API_KEY=
```

## 📊 Volumes de Données

Les données sont persistées dans des volumes Docker :

```yaml
mongodb_data       # Base de données MongoDB
static_volume      # Fichiers statiques Django
media_volume       # Fichiers uploadés
```

### Sauvegarder les données

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup
docker cp plateforme_mongodb:/backup ./mongodb_backup_$(date +%Y%m%d)

# Restore MongoDB
docker cp ./mongodb_backup plateforme_mongodb:/restore
docker-compose exec mongodb mongorestore /restore
```

## 🌐 Déploiement Production

### 1. Build optimisé

```bash
# Build sans cache
docker-compose build --no-cache

# Build avec tag de version
docker build -t plateforme-brvm:v1.0 .
```

### 2. Variables d'environnement production

```env
DJANGO_DEBUG=False
ALLOWED_HOSTS=api.votredomaine.com,www.votredomaine.com
MONGO_ROOT_PASSWORD=mot-de-passe-tres-securise-aleatoire
DJANGO_SECRET_KEY=cle-secrete-generee-aleatoirement-50-caracteres-minimum
```

### 3. NGINX Reverse Proxy

Ajoutez ce service dans `docker-compose.yml` :

```yaml
  nginx:
    image: nginx:alpine
    container_name: plateforme_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - web
    networks:
      - plateforme_network
```

### 4. SSL/HTTPS avec Let's Encrypt

```bash
# Installer certbot
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone \
  -d api.votredomaine.com
```

## 🐛 Dépannage

### Conteneur ne démarre pas

```bash
# Voir les logs détaillés
docker-compose logs --tail=100 web

# Vérifier la configuration
docker-compose config

# Reconstruire l'image
docker-compose build --no-cache web
docker-compose up -d web
```

### Erreur MongoDB

```bash
# Vérifier la santé
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Voir les logs
docker-compose logs mongodb

# Redémarrer MongoDB
docker-compose restart mongodb
```

### Problème de permissions

```bash
# Ajuster les permissions
docker-compose exec web chown -R root:root /app/staticfiles
docker-compose exec web chmod -R 755 /app/staticfiles
```

### Port déjà utilisé

```bash
# Changer le port dans docker-compose.yml
ports:
  - "8001:8000"  # Au lieu de 8000:8000

# Ou arrêter le processus utilisant le port
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## 📈 Monitoring

### Logs en temps réel

```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f web
docker-compose logs -f mongodb
```

### Stats des conteneurs

```bash
# Utilisation CPU/RAM
docker stats

# Espace disque
docker system df
```

## 🔄 Mises à jour

```bash
# 1. Arrêter les services
docker-compose down

# 2. Mettre à jour le code
git pull origin main

# 3. Reconstruire les images
docker-compose build

# 4. Redémarrer
docker-compose up -d

# 5. Vérifier
docker-compose ps
docker-compose logs web
```

## 📦 Export/Import Image

### Sauvegarder l'image

```bash
# Build et save
docker build -t plateforme-brvm:latest .
docker save plateforme-brvm:latest | gzip > plateforme-brvm.tar.gz
```

### Charger l'image

```bash
# Sur un autre serveur
docker load < plateforme-brvm.tar.gz
docker-compose up -d
```

## 🚀 CI/CD avec GitHub Actions

Créez `.github/workflows/docker-deploy.yml` :

```yaml
name: Docker Build & Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t plateforme-brvm:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push plateforme-brvm:${{ github.sha }}
```

## 🔐 Sécurité

### Bonnes pratiques

✅ Ne jamais commiter `.env`
✅ Utiliser des secrets pour les mots de passe
✅ Mettre à jour régulièrement les images de base
✅ Scanner les vulnérabilités

```bash
# Scanner l'image
docker scan plateforme-brvm:latest

# Mettre à jour les dépendances
pip list --outdated
pip install --upgrade <package>
```

## 📞 Support

**Issues GitHub** : https://github.com/sanaboukary/ecodata/issues
**Documentation** : README.md

---

**Dernière mise à jour** : 29 décembre 2025

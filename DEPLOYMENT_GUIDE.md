# 🚀 Guide de Déploiement - Plateforme de Centralisation des Données Économiques

## ✅ État de Déployabilité

Votre plateforme est **PRÊTE POUR LE DÉPLOIEMENT** avec les caractéristiques suivantes :

### 📦 Stack Technique
- **Backend**: Django 5.2.8 + Django REST Framework 3.16.1
- **Base de données**: MongoDB 7.0 (avec authentification)
- **Collecte automatique**: Apache Airflow 3.1.2
- **Web Server**: Gunicorn + Nginx (reverse proxy)
- **Conteneurisation**: Docker + Docker Compose
- **Python**: 3.11

### 🎯 Fonctionnalités Déployées
✅ 5 dashboards professionnels (BRVM, Banque Mondiale, FMI, ONU, BAD)
✅ Collecte automatique horaire BRVM (24/7)
✅ Collecte hebdomadaire WorldBank, IMF, UN, AfDB
✅ API REST complète pour toutes les sources
✅ Interface Airflow pour monitoring
✅ Design moderne glassmorphism responsive
✅ 158 dépendances Python gérées
✅ Authentification MongoDB sécurisée

---

## 🐳 Déploiement avec Docker (RECOMMANDÉ)

### Prérequis
```bash
# Installer Docker Desktop (Windows/Mac) ou Docker Engine (Linux)
docker --version  # Doit être >= 24.0
docker-compose --version  # Doit être >= 2.20
```

### Étape 1: Configuration Environnement
```bash
# Copier le fichier d'environnement
cp .env.docker .env.production

# Éditer .env.production et modifier:
# - MONGO_ROOT_PASSWORD (mot de passe fort)
# - DJANGO_SECRET_KEY (générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - ALLOWED_HOSTS (votre domaine de production)
nano .env.production
```

### Étape 2: Build et Démarrage
```bash
# Build des images Docker
docker-compose build

# Démarrer tous les services
docker-compose --env-file .env.production up -d

# Vérifier les logs
docker-compose logs -f web
docker-compose logs -f airflow-scheduler
```

### Étape 3: Initialisation Base de Données
```bash
# Les migrations s'exécutent automatiquement via docker-entrypoint.sh
# Superutilisateur créé automatiquement: admin / admin123

# Modifier le mot de passe admin (IMPORTANT)
docker-compose exec web python manage.py changepassword admin
```

### Étape 4: Accès à la Plateforme
```
🌐 Application Django: http://votre-domaine.com/
🔧 Interface Airflow: http://votre-domaine.com/airflow/
📊 API REST: http://votre-domaine.com/api/
```

### Services Docker
```bash
# Voir les services actifs
docker-compose ps

# Arrêter les services
docker-compose down

# Redémarrer un service spécifique
docker-compose restart web
docker-compose restart airflow-scheduler

# Voir les logs
docker-compose logs -f [service_name]

# Accéder au shell d'un conteneur
docker-compose exec web bash
docker-compose exec mongodb mongosh
```

---

## 🖥️ Déploiement Traditionnel (Sans Docker)

### Prérequis
```bash
# Python 3.11+
python --version

# MongoDB 7.0+
mongod --version

# Installer les dépendances système
# Ubuntu/Debian:
sudo apt-get install python3.11 python3.11-venv mongodb postgresql-client libpq-dev gcc

# Windows: Installer MongoDB, Python 3.11 depuis les sites officiels
```

### Étape 1: Configuration Environnement
```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement
# Windows Git Bash:
source .venv/Scripts/activate
# Linux/Mac:
source .venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 2: Configuration MongoDB
```bash
# Démarrer MongoDB (si pas déjà actif)
# Windows: Démarrer le service MongoDB
# Linux:
sudo systemctl start mongodb

# Créer l'utilisateur admin MongoDB
mongosh
> use admin
> db.createUser({
    user: "SANA",
    pwd: "Boukary89@",
    roles: [{role: "readWrite", db: "centralisation_db"}]
  })
> exit
```

### Étape 3: Configuration Django
```bash
# Créer .env.production (copier depuis .env et modifier)
cp .env .env.production

# Éditer .env.production:
# - DJANGO_DEBUG=False
# - DJANGO_SECRET_KEY=<générer une nouvelle clé>
# - ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
# - MONGODB_URI=mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin

# Exécuter les migrations
python manage.py migrate

# Créer le superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### Étape 4: Démarrage avec Gunicorn
```bash
# Installer Gunicorn
pip install gunicorn

# Démarrer l'application
gunicorn plateforme_centralisation.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Étape 5: Configuration Airflow
```bash
# Initialiser Airflow
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init

# Créer un utilisateur Airflow
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@plateforme.local \
  --password admin123

# Démarrer le scheduler (terminal 1)
airflow scheduler

# Démarrer le webserver (terminal 2)
airflow webserver --port 8080
```

### Étape 6: Configuration Nginx (Production)
```bash
# Installer Nginx
sudo apt-get install nginx

# Copier la configuration
sudo cp nginx.conf /etc/nginx/sites-available/plateforme
sudo ln -s /etc/nginx/sites-available/plateforme /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

---

## 📊 Monitoring & Maintenance

### Vérifier l'État des Services
```bash
# Docker
docker-compose ps
docker-compose logs -f

# Traditionnel
systemctl status gunicorn
systemctl status nginx
systemctl status airflow-scheduler
```

### Surveillance MongoDB
```bash
# Connexion MongoDB
mongosh "mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin"

# Vérifier les données
> db.curated_observations.countDocuments()
> db.curated_observations.find({source: "BRVM"}).limit(5)
> db.ingestion_runs.find().sort({ts: -1}).limit(10)
```

### Logs Applicatifs
```bash
# Django logs
tail -f logs/django.log

# Airflow logs
tail -f airflow/logs/scheduler/latest/*.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Backup MongoDB
```bash
# Backup complet
mongodump --uri="mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin" --out=/backup/$(date +%Y%m%d)

# Restauration
mongorestore --uri="mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin" /backup/20250124/
```

---

## 🔒 Sécurité Production

### Checklist Sécurité
- [ ] `DJANGO_DEBUG=False` dans `.env.production`
- [ ] `DJANGO_SECRET_KEY` unique et aléatoire (50+ caractères)
- [ ] `ALLOWED_HOSTS` configuré avec domaines de production
- [ ] Mot de passe MongoDB complexe (min 16 caractères)
- [ ] Mot de passe superutilisateur Django changé
- [ ] HTTPS configuré avec certificat SSL (Let's Encrypt recommandé)
- [ ] Firewall configuré (ports 80, 443, 8080)
- [ ] MongoDB non exposé publiquement (port 27017/27018 fermé)
- [ ] Logs de sécurité activés
- [ ] Backups automatiques configurés

### Configuration HTTPS (Let's Encrypt)
```bash
# Installer Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtenir le certificat SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique (vérifié automatiquement)
sudo certbot renew --dry-run
```

---

## 🚀 Déploiement Cloud

### AWS EC2
```bash
# Instance recommandée: t3.medium (2 vCPU, 4GB RAM)
# Système: Ubuntu 22.04 LTS
# Stockage: 30GB GP3

# 1. Connexion SSH
ssh -i votre-cle.pem ubuntu@ip-publique

# 2. Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# 3. Cloner le projet
git clone <votre-repo>
cd plateforme

# 4. Suivre les étapes Docker ci-dessus
```

### DigitalOcean Droplet
```bash
# Droplet recommandé: Basic - 2 vCPU, 4GB RAM, 80GB SSD
# Système: Ubuntu 22.04

# 1. Accès initial
ssh root@ip-publique

# 2. Suivre les étapes Docker/Traditionnel
```

### Heroku
```bash
# Installer Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Créer l'application
heroku create plateforme-centralisation

# Ajouter MongoDB Atlas (gratuit jusqu'à 512MB)
heroku addons:create mongolab:sandbox

# Configurer les variables
heroku config:set DJANGO_SECRET_KEY="votre-cle"
heroku config:set DJANGO_DEBUG=False
heroku config:set MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/db"

# Déployer
git push heroku main

# Migrations
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

---

## 📈 Performance & Scalabilité

### Optimisations Recommandées
1. **Redis Cache** pour sessions Django
2. **CDN** (CloudFlare) pour fichiers statiques
3. **MongoDB Replica Set** pour haute disponibilité
4. **Load Balancer** pour plusieurs instances Django
5. **Celery** pour tâches asynchrones (alternative à Airflow)

### Monitoring Production
- **Sentry** pour tracking des erreurs
- **Prometheus + Grafana** pour métriques système
- **UptimeRobot** pour monitoring uptime
- **MongoDB Atlas** pour base de données managée

---

## 📞 Support & Maintenance

### Commandes Utiles
```bash
# Redémarrer tous les services
docker-compose restart

# Nettoyer les logs Airflow
find airflow/logs -type f -mtime +30 -delete

# Vider le cache Django
python manage.py clearcache

# Vérifier la santé des services
curl http://localhost:8000/health
curl http://localhost:8080/health
```

### Troubleshooting
```bash
# Problème connexion MongoDB
docker-compose logs mongodb
python verifier_connexion_db.py

# Problème Airflow
docker-compose logs airflow-scheduler
airflow dags list

# Problème Django
docker-compose logs web
python manage.py check --deploy
```

---

## 📝 Notes Importantes

1. **Premier Déploiement**: Prévoir 15-30 minutes pour build et initialisation
2. **Collecte BRVM**: Démarre automatiquement toutes les heures (24/7)
3. **Collecte Autres Sources**: Dimanche 3h AM (hebdomadaire)
4. **Backups**: Configurer sauvegarde quotidienne MongoDB
5. **Monitoring**: Vérifier Airflow UI pour statut des DAGs
6. **Mises à jour**: `git pull && docker-compose up -d --build`

---

## ✅ Validation Déploiement

Après déploiement, vérifier:
- [ ] Page d'accueil accessible (/)
- [ ] 5 dashboards fonctionnels (/dashboards/brvm/, /worldbank/, /imf/, /un/, /afdb/)
- [ ] API REST répond (/api/data/list/)
- [ ] Airflow UI accessible (/airflow/)
- [ ] DAGs activés et en cours d'exécution
- [ ] MongoDB contient des données (> 0 observations)
- [ ] Fichiers statiques chargés correctement
- [ ] HTTPS fonctionnel (production)
- [ ] Logs sans erreurs critiques

---

**🎉 Votre plateforme est maintenant déployée et opérationnelle !**

Pour toute question: Consultez les logs ou vérifiez PROJECT_STRUCTURE.md

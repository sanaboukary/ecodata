# Guide d'installation détaillé

## Prérequis système

### Windows
- Windows 10 ou supérieur
- PowerShell ou Git Bash
- Python 3.10 ou supérieur
- MongoDB 4.4 ou supérieur

### Linux/Mac
- Python 3.10+
- MongoDB 4.4+
- Git

## Installation de MongoDB

### Windows
1. Téléchargez MongoDB Community Server depuis [mongodb.com](https://www.mongodb.com/try/download/community)
2. Installez avec les paramètres par défaut
3. MongoDB Compass (interface graphique) est optionnel mais recommandé
4. Le service MongoDB démarre automatiquement

### Linux (Ubuntu/Debian)
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Mac
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

## Installation du projet

### 1. Télécharger le projet

Si vous utilisez Git :
```bash
git clone <url-du-repo>
cd "Implementation plateforme"
```

### 2. Créer l'environnement virtuel

**Windows (Git Bash)** :
```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Windows (PowerShell)** :
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/Mac** :
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

**Pour la production** :
```bash
pip install --upgrade pip
pip install -r requirements/base.txt
```

**Pour le développement** :
```bash
pip install -r requirements/dev.txt
```

### 4. Configuration de l'environnement

Copier le fichier d'exemple :
```bash
cp .env.example .env
```

Éditer `.env` avec vos paramètres :
```env
# Django
DJANGO_SECRET_KEY=votre-cle-secrete-unique-ici
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGODB_NAME=centralisation_db
MONGODB_URI=mongodb://localhost:27017

# API
HTTP_TIMEOUT=30

# BRVM (si vous avez un endpoint)
BRVM_API_URL=https://api.brvm.org/quotes

# Logging
LOG_LEVEL=INFO
```

**Générer une clé secrète Django** :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Vérifier la connexion MongoDB

```bash
python manage.py check
```

### 6. Créer les collections MongoDB

```bash
python manage.py migrate
```

### 7. Créer un super utilisateur (optionnel)

```bash
python manage.py createsuperuser
```

### 8. Collecter les fichiers statiques (production)

```bash
python manage.py collectstatic --noinput
```

## Lancement du serveur

### Mode développement
```bash
python manage.py runserver
```

Le serveur sera accessible sur : http://localhost:8000

### Avec un port personnalisé
```bash
python manage.py runserver 0.0.0.0:8080
```

### En arrière-plan (Linux/Mac)
```bash
nohup python manage.py runserver > logs/server.log 2>&1 &
```

## Vérification de l'installation

1. **Accéder au dashboard** : http://localhost:8000
2. **Vérifier l'API** : http://localhost:8000/api/ingestion/health/
3. **Admin Django** : http://localhost:8000/admin/

## Problèmes courants

### Erreur : "No module named 'django'"
```bash
# Vérifiez que l'environnement virtuel est activé
pip install -r requirements/base.txt
```

### Erreur de connexion MongoDB
```bash
# Vérifiez que MongoDB est démarré
# Windows : services.msc > MongoDB Server
# Linux/Mac : sudo systemctl status mongod

# Testez la connexion
mongo --eval "db.version()"
```

### Port 8000 déjà utilisé
```bash
# Utilisez un autre port
python manage.py runserver 8080
```

### Erreur djongo
```bash
# Assurez-vous d'utiliser la bonne version
pip install djongo==1.3.6
pip install pymongo==3.12.3
```

## Désinstallation

```bash
# Désactiver l'environnement virtuel
deactivate

# Supprimer l'environnement virtuel
rm -rf .venv

# Supprimer la base de données MongoDB
mongo
> use centralisation_db
> db.dropDatabase()
```

## Prochaines étapes

- Consultez le [Guide d'utilisation](USAGE.md)
- Configurez l'[ETL](ETL.md)
- Explorez l'[API](API.md)

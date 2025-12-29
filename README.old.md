# Plateforme de centralisation des données

## Prérequis
- Python 3.10+
- MongoDB en local ou accessible par URI

## Installation
```bash
# Dans le dossier du projet
python -m venv .venv
# Git Bash / PowerShell
source .venv/Scripts/activate
pip install -r requirements.txt
```

Créer un fichier `.env` (déjà créé) et ajuster si besoin:
```env
MONGODB_NAME=centralisation_db
MONGODB_URI=mongodb://localhost:27017
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Lancer le projet
```bash
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py runserver
```

## Endpoints
- Accueil tableau de bord: `GET /`
- Santé ingestion: `GET /api/ingestion/health/`
- Démarrer ingestion: `POST /api/ingestion/start/` (body JSON optionnel)
  - `scripts_dir`: chemin vers vos scripts
  - `pattern`: motif glob (par défaut `*.py`)

## Commande de gestion
Exécuter tous les scripts dans le dossier `scripts`:
```bash
.venv/Scripts/python manage.py run_ingestion --scripts-dir ./scripts --pattern "*.py"
```

Placez vos scripts d’extraction existants dans `scripts/` (ou indiquez le chemin) et assurez-vous qu’ils utilisent `pymongo` ou vos mécanismes pour écrire dans MongoDB.


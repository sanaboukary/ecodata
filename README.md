# Plateforme de Centralisation des Données# Plateforme de centralisation des données



![Django](https://img.shields.io/badge/Django-4.1.13-green.svg)## Prérequis

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)- Python 3.10+

![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)- MongoDB en local ou accessible par URI



## 📋 Description## Installation

```bash

Plateforme de centralisation et d'analyse de données économiques provenant de diverses sources internationales (BRVM, Banque Mondiale, FMI, ONU, BAD).# Dans le dossier du projet

python -m venv .venv

## 🚀 Fonctionnalités# Git Bash / PowerShell

source .venv/Scripts/activate

- **Dashboard interactif** : Visualisation des indicateurs économiquespip install -r requirements.txt

- **Explorateur de données** : Recherche et comparaison multi-critères```

- **Ingestion automatique** : ETL pour 5 sources de données

- **API REST** : Accès programmatique aux donnéesCréer un fichier `.env` (déjà créé) et ajuster si besoin:

- **Exports** : CSV pour analyses externes```env

- **Scheduler** : Mise à jour automatique des données BRVMMONGODB_NAME=centralisation_db

MONGODB_URI=mongodb://localhost:27017

## 🛠️ TechnologiesDJANGO_DEBUG=True

DJANGO_SECRET_KEY=change-me

- **Backend** : Django 4.1.13, Django REST FrameworkALLOWED_HOSTS=localhost,127.0.0.1

- **Base de données** : MongoDB (via Djongo)```

- **ETL** : Scripts Python personnalisés

- **Frontend** : HTML, CSS, JavaScript## Lancer le projet

- **Scheduler** : APScheduler```bash

.venv/Scripts/python manage.py migrate

## 📦 Structure du projet.venv/Scripts/python manage.py runserver

```

```

plateforme_centralisation/## Endpoints

├── dashboard/              # Application tableau de bord- Accueil tableau de bord: `GET /`

├── ingestion/             # Application d'ingestion de données- Santé ingestion: `GET /api/ingestion/health/`

├── scripts/               # Scripts ETL et connecteurs- Démarrer ingestion: `POST /api/ingestion/start/` (body JSON optionnel)

├── plateforme_centralisation/  # Configuration Django  - `scripts_dir`: chemin vers vos scripts

├── static/                # Fichiers statiques (CSS, JS)  - `pattern`: motif glob (par défaut `*.py`)

├── templates/             # Templates HTML

├── docs/                  # Documentation détaillée## Commande de gestion

├── logs/                  # Logs applicatifsExécuter tous les scripts dans le dossier `scripts`:

├── requirements/          # Dépendances Python```bash

├── .env                   # Variables d'environnement.venv/Scripts/python manage.py run_ingestion --scripts-dir ./scripts --pattern "*.py"

└── manage.py             # Point d'entrée Django```

```

Placez vos scripts d’extraction existants dans `scripts/` (ou indiquez le chemin) et assurez-vous qu’ils utilisent `pymongo` ou vos mécanismes pour écrire dans MongoDB.

## ⚙️ Installation


### Prérequis

- Python 3.10+
- MongoDB (local ou distant)
- Git

### Étapes d'installation

1. **Cloner le projet**
```bash
cd "Implementation plateforme"
```

2. **Créer un environnement virtuel**
```bash
python -m venv .venv
source .venv/Scripts/activate  # Sur Windows Git Bash
```

3. **Installer les dépendances**
```bash
pip install -r requirements/base.txt
```

4. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. **Initialiser la base de données**
```bash
python manage.py migrate
```

6. **Lancer le serveur**
```bash
python manage.py runserver
```

Accédez à : **http://localhost:8000**

## 📖 Documentation complète

- [Guide d'installation détaillé](docs/INSTALLATION.md)
- [Guide d'utilisation](docs/USAGE.md)
- [Architecture ETL](docs/ETL.md)
- [API Reference](docs/API.md)

## 🔌 Utilisation rapide

### Dashboard
- **Accueil** : http://localhost:8000
- **Explorateur** : http://localhost:8000/explorer/
- **Comparateur** : http://localhost:8000/comparateur/

### API d'ingestion
```bash
# Vérifier l'état
curl http://localhost:8000/api/ingestion/health/

# Démarrer une ingestion
curl -X POST http://localhost:8000/api/ingestion/start/
```

### Commandes de gestion

```bash
# Ingestion par source
python manage.py ingest_source --source brvm
python manage.py ingest_source --source worldbank

# Scheduler automatique (BRVM horaire)
python manage.py start_scheduler
```

## 📊 Sources de données

| Source | Description | Fréquence |
|--------|-------------|-----------|
| BRVM | Bourse Régionale des Valeurs Mobilières | Horaire |
| World Bank | Indicateurs de développement mondial | Manuelle |
| IMF | Fonds Monétaire International | Manuelle |
| UN SDG | Objectifs de Développement Durable | Manuelle |
| AfDB | Banque Africaine de Développement | Manuelle |

## 🧪 Tests

```bash
python manage.py test
```

## 📝 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

---

**Note** : Pour plus de détails, consultez la [documentation complète](docs/)
# ECODATA-plateforme

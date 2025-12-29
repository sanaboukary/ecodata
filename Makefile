.PHONY: help install install-dev setup start test test-coverage clean migrate shell createsuperuser lint format check-format scheduler logs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Afficher l'aide
	@echo "$(BLUE)Plateforme de Centralisation - Commandes disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Installer les dépendances de production
	pip install -r requirements/base.txt

install-dev: ## Installer les dépendances de développement
	pip install -r requirements/dev.txt

setup: ## Configuration initiale du projet
	@echo "$(BLUE)Configuration du projet...$(NC)"
	@bash setup.sh

start: ## Démarrer le serveur Django
	@bash start.sh

test: ## Exécuter les tests
	python manage.py test

test-coverage: ## Exécuter les tests avec couverture
	@bash test.sh --coverage

clean: ## Nettoyer les fichiers temporaires
	@echo "$(YELLOW)Nettoyage...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@echo "$(GREEN)✓ Nettoyage terminé$(NC)"

migrate: ## Appliquer les migrations
	python manage.py migrate

makemigrations: ## Créer des migrations
	python manage.py makemigrations

shell: ## Ouvrir le shell Django
	python manage.py shell

createsuperuser: ## Créer un super utilisateur
	python manage.py createsuperuser

lint: ## Vérifier le code (flake8)
	flake8 .

format: ## Formater le code (black + isort)
	@echo "$(BLUE)Formatage du code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✓ Code formaté$(NC)"

check-format: ## Vérifier le formatage sans modification
	black --check .
	isort --check .

scheduler: ## Démarrer le scheduler BRVM
	@bash scheduler.sh

logs: ## Afficher les logs en temps réel
	tail -f logs/server.log

# Commandes d'ingestion
ingest-brvm: ## Ingérer les données BRVM
	python manage.py ingest_source --source brvm

ingest-worldbank: ## Ingérer les données Banque Mondiale
	python manage.py ingest_source --source worldbank

ingest-imf: ## Ingérer les données FMI
	python manage.py ingest_source --source imf

ingest-un: ## Ingérer les données ONU
	python manage.py ingest_source --source un

ingest-afdb: ## Ingérer les données BAD
	python manage.py ingest_source --source afdb

# Commandes utiles
check: ## Vérifier la configuration Django
	python manage.py check

collectstatic: ## Collecter les fichiers statiques
	python manage.py collectstatic --noinput

runserver: ## Démarrer le serveur (alias de start)
	python manage.py runserver

# Docker (si utilisé plus tard)
docker-build: ## Construire l'image Docker
	docker build -t plateforme-centralisation .

docker-up: ## Démarrer les conteneurs
	docker-compose up -d

docker-down: ## Arrêter les conteneurs
	docker-compose down

docker-logs: ## Afficher les logs Docker
	docker-compose logs -f

# Base de données
db-shell: ## Ouvrir le shell MongoDB
	mongo centralisation_db

db-backup: ## Sauvegarder la base de données
	mongodump --db=centralisation_db --out=backups/$(shell date +%Y%m%d_%H%M%S)

db-restore: ## Restaurer la base de données (usage: make db-restore BACKUP=backups/20251106_100000)
	mongorestore --db=centralisation_db $(BACKUP)/centralisation_db

# Documentation
docs-serve: ## Lancer un serveur de documentation local
	@echo "Documentation disponible dans docs/"
	@echo "README: README.md"
	@echo "Installation: docs/INSTALLATION.md"
	@echo "Usage: docs/USAGE.md"
	@echo "ETL: docs/ETL.md"
	@echo "API: docs/API.md"

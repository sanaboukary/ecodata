# Plateforme de Centralisation - Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### À venir
- Interface d'administration améliorée
- Notifications par email
- Export Excel
- API GraphQL
- Déploiement Docker

## [1.0.0] - 2025-11-06

### Ajouté
- Dashboard interactif avec visualisation des indicateurs
- Explorateur de données multi-critères
- Comparateur de pays
- Système d'ingestion ETL pour 5 sources :
  - BRVM (Bourse Régionale)
  - Banque Mondiale
  - FMI
  - ONU SDG
  - BAD (Banque Africaine de Développement)
- Scheduler automatique pour BRVM (horaire)
- API REST avec endpoints :
  - Health check
  - Démarrage d'ingestion
  - Liste des KPIs
  - Recherche de données
  - Exports CSV
- Système de favoris pour l'explorateur
- Autocomplétion pour indicateurs et pays
- Commandes de gestion Django personnalisées
- Tests unitaires pour dashboard et ingestion
- Documentation complète (Installation, Usage, ETL, API)
- Scripts de démarrage (setup.sh, start.sh, scheduler.sh, test.sh)
- Configuration multi-environnements (dev, prod)
- Logs structurés
- .gitignore et configuration des outils de développement

### Architecture
- Django 4.1.13
- MongoDB via Djongo
- Django REST Framework
- APScheduler pour les tâches planifiées
- Structure modulaire avec apps `dashboard` et `ingestion`

### Documentation
- README.md complet avec badges
- Guide d'installation détaillé
- Guide d'utilisation avec exemples
- Documentation ETL complète
- Référence API avec exemples curl/Python/JS
- Guide de contribution

### Configuration
- Variables d'environnement via .env
- Requirements séparés (base, dev, prod)
- Configuration pytest, flake8, black, isort
- Scripts shell pour automatisation

## Notes de version

### Compatibilité
- Python 3.10+
- MongoDB 4.4+
- Django 4.1.13

### Dépendances principales
- Django==4.1.13
- Djongo==1.3.6
- pymongo==3.12.3
- djangorestframework==3.15.1
- APScheduler>=3.10.0
- pandas>=2.0
- wbdata>=1.0

### Migration depuis une version antérieure
Première version stable, pas de migration nécessaire.

### Problèmes connus
- Djongo ne supporte pas toutes les fonctionnalités de l'ORM Django
- Les tests nécessitent MongoDB en local
- Le scheduler BRVM nécessite un endpoint API valide

### Remerciements
Merci à tous les contributeurs et utilisateurs bêta !

---

[Unreleased]: https://github.com/votre-repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/votre-repo/releases/tag/v1.0.0

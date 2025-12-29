# GUIDE NETTOYAGE PROJET POUR GITHUB

## ✅ FICHIERS ESSENTIELS À GARDER

### Core Django
- manage.py
- requirements.txt
- plateforme_centralisation/
- dashboard/
- ingestion/
- users/
- static/
- templates/
- media/

### Configuration
- .env.example (pas .env !)
- .gitignore
- .dockerignore
- Dockerfile
- docker-compose.yml
- nginx.conf

### Scripts essentiels
- `collecter_quotidien_intelligent.py` - Collecteur principal BRVM
- `collecter_csv_automatique.py` - Import CSV automatique
- `collecter_toutes_47_actions.py` - Collecte 47 actions
- `scripts/connectors/` - Tous les connecteurs

### Airflow
- `airflow/dags/` - DAGs de collecte automatique
- `airflow/` (structure de base)

### Documentation
- README.md
- PROJECT_STRUCTURE.md
- PIPELINE_STRUCTURE.txt
- CHANGELOG.md
- DEPLOYMENT_GUIDE.md
- docs/

## ❌ FICHIERS À SUPPRIMER

### 1. Tests et Debug (100+ fichiers)
```bash
rm -f test_*.py
rm -f check_*.py
rm -f verif_*.py
rm -f debug_*.py
rm -f diagnostic_*.py
rm -f explore_*.py
rm -f analyze_*.py
rm -f analyser_*.py
```

### 2. Scripts d'affichage (30+ fichiers)
```bash
rm -f afficher_*.py
rm -f lister_*.py
rm -f show_*.py
rm -f voir_*.py
```

### 3. Scripts obsolètes collecte (40+ fichiers)
```bash
rm -f collecter_brvm_*.py  # (garder collecter_toutes_47_actions.py)
rm -f collecter_cours_*.py
rm -f collecter_simple_*.py
rm -f mettre_a_jour_*.py
rm -f corriger_*.py
rm -f saisie_*.py
rm -f sauv_*.py
```

### 4. Scripts BAT Windows (20+ fichiers)
```bash
rm -f *.bat
```

### 5. Fichiers temporaires
```bash
rm -f *.log
rm -f *.txt  # Garder PIPELINE_STRUCTURE.txt
rm -f backup_*.json
rm -f backup_*.csv
rm -f *_2025*.json
rm -f top5_*.json
rm -f recommandations_*.json
rm -f rapport_*.json
```

### 6. HTML de scraping
```bash
rm -f *.html  # Sauf templates/
rm -f brvm_scrape_*.html
rm -f brvm_selenium_*.html
```

### 7. CSV temporaires
```bash
rm -f cours_brvm_*.csv
rm -f historique_brvm_*_PARTIEL_*.csv
rm -f donnees_reelles_*.csv
```

### 8. Dossiers à nettoyer
```bash
rm -rf bulletins_brvm/*
rm -rf logs/*
rm -rf csv/*
rm -rf csv_brvm/*
```

### 9. PDFs temporaires
```bash
rm -f *.pdf  # Garder docs/*.pdf si important
```

## 📊 RÉSULTAT ATTENDU

**Avant nettoyage:** ~300-400 fichiers Python
**Après nettoyage:** ~50-80 fichiers Python essentiels

**Espace libéré:** ~100-200 MB

## 🚀 COMMANDES RAPIDES

### Nettoyage automatique (recommandé)
```bash
python nettoyer_projet_github.py
```

### Aperçu sans supprimer
```bash
python apercu_nettoyage.py
```

### Nettoyage manuel sélectif
```bash
# Supprimer tous les tests
find . -name "test_*.py" -type f -delete

# Supprimer tous les checks
find . -name "check_*.py" -type f -delete

# Supprimer tous les logs
find . -name "*.log" -type f -delete

# Supprimer les BAT
find . -name "*.bat" -type f -delete
```

## ⚠️ ATTENTION NE PAS SUPPRIMER

- `.git/` - Historique Git
- `.venv/` - Environnement Python
- `dashboard/` - Application principale
- `ingestion/` - Pipeline ETL
- `plateforme_centralisation/` - Configuration Django
- `scripts/connectors/` - Connecteurs API
- `airflow/dags/` - Automatisation
- `static/` - CSS/JS
- `templates/` - Templates HTML

## 📋 CHECKLIST FINALE

Après nettoyage, vérifier :

1. ✅ L'application démarre : `python manage.py runserver`
2. ✅ Les collectes fonctionnent : `python collecter_quotidien_intelligent.py --rapport`
3. ✅ .gitignore à jour
4. ✅ requirements.txt complet
5. ✅ README.md à jour
6. ✅ Tests de base passent

## 🔄 GIT WORKFLOW APRÈS NETTOYAGE

```bash
# 1. Vérifier le statut
git status

# 2. Ajouter les suppressions
git add -A

# 3. Commit
git commit -m "Nettoyage projet pour production - suppression fichiers obsolètes"

# 4. Push
git push origin main
```

## 💡 CONSEILS

- **Faire un backup** avant nettoyage massif
- Tester l'application après nettoyage
- Garder une copie locale des scripts de test si besoin futur
- Documenter les scripts conservés dans README.md

# Copilot Instructions – Plateforme de Centralisation des Données

## 🏗️ Architecture & Data Flow

**Django 4.1.13** app for West African economic data centralization (BRVM, World Bank, IMF, UN SDG, AfDB). Windows development environment with Git Bash shell.

### 🎯 Mission Principale : Trading & Investissement BRVM
Plateforme d'aide à la décision pour investisseurs ouest-africains, basée sur 4 piliers :
1. **Recommandations automatiques** : Analyse technique + fondamentale → signaux buy/hold/sell
2. **Alertes temps réel** : Notifications sur variations significatives, franchissement de seuils
3. **Publications financières** : Rapports annuels, communiqués, documents réglementaires (PDF)
4. **Contexte macroéconomique** : Corrélation BRVM ↔ indicateurs économiques (WB/IMF/UN)

**⚠️ CRITIQUE : DONNÉES RÉELLES UNIQUEMENT - POLITIQUE ZÉRO TOLÉRANCE**
- **JAMAIS de données simulées/fictives/estimées** pour les prix BRVM
- **JAMAIS de génération automatique** de valeurs en cas de manque
- **Toujours vérifier** `attrs.data_quality` dans curated_observations
- **Sources valides UNIQUEMENT** : `REAL_MANUAL` (saisie officielle) ou `REAL_SCRAPER` (scraping vérifié)
- **En cas de manque** : NE PAS générer → système reste inactif → alerter pour action manuelle
- **Stratégies autorisées** : Scraping site BRVM → Saisie manuelle → AUCUNE collecte
- **Collecteur intelligent** : `collecter_quotidien_intelligent.py` (scraping puis saisie ou rien)

**ETL Pipeline (Critical):**
```
scripts/connectors/*.py → scripts/pipeline.py → MongoDB collections
```
- `raw_events`: Immutable audit trail of API responses
- `curated_observations`: **Always query here** - normalized schema `{source, dataset, key, ts, value, attrs}`
- `ingestion_runs`: Execution logs with status, duration, obs_count

**Django Apps:**
- `ingestion/`: ETL management commands + REST API endpoints
- `dashboard/`: **Only `dashboard/views.py` is production code** (others are demos/prototypes)
- `users/`: RBAC (role-based access control)

## ⚡️ Critical Patterns & Conventions

### MongoDB Access
```python
from plateforme_centralisation.mongo import get_mongo_db
client, db = get_mongo_db()  # Always use this
# Use PyMongo directly - NOT Django ORM/Djongo models
docs = list(db.curated_observations.find({'source': 'BRVM'}).limit(100))
```

### Data Schema (curated_observations)
```python
{
  "source": "BRVM",           # BRVM|WorldBank|IMF|UN_SDG|AfDB|BRVM_PUBLICATIONS
  "dataset": "STOCK_PRICE",   # Logical grouping
  "key": "SONATEL.BC",        # Unique identifier (symbol, country code, etc.)
  "ts": "2024-12-08",         # ISO date string
  "value": 15500.0,           # Primary metric
  "attrs": {                  # Source-specific metadata
    "open": 15400, "high": 15600, "volume": 1200,
    "sector": "Telecommunications", "country": "SN"
  }
}
```

### Adding New Data Sources
1. Create connector: `scripts/connectors/new_source.py` with `fetch_new_source()` → returns raw records
2. Add normalizer in `scripts/pipeline.py`: `normalize_new_source(records)` → returns curated obs
3. Register in `scripts/pipeline.py:run_ingestion()` switch statement
4. Update `ingestion/management/commands/ingest_source.py` choices
5. Create Airflow DAG in `airflow/dags/` for scheduling (use existing as template)

### Scheduler Pattern
- **Dev**: APScheduler via `python manage.py start_scheduler`
- **Prod**: Airflow on Windows (background service via `start_airflow_background.bat`)
  - **DAG Principal** : `brvm_collecte_quotidienne_reelle.py` (17h lun-ven, données réelles UNIQUEMENT)
  - **Politique stricte** : Scraping → Saisie manuelle → AUCUNE collecte (pas d'estimation)
  - **Vérifications** : Présence données + Qualité 100% réelle + Couverture minimale
  - Autres DAGs: worldbank_dag, imf_dag, afdb_un_dag (contexte macro)
  - Logs: `airflow/logs/` for debugging
  - Web UI: http://localhost:8080 (admin/admin)
  - Check status: `check_airflow_status.bat`

## 🛠️ Developer Workflows

### Environment Setup (Git Bash)
```bash
source .venv/Scripts/activate
python manage.py runserver  # or: make start
```

### Data Ingestion
```bash
# Manual ingestion
python manage.py ingest_source --source brvm
python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI
python manage.py ingest_source --source imf --series PCPI_IX --area CI

# BRVM: Mise à jour cours RÉELS (PRIORITAIRE)
python mettre_a_jour_cours_brvm.py           # Saisie manuelle officielle
python scripts/connectors/brvm_scraper_production.py  # Scraping site BRVM

# Import CSV automatique (NOUVEAU - Recommandé pour historique massif)
python collecter_csv_automatique.py --dry-run     # Test
python collecter_csv_automatique.py               # Import réel
python collecter_csv_automatique.py --dossier ./data_historiques  # Dossier spécifique

# Vérification qualité données BRVM
python verifier_cours_brvm.py                # Check data_quality field
python verifier_historique_60jours.py        # Check 60 days coverage

# Via REST API
curl -X POST http://localhost:8000/api/ingestion/start/ \
  -H "Content-Type: application/json" \
  -d '{"source": "brvm"}'
```

### Collecte BRVM : Données Réelles Uniquement
**PROCÉDURE QUOTIDIENNE (16h30 après clôture BRVM)** :

**Option A - Collecte intelligente automatique** (⭐ RECOMMANDÉ) :
```bash
# Collecteur intelligent : Scraping → Saisie manuelle → Rien
python collecter_quotidien_intelligent.py

# Rapport sans collecter
python collecter_quotidien_intelligent.py --rapport

# Airflow automatique (17h lun-ven)
start_airflow_background.bat
# Activer DAG : brvm_collecte_quotidienne_reelle
```

**Option B - Scraping manuel** (si site accessible) :
```bash
python scripts/connectors/brvm_scraper_production.py
# Utilise BeautifulSoup + contournement SSL
```

**Option C - Saisie manuelle** (5-10 min, toujours possible) :
```bash
# Aller sur https://www.brvm.org/fr/investir/cours-et-cotations
# Modifier VRAIS_COURS_BRVM dans mettre_a_jour_cours_brvm.py
python mettre_a_jour_cours_brvm.py
```

**🔴 POLITIQUE STRICTE** :
- Si scraping échoue ET saisie manuelle non faite → AUCUNE donnée ajoutée
- JAMAIS d'estimation automatique
- JAMAIS de simulation de valeurs
- En cas d'échec total → Notification + Action manuelle requise

**⚠️ NE JAMAIS utiliser `scripts/connectors/brvm.py` en production** → contient données simulées

**📊 Constitution historique 60 jours (pour trading hebdomadaire)** :

**Option A - Import CSV automatique** (⭐ RECOMMANDÉ pour volumes importants) :
```bash
# 1. Préparer CSV avec format :
#    DATE,SYMBOL,CLOSE,VOLUME,VARIATION
#    2025-12-08,SNTS,15500,8500,2.3

# 2. Tester import
python collecter_csv_automatique.py --dry-run

# 3. Import réel
python collecter_csv_automatique.py

# 4. Vérifier : ~2820 observations (60j × 47 actions)
python verifier_historique_60jours.py
```

**Option B - Parser bulletins PDF BRVM** :
```bash
# 1. Télécharger 60 bulletins PDF BRVM dans bulletins_brvm/
# 2. Parser automatiquement
python parser_bulletins_brvm_pdf.py
# 3. Importer le CSV généré
python importer_csv_brvm.py historique_brvm_60jours.csv
# 4. Vérifier : ~2820 observations (60j × 47 actions)
python verifier_historique_60jours.py
```

**Option C - Import manuel progressif** (plus lent) :
```bash
# Saisie quotidienne via script
python mettre_a_jour_cours_brvm.py
```

**📋 Supports multiples** :
- ✅ CSV : `collecter_csv_automatique.py` (détection auto BRVM/WB/IMF/AfDB/UN)
- ✅ PDF : `parser_bulletins_brvm_pdf.py` (bulletins officiels BRVM)
- ✅ API : `scripts/connectors/brvm_scraper_production.py` (scraping temps réel)
- ✅ Manuel : `mettre_a_jour_cours_brvm.py` (saisie guidée)

### Debug Workflows (Production Tools)
```bash
python show_complete_data.py         # Full data report (obs count by source)
python show_ingestion_history.py     # Execution history (success/error rates)
python verifier_connexion_db.py      # Test MongoDB connection
check_airflow_status.bat             # Check if Airflow processes running
```

### Airflow Management
```bash
start_airflow_background.bat         # Start scheduler + webserver
# Processes run detached - check logs in airflow/logs/
# Kill with Task Manager if needed (search "python airflow")
```

## 🧩 Key Files Reference

| File/Dir | Purpose |
|----------|---------|
| `scripts/pipeline.py` | ETL orchestrator - `run_ingestion(source, **params)` entry point |
| `scripts/mongo_utils.py` | `write_raw()`, `upsert_observations()`, `log_ingestion_run()` |
| `scripts/connectors/brvm_scraper_production.py` | **PRODUCTION** - Scraping cours réels BRVM |
| `mettre_a_jour_cours_brvm.py` | **PRODUCTION** - Saisie manuelle cours réels |
| `scripts/connectors/brvm.py` | ⚠️ **DEV ONLY** - Données simulées, NE PAS UTILISER |
| `scripts/connectors/worldbank.py` | Connector World Bank API |
| `dashboard/views.py` | **Production APIs** - all JSON endpoints + HTML views |
| `airflow/dags/` | Airflow DAGs for automated scheduling |
| `Makefile` | Shortcut commands (make start, make test, make clean, etc.) |

## 🔑 Environment Variables (.env)

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_NAME=centralisation_db
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
BRVM_API_URL=                    # Empty = use mock data
```

## 🧭 Troubleshooting Checklist

| Symptom | Diagnosis Command | Fix |
|---------|------------------|-----|
| No dashboard data | `python show_complete_data.py` | Run `python manage.py ingest_source --source brvm` |
| Ingestion failed | `python show_ingestion_history.py` | Check error_msg in ingestion_runs collection |
| MongoDB connection error | `python verifier_connexion_db.py` | Verify MongoDB service running + URI in .env |
| Airflow not collecting | `check_airflow_status.bat` | Run `start_airflow_background.bat` |
| Old/stale data | Check `airflow/logs/` | Unpause DAG in Airflow UI, check schedule |

## 📋 Data Sources Overview

### BRVM (Priorité #1 - Coeur du système)
- **47 actions cotées** à la BRVM
- **Collecte horaire** : 9h-16h jours ouvrables
- **70+ attributs par action** :
  - Prix & volumes (OHLCV)
  - Performance (variations J/S/M/A, YTD)
  - Valorisation (market cap, PE, PB, EPS)
  - Dividendes (yield, payout ratio)
  - Technique (SMA 20/50, RSI, beta, support/resistance)
  - Fondamentaux (ROE, ROA, debt/equity, current ratio)
  - **Recommandations** (buy/hold/sell, target price, consensus)
  - **Scores qualité** (liquidité, croissance, dividende)
- **Publications** : Rapports annuels, communiqués, documents financiers (PDFs)
- **Module d'analyse** : `dashboard/correlation_engine.py`, `dashboard/alert_service.py`, `dashboard/backtest_service.py`

### World Bank (Contexte macroéconomique)
- **35+ indicateurs** × 15 pays ouest-africains
- **Collecte mensuelle** le 15 à 2h00
- **Catégories** : Démographie, économie, santé, éducation, infrastructure
- **Usage** : Corrélation PIB/inflation/population ↔ performance BRVM par pays

### IMF (Indicateurs monétaires & conjoncture)
- **20+ séries** : CPI, GDP, réserves, taux de change
- **Collecte mensuelle** le 1er à 2h30
- **Usage** : Analyse impact inflation/taux de change sur valorisations BRVM

### AfDB + UN SDG (Contexte développement)
- **AfDB** : 6 indicateurs × 8 pays (dette, croissance, IDE, balance commerciale) - trimestriel
- **UN SDG** : 8 séries ODD (chômage, pauvreté, mortalité, éducation) - trimestriel
- **Usage** : Facteurs structurels influençant croissance long terme

---

**See also:** `README.md`, `PROJECT_STRUCTURE.md`, `AIRFLOW_SETUP.md`

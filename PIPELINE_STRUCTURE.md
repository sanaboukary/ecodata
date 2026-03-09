# STRUCTURE DU PIPELINE ETL - Plateforme de Centralisation des Données
# =======================================================================

## 1. ARCHITECTURE GLOBALE

```
SOURCES → CONNECTEURS → PIPELINE → NORMALISATION → MONGODB → UTILISATION
```

## 2. SOURCES DE DONNEES

### A. BRVM (Bourse Régionale des Valeurs Mobilières)
- **Type**: Données boursières temps réel
- **Collecte**: Scraping web + API
- **Fréquence**: Horaire (9h-16h jours ouvrables)
- **Données**: 47 actions cotées
- **Métriques**: Prix (OHLC), volumes, capitalisation, ratios financiers, indicateurs techniques

### B. World Bank (Banque Mondiale)
- **Type**: Indicateurs macroéconomiques
- **Collecte**: API REST officielle
- **Fréquence**: Mensuelle (15 du mois à 2h00)
- **Données**: 35+ indicateurs × 15 pays ouest-africains
- **Métriques**: PIB, population, inflation, chômage, dette, commerce

### C. IMF (Fonds Monétaire International)
- **Type**: Séries monétaires et conjoncturelles
- **Collecte**: API SDMX
- **Fréquence**: Mensuelle (1er du mois à 2h30)
- **Données**: 20+ séries × 8 pays BRVM
- **Métriques**: IPC, PIB réel, croissance, inflation, réserves

### D. AfDB (Banque Africaine de Développement)
- **Type**: Indicateurs de développement
- **Collecte**: API SDMX
- **Fréquence**: Trimestrielle
- **Données**: 6 indicateurs × 8 pays
- **Métriques**: Dette, croissance, IDE, balance commerciale

### E. UN SDG (Objectifs de Développement Durable ONU)
- **Type**: Indicateurs ODD
- **Collecte**: API UN Data
- **Fréquence**: Trimestrielle
- **Données**: 8 séries × pays africains
- **Métriques**: Pauvreté, éducation, santé, environnement

## 3. CONNECTEURS (scripts/connectors/)

Chaque connecteur est responsable de l'EXTRACTION des données depuis sa source:

```python
# scripts/connectors/brvm_scraper_production.py
def scrape_brvm_data() -> List[Dict]:
    """Scrape données BRVM en temps réel"""
    # Stratégie 3-tier:
    # 1. BeautifulSoup (rapide, léger)
    # 2. Selenium headless (si JS requis)
    # 3. Selenium visible (fallback)
    return records  # List[{"symbol": "SNTS", "close": 15500, ...}]

# scripts/connectors/worldbank.py
def fetch_worldbank_indicator(indicator, date, country) -> List[Dict]:
    """Récupère indicateur World Bank via API"""
    # Appel: http://api.worldbank.org/v2/country/{country}/indicator/{indicator}
    return observations  # Déjà normalisé

# scripts/connectors/imf.py
def fetch_imf_compact(dataset, key) -> List[Dict]:
    """Récupère série IMF via API SDMX"""
    # Appel: https://www.imf.org/external/datamapper/api/v1/{dataset}/{key}
    return observations  # Déjà normalisé

# scripts/connectors/afdb.py
def fetch_afdb_sdmx(dataset, key) -> List[Dict]:
    """Récupère données AfDB via API SDMX"""
    return observations

# scripts/connectors/un_sdg.py
def fetch_un_sdg(series, area, time) -> List[Dict]:
    """Récupère données UN SDG"""
    return observations
```

## 4. PIPELINE PRINCIPAL (scripts/pipeline.py)

Le pipeline orchestre le flux ETL pour toutes les sources:

```python
def run_ingestion(source: str, **kwargs) -> int:
    """
    Point d'entrée unique pour l'ingestion de données
    
    Args:
        source: "brvm" | "worldbank" | "imf" | "afdb" | "un"
        **kwargs: Paramètres spécifiques à la source
                  Ex: indicator="SP.POP.TOTL", country="CI"
    
    Returns:
        obs_count: Nombre d'observations insérées/mises à jour
    """
    db = get_db(MONGO_URI, MONGO_DB)
    start = time.time()
    
    # 1. EXTRACTION - Appel du connecteur approprié
    if source == "brvm":
        recs = fetch_brvm()
    elif source == "worldbank":
        obs = fetch_worldbank_indicator(kwargs["indicator"], kwargs["country"])
    # ... autres sources
    
    # 2. SAUVEGARDE RAW - Audit trail immuable
    write_raw(db, source, recs)
    
    # 3. NORMALISATION - Transformation vers schéma unifié
    if source == "brvm":
        obs = normalize_brvm(recs)
    # World Bank/IMF/AfDB/UN retournent déjà format normalisé
    
    # 4. SAUVEGARDE CURATED - Collection principale
    upsert_observations(db, obs)
    
    # 5. LOG EXECUTION - Traçabilité
    log_ingestion_run(db, source, status, obs_count, duration, error_msg, kwargs)
    
    return obs_count
```

## 5. NORMALISATION - Schéma Unifié

Toutes les sources sont transformées vers un schéma commun:

```python
{
  "source": "BRVM",           # Source de données
  "dataset": "QUOTES",        # Sous-ensemble logique
  "key": "SNTS",              # Identifiant unique (symbole, pays, etc.)
  "ts": "2026-01-06",         # Date/timestamp ISO
  "value": 15500.0,           # Valeur principale (prix, métrique)
  "attrs": {                  # Attributs spécifiques à la source
    "open": 15400,
    "high": 15600,
    "low": 15300,
    "volume": 1200,
    "market_cap": 750000000,
    "pe_ratio": 12.5,
    "dividend_yield": 4.2,
    "rsi": 68.5,
    "macd": 120.3,
    "recommendation": "BUY",
    "sector": "Telecommunications",
    "country": "SN"
  }
}
```

### Fonction de normalisation BRVM:

```python
def normalize_brvm(records: List[Dict]) -> List[Dict]:
    """Normalise les enregistrements BRVM vers le schéma curated"""
    out = []
    for r in records:
        attrs = {
            # Prix de base
            "open": r["open"], 
            "high": r["high"], 
            "low": r["low"], 
            "volume": r["volume"],
            
            # Métadonnées
            "name": r.get("name"),
            "sector": r.get("sector"),
            "country": r.get("country"),
            
            # Performance
            "day_change_pct": r.get("day_change_pct", 0),
            "week_change_pct": r.get("week_change_pct", 0),
            "ytd_change_pct": r.get("ytd_change_pct", 0),
            
            # Valorisation
            "market_cap": r.get("market_cap", 0),
            "pe_ratio": r.get("pe_ratio", 0),
            "pb_ratio": r.get("pb_ratio", 0),
            "eps": r.get("eps", 0),
            
            # Dividendes
            "dividend_yield": r.get("dividend_yield", 0),
            "payout_ratio": r.get("payout_ratio", 0),
            
            # Analyse Technique
            "sma_20": r.get("sma_20", 0),
            "sma_50": r.get("sma_50", 0),
            "rsi": r.get("rsi", 50),
            "beta": r.get("beta", 1.0),
            
            # Santé Financière
            "roe": r.get("roe", 0),
            "roa": r.get("roa", 0),
            "debt_to_equity": r.get("debt_to_equity", 0),
            
            # Recommandations
            "recommendation": r.get("recommendation", "Hold"),
            "target_price": r.get("target_price", 0),
            
            # Qualité
            "data_quality": r.get("data_quality", "REAL_MANUAL")
        }
        
        out.append({
            "source": "BRVM", 
            "dataset": "QUOTES", 
            "key": r["symbol"],
            "ts": r["ts"], 
            "value": r["close"],  # Prix de clôture = valeur principale
            "attrs": attrs
        })
    return out
```

## 6. MONGODB - Collections

### A. curated_observations (PRINCIPALE - Always query here)
```javascript
{
  "_id": ObjectId("..."),
  "source": "BRVM",
  "dataset": "QUOTES",
  "key": "SNTS",
  "ts": "2026-01-06",
  "value": 15500.0,
  "attrs": { /* 70+ attributs */ }
}

// Index unique pour éviter doublons
db.curated_observations.createIndex(
  {source: 1, dataset: 1, key: 1, ts: 1}, 
  {unique: true}
)
```

### B. raw_events (AUDIT TRAIL - Immuable)
```javascript
{
  "_id": ObjectId("..."),
  "source": "BRVM",
  "ingested_at": ISODate("2026-01-06T12:00:00Z"),
  "data": [ /* Réponse API brute */ ]
}
```

### C. ingestion_runs (LOGS - Traçabilité)
```javascript
{
  "_id": ObjectId("..."),
  "source": "BRVM",
  "status": "success",
  "start_time": ISODate("2026-01-06T12:00:00Z"),
  "end_time": ISODate("2026-01-06T12:01:23Z"),
  "duration_sec": 83.4,
  "obs_count": 47,
  "error_msg": null,
  "params": {}
}
```

## 7. ORCHESTRATION - Déclenchement de l'ingestion

### A. MANUEL (Django Management Command)
```bash
# BRVM
python manage.py ingest_source --source brvm

# World Bank avec paramètres
python manage.py ingest_source --source worldbank \
  --indicator SP.POP.TOTL \
  --country CI

# IMF
python manage.py ingest_source --source imf \
  --series PCPI_IX \
  --area CI
```

### B. PROGRAMMATIQUE (REST API)
```bash
# Via POST request
curl -X POST http://localhost:8000/api/ingestion/start/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "brvm"
  }'

# Avec paramètres
curl -X POST http://localhost:8000/api/ingestion/start/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "worldbank",
    "indicator": "SP.POP.TOTL",
    "country": "CI"
  }'
```

### C. AUTOMATIQUE (Airflow DAGs)
```python
# airflow/dags/worldbank_dag.py
@dag(schedule_interval='0 2 15 * *')  # Mensuel, 15 à 2h00
def worldbank_data_collection():
    for indicator in WORLDBANK_INDICATORS:
        for country in BRVM_COUNTRIES:
            ingest_task = PythonOperator(
                task_id=f'ingest_wb_{indicator}_{country}',
                python_callable=run_ingestion,
                op_kwargs={
                    'source': 'worldbank',
                    'indicator': indicator,
                    'country': country
                }
            )

# airflow/dags/brvm_complete_daily.py
@dag(schedule_interval='0 17 * * 1-5')  # Quotidien à 17h lun-ven
def brvm_daily_collection():
    ingest_brvm = PythonOperator(
        task_id='ingest_brvm',
        python_callable=run_ingestion,
        op_kwargs={'source': 'brvm'}
    )
```

### D. SCRIPT DIRECT (Python)
```python
from scripts.pipeline import run_ingestion

# BRVM
obs_count = run_ingestion('brvm')
print(f"{obs_count} observations collectées")

# World Bank
obs_count = run_ingestion('worldbank', 
                         indicator='SP.POP.TOTL', 
                         country='CI')
```

## 8. UTILITAIRES (scripts/mongo_utils.py)

Fonctions communes pour interagir avec MongoDB:

```python
def get_db(uri, db_name):
    """Connexion MongoDB"""
    client = MongoClient(uri)
    return client[db_name]

def write_raw(db, source, data):
    """Sauvegarde audit trail (raw_events)"""
    db.raw_events.insert_one({
        'source': source,
        'ingested_at': datetime.now(),
        'data': data
    })

def upsert_observations(db, observations):
    """Insert/Update curated_observations (évite doublons)"""
    for obs in observations:
        db.curated_observations.update_one(
            {
                'source': obs['source'],
                'dataset': obs['dataset'],
                'key': obs['key'],
                'ts': obs['ts']
            },
            {'$set': obs},
            upsert=True
        )

def log_ingestion_run(db, source, status, obs_count, duration, error_msg, params):
    """Log exécution dans ingestion_runs"""
    db.ingestion_runs.insert_one({
        'source': source,
        'status': status,
        'start_time': datetime.now(),
        'duration_sec': duration,
        'obs_count': obs_count,
        'error_msg': error_msg,
        'params': params
    })
```

## 9. FLUX COMPLET - Exemple BRVM

```
1. DÉCLENCHEMENT
   └─► python manage.py ingest_source --source brvm
   
2. PIPELINE.run_ingestion('brvm')
   │
   ├─► EXTRACTION: fetch_brvm()
   │   └─► brvm_scraper_production.py scrape le site BRVM
   │   └─► Retourne: [{"symbol": "SNTS", "close": 15500, "open": 15400, ...}]
   │
   ├─► SAUVEGARDE RAW: write_raw(db, "BRVM", records)
   │   └─► INSERT raw_events
   │
   ├─► NORMALISATION: normalize_brvm(records)
   │   └─► Transforme vers schéma unifié
   │   └─► {"source": "BRVM", "dataset": "QUOTES", "key": "SNTS", 
   │        "ts": "2026-01-06", "value": 15500, "attrs": {...}}
   │
   ├─► SAUVEGARDE CURATED: upsert_observations(db, obs)
   │   └─► UPSERT curated_observations (évite doublons)
   │
   └─► LOG EXECUTION: log_ingestion_run(db, ...)
       └─► INSERT ingestion_runs
       └─► {"source": "BRVM", "status": "success", "obs_count": 47, ...}

3. RÉSULTAT
   └─► MongoDB contient maintenant:
       - 47 observations dans curated_observations
       - 1 enregistrement raw dans raw_events
       - 1 log dans ingestion_runs
```

## 10. VÉRIFICATION & DEBUG

```bash
# Voir les données collectées par source
python voir_donnees.py

# Rapport complet (count par source)
python show_complete_data.py

# Historique d'ingestion (logs)
python show_ingestion_history.py

# Inspection approfondie MongoDB
python inspection_approfondie.py

# Rapport état complet
python rapport_etat_donnees.py

# Test connexion MongoDB
python verifier_connexion_db.py

# Vérifier qualité données BRVM
python verifier_cours_brvm.py
python verifier_historique_60jours.py
```

## 11. FICHIERS CLÉS

| Fichier | Rôle |
|---------|------|
| `scripts/pipeline.py` | Orchestrateur ETL principal - Point d'entrée `run_ingestion()` |
| `scripts/mongo_utils.py` | Utilitaires MongoDB (write_raw, upsert_observations, log) |
| `scripts/connectors/brvm_scraper_production.py` | Scraping BRVM temps réel |
| `scripts/connectors/worldbank.py` | Connecteur API World Bank |
| `scripts/connectors/imf.py` | Connecteur API IMF SDMX |
| `scripts/connectors/afdb.py` | Connecteur API AfDB |
| `scripts/connectors/un_sdg.py` | Connecteur API UN SDG |
| `ingestion/management/commands/ingest_source.py` | Commande Django pour ingestion manuelle |
| `airflow/dags/*.py` | DAGs pour collecte automatique programmée |

## 12. DONNÉES ACTUELLES

**MongoDB centralisation_db:**
- ✅ BRVM: 2,021 observations (47 actions × 43 jours)
- ✅ AI_ANALYSIS: 47 recommandations
- ❌ WorldBank: 0 observations (non collecté)
- ❌ IMF: 0 observations (non collecté)
- ❌ AfDB: 0 observations (non collecté)
- ❌ UN_SDG: 0 observations (non collecté)

**Pour collecter les sources manquantes:**
```bash
python collecter_toutes_sources.py
# OU
airflow db init
python start_airflow_background.bat
```

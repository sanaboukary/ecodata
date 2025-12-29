# Documentation ETL

## Architecture du système d'ingestion

Le système ETL (Extract, Transform, Load) est conçu pour centraliser les données de 5 sources différentes dans MongoDB.

## Sources de données

### 1. BRVM (Bourse Régionale des Valeurs Mobilières)
- **Type** : API REST
- **Fréquence** : Horaire (via scheduler)
- **Données** : Cotations boursières
- **Connecteur** : `scripts/connectors/brvm.py`

### 2. Banque Mondiale (World Bank)
- **Type** : API wbdata
- **Fréquence** : Manuelle ou hebdomadaire
- **Données** : Indicateurs de développement
- **Connecteur** : `scripts/connectors/worldbank.py`

### 3. FMI (International Monetary Fund)
- **Type** : API REST
- **Fréquence** : Manuelle ou mensuelle
- **Données** : Indicateurs économiques
- **Connecteur** : `scripts/connectors/imf.py`

### 4. ONU SDG (UN Sustainable Development Goals)
- **Type** : API REST
- **Fréquence** : Manuelle ou trimestrielle
- **Données** : Objectifs de développement durable
- **Connecteur** : `scripts/connectors/un_sdg.py`

### 5. BAD (Banque Africaine de Développement)
- **Type** : API REST / Scraping
- **Fréquence** : Manuelle ou mensuelle
- **Données** : Données africaines
- **Connecteur** : `scripts/connectors/afdb.py`

## Pipeline unifié

Le fichier `scripts/pipeline.py` fournit un pipeline unifié pour tous les connecteurs.

### Étapes du pipeline

1. **Extract** : Récupération des données depuis la source
2. **Transform** : Nettoyage et normalisation des données
3. **Load** : Insertion dans MongoDB

### Structure des données

Toutes les données sont normalisées selon ce schéma :

```python
{
    "source": "worldbank",  # Source de la donnée
    "indicator_code": "GDP",  # Code de l'indicateur
    "indicator_name": "Gross Domestic Product",  # Nom de l'indicateur
    "country_code": "BEN",  # Code ISO du pays
    "country_name": "Benin",  # Nom du pays
    "year": 2020,  # Année
    "value": 123456789,  # Valeur
    "unit": "USD",  # Unité
    "last_updated": "2025-11-06T10:00:00Z",  # Date de mise à jour
    "metadata": {}  # Métadonnées additionnelles
}
```

## Collections MongoDB

### `indicators`
Stocke tous les indicateurs avec leurs métadonnées.

```javascript
{
    _id: ObjectId("..."),
    code: "GDP",
    name: "Gross Domestic Product",
    source: "worldbank",
    category: "economic",
    description: "...",
    unit: "USD"
}
```

### `data_points`
Stocke les valeurs des indicateurs par pays et année.

```javascript
{
    _id: ObjectId("..."),
    indicator_code: "GDP",
    country_code: "BEN",
    year: 2020,
    value: 123456789,
    source: "worldbank",
    timestamp: ISODate("2025-11-06T10:00:00Z")
}
```

### `ingestion_logs`
Stocke les logs d'exécution des ingestions.

```javascript
{
    _id: ObjectId("..."),
    source: "worldbank",
    start_time: ISODate("2025-11-06T10:00:00Z"),
    end_time: ISODate("2025-11-06T10:05:00Z"),
    status: "success",
    records_processed: 1000,
    errors: []
}
```

## Commandes d'ingestion

### Ingestion manuelle par source

```bash
# BRVM
python manage.py ingest_source --source brvm

# World Bank
python manage.py ingest_source --source worldbank --years 2010-2020

# IMF
python manage.py ingest_source --source imf --countries BEN,TGO,CIV

# UN SDG
python manage.py ingest_source --source un --indicators 1.1.1,1.2.1

# AfDB
python manage.py ingest_source --source afdb
```

### Options disponibles

- `--source` : Source de données (obligatoire)
- `--years` : Plage d'années (format: 2010-2020)
- `--countries` : Liste de pays ISO (format: BEN,TGO,CIV)
- `--indicators` : Liste d'indicateurs (format: GDP,INFLATION)
- `--verbose` : Mode verbeux (affiche plus de détails)
- `--dry-run` : Simulation sans insertion en base

### Scheduler automatique

Le scheduler BRVM s'exécute toutes les heures :

```bash
python manage.py start_scheduler
```

Configuration dans `scripts/schedule_brvm.py` :

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BlockingScheduler()

# Toutes les heures
scheduler.add_job(
    ingest_brvm,
    trigger=CronTrigger(hour='*'),
    id='brvm_hourly',
    name='BRVM Hourly Ingestion'
)
```

## Gestion des erreurs

### Retry automatique

Les connecteurs intègrent une logique de retry :

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

### Logging

Tous les logs sont stockés dans :
- `logs/ingestion.log` : Logs détaillés des ingestions
- `logs/error.log` : Erreurs critiques uniquement

### Notifications (à venir)

Configuration pour les notifications email en cas d'échec :

```python
# Dans .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
NOTIFICATION_EMAILS=admin@example.com,devops@example.com
```

## Performance

### Optimisations

1. **Batch insertion** : Les données sont insérées par batch de 1000
2. **Index MongoDB** : Index sur `indicator_code`, `country_code`, `year`
3. **Caching** : Cache des métadonnées d'indicateurs

### Monitoring

```bash
# Statistiques d'ingestion
python manage.py ingestion_stats

# Dernière ingestion
python manage.py show_last_ingestion_run
```

## Développement

### Ajouter une nouvelle source

1. Créer un nouveau connecteur dans `scripts/connectors/new_source.py`
2. Implémenter les méthodes `extract()`, `transform()`, `load()`
3. Ajouter la source dans `ingestion/management/commands/ingest_source.py`
4. Tester avec `--dry-run`

Exemple minimal :

```python
# scripts/connectors/new_source.py
from scripts._common import get_mongo_client

def extract():
    """Récupère les données de la source"""
    # Votre code ici
    return raw_data

def transform(raw_data):
    """Transforme les données au format standard"""
    normalized = []
    for item in raw_data:
        normalized.append({
            "source": "new_source",
            "indicator_code": item['code'],
            # ...
        })
    return normalized

def load(data):
    """Charge les données dans MongoDB"""
    client = get_mongo_client()
    db = client.centralisation_db
    db.data_points.insert_many(data)

def run():
    """Point d'entrée principal"""
    raw_data = extract()
    normalized_data = transform(raw_data)
    load(normalized_data)
```

## Tests

```bash
# Tester l'ingestion en mode dry-run
python manage.py ingest_source --source worldbank --dry-run

# Tester un connecteur spécifique
python scripts/connectors/worldbank.py

# Tests unitaires
python manage.py test ingestion
```

## Troubleshooting

### Erreur de connexion MongoDB
```bash
# Vérifier que MongoDB est démarré
sudo systemctl status mongod  # Linux
# ou vérifier dans services.msc (Windows)

# Tester la connexion
mongo --eval "db.version()"
```

### Timeout API
Augmenter le timeout dans `.env` :
```
HTTP_TIMEOUT=60
```

### Données dupliquées
Les données sont dédupliquées par combinaison unique :
- `(indicator_code, country_code, year, source)`

### Performance lente
Créer des index MongoDB :
```javascript
db.data_points.createIndex({ indicator_code: 1, country_code: 1, year: 1 })
db.data_points.createIndex({ source: 1, timestamp: -1 })
```

# ✅ Intégration Scheduler Multi-Sources Complétée

## 🎉 Statut

**SUCCÈS** - Le scheduler automatique multi-sources est opérationnel !

## 📋 Ce qui a été fait

### 1. **Extraction et Configuration** ✅
- ✅ Fichier `.env` mis à jour avec configuration MongoDB correcte
- ✅ Scheduler `start_scheduler.py` intégré dans `ingestion/management/commands/`
- ✅ Configuration MongoDB : `mongodb://SANA:Boukary89@127.0.0.1:27018/centralisation_db?authSource=admin`

### 2. **Test d'Ingestion BRVM** ✅
```bash
python manage.py ingest_source --source brvm
# Résultat : 3 observations insérées ✅
```

### 3. **Vérification MongoDB** ✅
- Collection `raw_events` : 2 enregistrements
- Collection `curated_observations` : 6 observations
- Base de données : `centralisation_db` ✅

### 4. **Scheduler Démarré** ✅
```bash
python manage.py start_scheduler
# Statut : Scheduler actif avec timezone Africa/Abidjan ✅
```

## ⏰ Planning du Scheduler

Le scheduler utilise l'heure locale d'**Abidjan (Africa/Abidjan)** :

| Source | Fréquence | Horaire | Description |
|--------|-----------|---------|-------------|
| **BRVM** | Toutes les heures | `0 * * * *` | Données boursières |
| **IMF** | Le 1er du mois | `02h30` | Indicateurs FMI |
| **AfDB** | Trimestriel (jan/avr/jul/oct) | `03h00 le 1er` | Données BAD |
| **UN SDG** | Trimestriel (jan/avr/jul/oct) | `03h15 le 1er` | ODD ONU |
| **WorldBank** | Le 15 du mois | `02h00` | Indicateurs Banque Mondiale |

## 📊 Collections MongoDB

### `raw_events` (trace brute)
Enregistre les événements bruts d'ingestion :
```javascript
{
  "source": "BRVM",
  "timestamp": ISODate("2025-11-06T..."),
  "data": {...}
}
```

### `curated_observations` (format standardisé)
Données normalisées pour analyse :
```javascript
{
  "source": "BRVM",
  "dataset": "QUOTES",
  "key": "SYMBOL",
  "ts": ISODate("2025-11-06T..."),
  "value": 123.45,
  "attrs": {
    "open": 120.00,
    "high": 125.00,
    "low": 119.00,
    "volume": 1000
  }
}
```

## 🔧 Configuration Actuelle

### Variables d'Environnement (.env)
```properties
ENV=dev
TZ=Africa/Abidjan

# MongoDB
MONGODB_URI=mongodb://SANA:Boukary89@127.0.0.1:27018/centralisation_db?authSource=admin
MONGODB_NAME=centralisation_db

# World Bank
WB_INDICATOR=SP.POP.TOTL
WB_DATE=2000:2024
WB_COUNTRY=all

# IMF
IMF_DATASET=IFS
IMF_KEY=M.CIV.PCPI_IX

# UN SDG
UN_SERIES=SL_TLF_UEM
UN_AREA=
UN_TIME=

HTTP_TIMEOUT=30
```

## 📡 API Disponible

### Endpoint pour les Dashboards
```bash
GET /api/ingestion/series/?key=SYMBOL
```

**Exemple** :
```bash
curl "http://localhost:8000/api/ingestion/series/?key=BRVM.QUOTE.SYMBOL"
```

**Réponse** :
```json
{
  "key": "BRVM.QUOTE.SYMBOL",
  "observations": [
    {
      "ts": "2025-11-06T10:00:00Z",
      "value": 123.45,
      "attrs": {
        "open": 120.00,
        "high": 125.00,
        "low": 119.00,
        "volume": 1000
      }
    }
  ]
}
```

## 🚀 Commandes Utiles

### Ingestion Manuelle
```bash
# BRVM
.venv/Scripts/python.exe manage.py ingest_source --source brvm

# World Bank
.venv/Scripts/python.exe manage.py ingest_source --source worldbank

# IMF
.venv/Scripts/python.exe manage.py ingest_source --source imf

# UN SDG
.venv/Scripts/python.exe manage.py ingest_source --source un

# AfDB
.venv/Scripts/python.exe manage.py ingest_source --source afdb
```

### Gestion du Scheduler
```bash
# Démarrer
.venv/Scripts/python.exe manage.py start_scheduler

# Arrêter (Ctrl+C dans le terminal)

# Vérifier les logs (si configuré)
tail -f logs/scheduler.log
```

### Vérification MongoDB
```bash
# Se connecter
mongo "mongodb://SANA:Boukary89@127.0.0.1:27018/centralisation_db?authSource=admin"

# Dans le shell MongoDB
use centralisation_db
db.curated_observations.find().pretty()
db.raw_events.find().pretty()

# Compter les observations
db.curated_observations.countDocuments({source: "BRVM"})
```

## 🔍 Monitoring

### Vérifier le statut
```bash
# Nombre d'observations par source
.venv/Scripts/python.exe -c "
from scripts.mongo_utils import get_db
db = get_db('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin', 'centralisation_db')
pipeline = [{'$group': {'_id': '$source', 'count': {'$sum': 1}}}]
for doc in db.curated_observations.aggregate(pipeline):
    print(f\"{doc['_id']}: {doc['count']} observations\")
"
```

### Dernières observations
```bash
.venv/Scripts/python.exe -c "
from scripts.mongo_utils import get_db
db = get_db('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin', 'centralisation_db')
for obs in db.curated_observations.find().sort('ts', -1).limit(5):
    print(f\"{obs['source']}/{obs['key']}: {obs['value']} @ {obs['ts']}\")
"
```

## 📝 Personnalisation

### Modifier les Paramètres d'Ingestion

Éditez `.env` pour changer les paramètres :

```properties
# Changer l'indicateur World Bank
WB_INDICATOR=NY.GDP.MKTP.CD

# Changer la période
WB_DATE=2010:2023

# Changer les pays (codes ISO)
WB_COUNTRY=BEN,TGO,CIV

# Changer la série IMF
IMF_KEY=M.BEN.PCPI_IX
```

Puis redémarrez le scheduler.

### Ajouter une Nouvelle Source

1. Créez un connecteur dans `scripts/connectors/nouvelle_source.py`
2. Ajoutez la fonction fetch dans le connecteur
3. Intégrez dans `scripts/pipeline.py`
4. Ajoutez un job dans `start_scheduler.py`

## ⚠️ Notes Importantes

1. **Port MongoDB** : Utilisez `27018` (port mappé du conteneur)
2. **Authentification** : User `SANA` avec `authSource=admin`
3. **Timezone** : Tous les horaires sont en heure locale d'Abidjan
4. **Collections** : 
   - `raw_events` pour les traces brutes
   - `curated_observations` pour les données normalisées

## 🎯 Prochaines Étapes

1. **Dashboard** : Intégrer l'API `/api/ingestion/series/` dans vos visualisations
2. **Monitoring** : Ajouter des alertes en cas d'échec d'ingestion
3. **Logs** : Configurer le logging dans fichiers
4. **Backup** : Mettre en place des sauvegardes régulières MongoDB
5. **Tests** : Ajouter des tests pour chaque connecteur

## 🐛 Dépannage

### Le scheduler ne démarre pas
```bash
# Vérifier les imports
.venv/Scripts/python.exe -c "from scripts.pipeline import run_ingestion; print('OK')"

# Vérifier MongoDB
mongo "mongodb://SANA:Boukary89@127.0.0.1:27018/admin" --eval "db.version()"
```

### Pas de données insérées
```bash
# Tester manuellement
.venv/Scripts/python.exe manage.py ingest_source --source brvm --verbose
```

### Erreur d'authentification MongoDB
Vérifiez que :
- Le conteneur MongoDB est démarré
- Le port 27018 est bien mappé
- Les credentials sont corrects

---

**✅ Le système d'ingestion automatique multi-sources est opérationnel !**

Pour toute question, consultez la documentation dans `docs/` ou les logs.

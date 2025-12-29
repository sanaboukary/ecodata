# API Reference

## Vue d'ensemble

La plateforme expose plusieurs endpoints REST pour interagir avec les données centralisées.

## Base URL

```
http://localhost:8000
```

## Authentification

Actuellement, l'API est ouverte. En production, ajoutez l'authentification via :
- Token JWT
- OAuth2
- API Keys

## Endpoints

### Ingestion

#### Health Check

Vérifier l'état du système d'ingestion.

**Request**
```http
GET /api/ingestion/health/
```

**Response** (200 OK)
```json
{
  "status": "ok",
  "mongodb": "connected",
  "database": "centralisation_db",
  "collections": {
    "indicators": 150,
    "data_points": 25000
  },
  "last_ingestion": {
    "source": "brvm",
    "timestamp": "2025-11-06T10:00:00Z",
    "status": "success"
  }
}
```

**Error Response** (503 Service Unavailable)
```json
{
  "status": "error",
  "mongodb": "disconnected",
  "error": "Connection refused"
}
```

#### Start Ingestion

Démarrer une ingestion manuelle.

**Request**
```http
POST /api/ingestion/start/
Content-Type: application/json

{
  "scripts_dir": "./scripts",
  "pattern": "*.py",
  "source": "worldbank"
}
```

**Parameters**
- `scripts_dir` (string, optional) : Chemin vers les scripts d'ingestion
- `pattern` (string, optional) : Pattern glob pour les fichiers
- `source` (string, optional) : Source spécifique à ingérer

**Response** (200 OK)
```json
{
  "status": "started",
  "message": "Ingestion démarrée pour la source: worldbank",
  "job_id": "job_123456"
}
```

**Error Response** (400 Bad Request)
```json
{
  "status": "error",
  "message": "Source invalide"
}
```

### Dashboard

#### Liste des KPIs

Récupérer tous les KPIs disponibles.

**Request**
```http
GET /api/kpis/
```

**Response** (200 OK)
```json
{
  "count": 150,
  "kpis": [
    {
      "code": "GDP",
      "name": "Gross Domestic Product",
      "category": "economic",
      "sources": ["worldbank", "imf"],
      "countries": 54,
      "years_available": "2000-2023"
    },
    {
      "code": "INFLATION",
      "name": "Inflation Rate",
      "category": "economic",
      "sources": ["worldbank", "imf"],
      "countries": 54,
      "years_available": "2000-2023"
    }
  ]
}
```

#### Export Indicateurs CSV

Exporter tous les indicateurs en CSV.

**Request**
```http
GET /export/indicateurs.csv
```

**Response** (200 OK)
```
Content-Type: text/csv
Content-Disposition: attachment; filename="indicateurs_2025-11-06.csv"

code,name,category,source,unit
GDP,"Gross Domestic Product",economic,worldbank,USD
INFLATION,"Inflation Rate",economic,imf,%
...
```

### Explorateur

#### Recherche de données

Rechercher des données selon des critères.

**Request**
```http
GET /explorer/data/?indicator=GDP&country=BEN&start_year=2010&end_year=2020
```

**Query Parameters**
- `indicator` (string, required) : Code de l'indicateur
- `country` (string, optional) : Code ISO du pays
- `start_year` (integer, optional) : Année de début
- `end_year` (integer, optional) : Année de fin
- `source` (string, optional) : Source des données

**Response** (200 OK)
```json
{
  "indicator": {
    "code": "GDP",
    "name": "Gross Domestic Product",
    "unit": "USD"
  },
  "country": {
    "code": "BEN",
    "name": "Benin"
  },
  "data": [
    {
      "year": 2010,
      "value": 6494000000,
      "source": "worldbank"
    },
    {
      "year": 2011,
      "value": 7258000000,
      "source": "worldbank"
    }
  ],
  "count": 11
}
```

#### Export données CSV

Exporter les résultats de recherche en CSV.

**Request**
```http
GET /explorer/export/?indicator=GDP&country=BEN&start_year=2010&end_year=2020
```

**Response** (200 OK)
```
Content-Type: text/csv
Content-Disposition: attachment; filename="GDP_BEN_2010-2020.csv"

year,country,indicator,value,unit,source
2010,BEN,GDP,6494000000,USD,worldbank
2011,BEN,GDP,7258000000,USD,worldbank
...
```

#### Autocomplétion indicateurs

Rechercher des indicateurs par nom.

**Request**
```http
GET /explorer/autocomplete/indicators/?q=GDP
```

**Response** (200 OK)
```json
{
  "results": [
    {
      "code": "GDP",
      "name": "Gross Domestic Product",
      "category": "economic"
    },
    {
      "code": "GDP_GROWTH",
      "name": "GDP Growth Rate",
      "category": "economic"
    }
  ]
}
```

#### Autocomplétion pays

Rechercher des pays par nom.

**Request**
```http
GET /explorer/autocomplete/countries/?q=Benin
```

**Response** (200 OK)
```json
{
  "results": [
    {
      "code": "BEN",
      "name": "Benin",
      "region": "West Africa"
    }
  ]
}
```

#### Ajouter un favori

Sauvegarder une recherche en favori.

**Request**
```http
POST /explorer/favorite/
Content-Type: application/json

{
  "indicator": "GDP",
  "country": "BEN",
  "name": "PIB Bénin",
  "start_year": 2010,
  "end_year": 2020
}
```

**Response** (201 Created)
```json
{
  "id": "fav_123",
  "message": "Favori créé avec succès"
}
```

#### Liste des favoris

Récupérer tous les favoris de l'utilisateur.

**Request**
```http
GET /explorer/favorites/
```

**Response** (200 OK)
```json
{
  "count": 5,
  "favorites": [
    {
      "id": "fav_123",
      "name": "PIB Bénin",
      "indicator": "GDP",
      "country": "BEN",
      "start_year": 2010,
      "end_year": 2020,
      "created_at": "2025-11-06T10:00:00Z"
    }
  ]
}
```

## Codes d'erreur

| Code | Signification |
|------|---------------|
| 200 | OK - Requête réussie |
| 201 | Created - Ressource créée |
| 400 | Bad Request - Paramètres invalides |
| 404 | Not Found - Ressource introuvable |
| 405 | Method Not Allowed - Méthode HTTP non autorisée |
| 500 | Internal Server Error - Erreur serveur |
| 503 | Service Unavailable - Service indisponible |

## Limites de taux

Actuellement aucune limite. En production, implémentez :
- 100 requêtes / minute par IP
- 1000 requêtes / heure par utilisateur authentifié

Exemple avec Django REST Framework :

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/hour'
    }
}
```

## Pagination

Pour les endpoints retournant des listes, la pagination est automatique :

```http
GET /explorer/data/?indicator=GDP&page=2&page_size=50
```

**Response**
```json
{
  "count": 200,
  "next": "/explorer/data/?indicator=GDP&page=3",
  "previous": "/explorer/data/?indicator=GDP&page=1",
  "results": [...]
}
```

## Formats de réponse

Tous les endpoints supportent JSON par défaut. Pour CSV, utilisez les endpoints `/export/`.

## CORS

En production, configurez CORS :

```python
# settings.py
INSTALLED_APPS += ['corsheaders']

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "https://votre-frontend.com",
]
```

## Exemples d'utilisation

### Python

```python
import requests

# Health check
response = requests.get('http://localhost:8000/api/ingestion/health/')
print(response.json())

# Recherche de données
params = {
    'indicator': 'GDP',
    'country': 'BEN',
    'start_year': 2010,
    'end_year': 2020
}
response = requests.get('http://localhost:8000/explorer/data/', params=params)
data = response.json()
```

### JavaScript (Fetch)

```javascript
// Health check
fetch('http://localhost:8000/api/ingestion/health/')
  .then(response => response.json())
  .then(data => console.log(data));

// Recherche de données
const params = new URLSearchParams({
  indicator: 'GDP',
  country: 'BEN',
  start_year: 2010,
  end_year: 2020
});

fetch(`http://localhost:8000/explorer/data/?${params}`)
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL

```bash
# Health check
curl http://localhost:8000/api/ingestion/health/

# Démarrer une ingestion
curl -X POST http://localhost:8000/api/ingestion/start/ \
  -H "Content-Type: application/json" \
  -d '{"source": "worldbank"}'

# Recherche de données
curl "http://localhost:8000/explorer/data/?indicator=GDP&country=BEN"
```

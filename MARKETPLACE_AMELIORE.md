# 📊 Guide Marketplace Amélioré - Téléchargement Données par Année

## ✅ Améliorations Implementées

### 1. **Format CSV Optimisé pour Analyses**

Le CSV est maintenant structuré selon la source :

#### 📈 WorldBank / IMF / UN_SDG / AfDB
```csv
Date,Pays,Code_Pays,Indicateur,Code_Indicateur,Valeur,Année,Région
2023-01-01,Sénégal,SN,Croissance PIB (%),NY.GDP.MKTP.KD.ZG,4.5,2023,UEMOA
2023-01-01,Côte d'Ivoire,CI,Croissance PIB (%),NY.GDP.MKTP.KD.ZG,7.1,2023,UEMOA
```

**Colonnes claires** :
- `Date` : Date complète
- `Pays` : Nom du pays en français
- `Code_Pays` : Code ISO (SN, CI, BJ...)
- `Indicateur` : Nom de l'indicateur
- `Code_Indicateur` : Code technique
- `Valeur` : Valeur numérique
- `Année` : Année extraite
- `Région` : Région/Zone économique

#### 💹 BRVM (Actions)
```csv
Date,Symbole,Nom,Prix_Clôture,Prix_Ouverture,Prix_Haut,Prix_Bas,Volume,Variation_%,Volatilité,Market_Cap,RSI,MACD,Beta,Secteur
2026-01-12,SNTS,Sonatel,14500,14300,14600,14200,1250,1.5,12.3,850000000,62.5,125.3,0.85,Télécommunications
```

**Attributs BRVM** :
- Prix OHLC (Open, High, Low, Close)
- Volume de transactions
- Variation en %
- Indicateurs techniques (RSI, MACD, Beta)
- Market Cap, Secteur

#### 📄 Publications BRVM
```csv
Date,Type,Titre,Société,Contenu,URL
2026-01-10,Rapport annuel,Rapport 2025 - Sonatel,SNTS,Croissance du chiffre d'affaires...,https://...
```

### 2. **Nouveaux Endpoints API**

#### 📅 Récupérer années disponibles
```
GET /marketplace/get-years/?source=worldbank
```

**Réponse** :
```json
{
    "years": [2024, 2023, 2022, 2021, 2020, ...],
    "source": "WorldBank"
}
```

**Exemples** :
- WorldBank : 1960 → 2024 (65 ans)
- IMF : 2000 → 2026 (27 ans)
- UN_SDG : 1985 → 2025 (35 ans)
- AfDB : 2020 → 2024 (5 ans)
- BRVM : 2024 → 2026

#### 📊 Récupérer datasets disponibles
```
GET /marketplace/get-datasets/?source=worldbank&year=2023
```

**Réponse** :
```json
{
    "datasets": [
        {
            "code": "NY.GDP.MKTP.KD.ZG",
            "name": "Croissance PIB (%)",
            "count": 487,
            "first_date": "2023-01-01",
            "last_date": "2023-12-31",
            "sample_key": "SN",
            "sample_value": 4.5
        },
        ...
    ],
    "source": "WorldBank",
    "year": "2023",
    "total": 35
}
```

**Paramètres** :
- `source` : brvm, worldbank, imf, un_sdg, afdb, publications
- `year` : Année spécifique ou "all" (optionnel)

### 3. **Utilisation dans Interface Web**

Vous pouvez maintenant :

1. **Sélectionner la source** (WorldBank, IMF, etc.)
2. **Choisir l'année** (2020, 2021, 2022...)
3. **Télécharger CSV structuré**

Le CSV téléchargé sera :
- ✅ **Propre** : Colonnes claires, pas de colonnes vides
- ✅ **Structuré** : Même format pour toutes les lignes
- ✅ **Analysable** : Direct dans Excel, Python pandas, R
- ✅ **Compact** : Seulement les colonnes pertinentes

## 🔧 Utilisation Programmée (API)

### Python
```python
import requests
import pandas as pd

# 1. Récupérer années disponibles
r = requests.get('http://127.0.0.1:8000/marketplace/get-years/?source=worldbank')
years = r.json()['years']
print(f"Années: {years}")

# 2. Récupérer datasets pour 2023
r = requests.get('http://127.0.0.1:8000/marketplace/get-datasets/?source=worldbank&year=2023')
datasets = r.json()['datasets']

for ds in datasets:
    print(f"{ds['name']}: {ds['count']} observations")

# 3. Télécharger CSV 2023
r = requests.get('http://127.0.0.1:8000/marketplace/download/?source=worldbank&period=all&format=csv')

# 4. Charger dans pandas
df = pd.read_csv(io.StringIO(r.text))
print(df.head())
```

### R
```r
library(httr)
library(jsonlite)

# Récupérer années
response <- GET("http://127.0.0.1:8000/marketplace/get-years/?source=worldbank")
years <- fromJSON(content(response, "text"))$years

# Télécharger CSV
response <- GET("http://127.0.0.1:8000/marketplace/download/?source=worldbank&period=all&format=csv")
data <- read.csv(text = content(response, "text"))
head(data)
```

## 📥 Formats Disponibles

1. **CSV** : Pour Excel, Google Sheets, analyses statistiques
2. **JSON** : Pour applications web, APIs
3. **Excel** : Format .xlsx avec formatage

## 🎯 Cas d'Usage

### Analyse économique pays UEMOA
```
1. Source: WorldBank
2. Année: 2020-2024
3. Datasets: PIB, Inflation, Population
4. Export: CSV
5. Analyse: Tendances économiques sur 5 ans
```

### Analyse portefeuille BRVM
```
1. Source: BRVM
2. Année: 2026
3. Datasets: Tous cours
4. Export: CSV
5. Analyse: Performance, corrélations, RSI
```

### Étude impact publications
```
1. Source: BRVM_PUBLICATION
2. Année: 2025-2026
3. Datasets: Rapports, Communiqués
4. Export: JSON
5. Analyse: Sentiment, impact cours
```

## 🔍 Avantages du Nouveau Format

### Avant (Problématique)
```csv
Source,Dataset,Key,Date,Value,attr1,attr2,...,attr50
WorldBank,NY.GDP,SN,2023,4.5,,,,,Sénégal,,,,,,,,...
```
- ❌ 50+ colonnes dynamiques
- ❌ 90% cellules vides
- ❌ Difficile à importer
- ❌ Colonnes changent selon données

### Après (Optimisé)
```csv
Date,Pays,Code_Pays,Indicateur,Code_Indicateur,Valeur,Année,Région
2023-01-01,Sénégal,SN,Croissance PIB,NY.GDP.MKTP.KD.ZG,4.5,2023,UEMOA
```
- ✅ 8 colonnes fixes
- ✅ 0% cellules vides
- ✅ Import direct Excel/Python
- ✅ Colonnes constantes

## 📊 Volumes Données Disponibles

| Source | Observations | Années | Entités |
|--------|-------------|--------|----------|
| **BRVM** | 2,505 | 2024-2026 | 47 actions |
| **WorldBank** | 4,451 | 1960-2024 | 87 pays |
| **IMF** | 3,696 | 2000-2026 | 48 pays |
| **UN_SDG** | 711 | 1985-2025 | 40 pays |
| **AfDB** | 1,920 | 2020-2024 | 384 pays |
| **Publications** | 168 | 2024-2026 | 47 sociétés |

**Total : 13,565 observations**

## 🚀 Prochaines Étapes

1. **Tester téléchargement** : Aller sur http://127.0.0.1:8000/marketplace/
2. **Sélectionner source** : WorldBank, IMF, etc.
3. **Choisir période** : Toutes années ou année spécifique
4. **Télécharger CSV** : Bouton "Télécharger"
5. **Analyser** : Ouvrir dans Excel, Python pandas, R

## 💡 Support

Si problème avec téléchargement ou format CSV :
1. Vérifier serveur Django actif : `python manage.py runserver`
2. Tester endpoints : `python test_rapide_marketplace.py`
3. Consulter logs serveur pour erreurs

---

**Version** : 2.0
**Date** : 12 janvier 2026
**Fichiers modifiés** :
- `dashboard/data_marketplace.py` : export_csv(), get_available_years(), get_available_datasets()
- `dashboard/urls.py` : Routes /get-years/, /get-datasets/
- `dashboard/views.py` : Imports fonctions

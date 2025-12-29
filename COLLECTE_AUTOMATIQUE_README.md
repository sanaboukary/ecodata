# 🎯 COLLECTE INTELLIGENTE AUTOMATISÉE BRVM

## Objectif
Système de collecte automatisée des cours BRVM pour recommandations trading.

**Politique**: 🔴 ZÉRO TOLÉRANCE pour données simulées - Scraping site officiel BRVM uniquement

---

## 📋 Modes de Collecte

### 1️⃣ Collecte Unique (Immédiate)

Collecte les cours BRVM **maintenant** (une seule fois).

**Windows:**
```bash
collecter_maintenant.bat
```

**Python direct:**
```bash
python collecte_intelligente_auto.py --mode unique
```

**Quand l'utiliser:**
- Collecte manuelle ponctuelle
- Test du système
- Mise à jour immédiate des données

---

### 2️⃣ Collecte Horaire (Automatique)

Collecte automatique **toutes les heures** pendant les heures de marché BRVM:
- 📅 Lundi à Vendredi
- ⏰ 9h00 à 16h00

**Windows:**
```bash
activer_collecte_horaire.bat
```

**Python direct:**
```bash
python collecte_intelligente_auto.py --mode horaire
```

**Quand l'utiliser:**
- Production (laisser tourner en permanence)
- Serveur dédié
- Collecte continue pendant la semaine

---

## ⚙️ Fonctionnement Intelligent

Le système effectue automatiquement:

### 1. Scraping Selenium
- ✅ Connexion au site officiel BRVM
- ✅ Extraction des cours en temps réel
- ✅ Gestion des erreurs de connexion
- ✅ Sauvegarde HTML pour audit

### 2. Vérification Qualité
- ✅ Minimum 10 actions collectées
- ✅ Prix strictement positifs
- ✅ Variations réalistes (-20% à +20%)
- ✅ Symboles valides (format .BC)

### 3. Sauvegarde MongoDB
- ✅ Upsert automatique (insertion ou mise à jour)
- ✅ Marquage `REAL_SCRAPER` (données réelles)
- ✅ Horodatage précis
- ✅ Métadonnées complètes

### 4. Rapport Automatique
- ✅ JSON généré à chaque collecte
- ✅ Top 5 variations du jour
- ✅ Statistiques de collecte
- ✅ Traçabilité complète

---

## 📊 Fichiers Générés

| Fichier | Description |
|---------|-------------|
| `rapport_collecte_YYYYMMDD_HHMM.json` | Rapport JSON avec Top 5 et stats |
| `brvm_auto_YYYYMMDD_HHMM.html` | HTML du site BRVM (audit) |

---

## 🔧 Prérequis

### Logiciels
- ✅ Python 3.13+
- ✅ MongoDB (port 27017)
- ✅ Chrome/Chromium installé

### Packages Python
```bash
pip install selenium webdriver-manager django pymongo
```

### Configuration
Base de données: `centralisation_db`  
Collection: `curated_observations`

---

## 📈 Workflow Complet

### 1. Collecte Quotidienne Automatique

**Matin (9h00):**
```bash
# Option A: Laisser tourner en permanence (recommandé)
activer_collecte_horaire.bat

# Option B: Collecte manuelle
collecter_maintenant.bat
```

**Le système:**
1. Scrape le site BRVM toutes les heures (9h, 10h, 11h... 16h)
2. Vérifie la qualité des données
3. Sauvegarde dans MongoDB
4. Génère un rapport JSON

### 2. Génération Recommandations

**Après-midi (17h00):**
```bash
python generer_top5_nlp.py
```

**Résultat:**
- Top 5 recommandations basées sur données réelles du jour
- Scores 0-100 (Momentum + Volatilité + Catalyseurs + Sentiment)
- Fichier JSON `top5_nlp_YYYYMMDD_HHMM.json`

### 3. Backtesting (Hebdomadaire)

**Vendredi soir:**
```bash
python backtest_recommandations.py
```

**Vérification:**
- Précision des recommandations ≥ 85%
- Rendement moyen ≥ 50%
- Validation stratégie

---

## 🛡️ Politique Qualité

### ZÉRO TOLÉRANCE pour:
- ❌ Données simulées/fictives
- ❌ Estimations automatiques
- ❌ Valeurs par défaut inventées

### UNIQUEMENT:
- ✅ Scraping site officiel BRVM
- ✅ Saisie manuelle vérifiée
- ✅ Import CSV officiel BRVM

### Marquage:
- `REAL_SCRAPER`: Scraping automatique Selenium
- `REAL_MANUAL`: Saisie manuelle vérifiée
- `REAL_CSV`: Import CSV officiel

---

## 📞 Monitoring

### Vérifier la collecte:
```bash
python verif_mongodb_direct.py
```

### Consulter les rapports:
```bash
ls -lh rapport_collecte_*.json
cat rapport_collecte_20251223_1030.json
```

### Vérifier MongoDB:
```python
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': '2025-12-23'
})
print(f"{count} observations du 23/12/2025")
```

---

## 🔄 Automatisation Avancée

### Windows Task Scheduler

Créer une tâche planifiée:
1. Ouvrir Task Scheduler
2. Créer une tâche de base
3. Déclencheur: Quotidien à 8h55
4. Action: `activer_collecte_horaire.bat`
5. Conditions: Uniquement si connecté

### Airflow (Production)

Voir: `AIRFLOW_SETUP.md` pour configuration complète.

DAG existant: `brvm_collecte_quotidienne_reelle.py`

---

## ⚠️ Dépannage

### Erreur: "MongoDB connection failed"
```bash
# Vérifier MongoDB
tasklist | findstr -i mongo

# Démarrer MongoDB
net start MongoDB
```

### Erreur: "Chrome driver not found"
```bash
# Réinstaller ChromeDriver
pip install --upgrade webdriver-manager
```

### Erreur: "No data collected"
- Vérifier connexion Internet
- Consulter `brvm_auto_*.html` pour structure site
- Vérifier que site BRVM est accessible

---

## 📚 Documentation Complète

- `README.md` - Vue d'ensemble projet
- `PROJECT_STRUCTURE.md` - Architecture détaillée
- `AIRFLOW_SETUP.md` - Configuration Airflow
- `BRVM_COLLECTE_HORAIRE.md` - Détails collecte horaire

---

**Dernière mise à jour**: 23 décembre 2025  
**Auteur**: Système de Recommandations Trading BRVM  
**Licence**: Privé - Usage interne uniquement

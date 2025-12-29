# 📥 Guide Complet : Import de Données CSV vers MongoDB

## ✅ Ce qui vient d'être créé

### 🔧 Script Principal
**`collecter_csv_automatique.py`** - Collecteur intelligent de fichiers CSV

**Fonctionnalités :**
- ✅ Scan récursif de tous les CSV dans un dossier
- ✅ Détection automatique du type de données (BRVM, World Bank, IMF, etc.)
- ✅ Import structuré dans MongoDB avec upsert
- ✅ Mode dry-run pour tester avant import réel
- ✅ Support multi-formats (colonnes flexibles)
- ✅ Traçabilité complète (import_source, import_timestamp)

---

## 🚀 Utilisation

### 1️⃣ Import Simple (Dossier Courant)
```bash
# Simulation (test)
python collecter_csv_automatique.py --dry-run

# Import réel
python collecter_csv_automatique.py
```

### 2️⃣ Import depuis un Dossier Spécifique
```bash
# Scanner un dossier précis
python collecter_csv_automatique.py --dossier "./data_historiques"

# Scanner récursivement
python collecter_csv_automatique.py --dossier "./archives" --pattern "**/*.csv"
```

### 3️⃣ Filtrage Avancé
```bash
# Seulement les CSV BRVM
python collecter_csv_automatique.py --pattern "**/brvm*.csv"

# Exclure les bulletins PDF (pas encore parsés)
python collecter_csv_automatique.py --exclude-bulletins
```

---

## 📊 Formats CSV Supportés

### Format BRVM (Cours d'Actions)
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-12-07,SNTS,15500,8500,2.3
2025-12-07,BICC,7200,1250,1.2
```

**Colonnes reconnues :**
- `DATE`, `date`, `Date`
- `SYMBOL`, `symbol`, `Symbole`
- `CLOSE`, `close`, `Cours`
- `VOLUME`, `volume`, `Volume`
- `VARIATION`, `variation`, `Var`

**Résultat MongoDB :**
```json
{
  "source": "BRVM",
  "dataset": "STOCK_PRICE",
  "key": "SNTS",
  "ts": "2025-12-07",
  "value": 15500.0,
  "attrs": {
    "close": 15500.0,
    "volume": 8500,
    "variation_pct": 2.3,
    "data_quality": "REAL_MANUAL",
    "import_source": "CSV_AUTO",
    "import_file": "template_import_brvm.csv",
    "import_timestamp": "2025-12-08T11:34:46.602948"
  }
}
```

### Format World Bank (Indicateurs)
```csv
country,indicator,year,value
CI,SP.POP.TOTL,2024,28000000
SN,GDP.PCAP.CD,2024,1500
```

**Résultat MongoDB :**
```json
{
  "source": "WorldBank",
  "dataset": "INDICATOR",
  "key": "CI_SP.POP.TOTL",
  "ts": "2024-12-31",
  "value": 28000000.0,
  "attrs": {
    "country_code": "CI",
    "indicator_code": "SP.POP.TOTL",
    "year": 2024,
    "data_quality": "REAL_MANUAL",
    "import_source": "CSV_AUTO"
  }
}
```

### Format Générique (Auto-détection)
```csv
date,symbol,price,notes
2025-12-08,ASSET1,1250.5,Test data
2025-12-08,ASSET2,3400.2,Another test
```

**Le script détecte automatiquement :**
- Colonne de date : `date`, `year`, `ts`, `timestamp`
- Colonne de clé : `key`, `symbol`, `code`, `id`, `name`
- Colonne de valeur : `value`, `close`, `price`, `amount`

---

## 🔍 Détection Automatique

Le script détecte le type de CSV par :

1. **Nom du fichier** :
   - `brvm_*`, `bulletin_*`, `cotation_*` → BRVM
   - `worldbank_*`, `wb_*` → World Bank
   - `imf_*`, `fmi_*` → IMF
   - `afdb_*`, `bad_*` → AfDB
   - `un_sdg_*`, `odd_*` → UN SDG

2. **Contenu des colonnes** :
   - Présence de `symbol` + `close` → BRVM
   - Présence de `indicator` + `country` → World Bank
   - Autres → Générique

---

## 📈 Workflow Complet

### Scénario 1 : Import Historique BRVM (60 jours)

```bash
# 1. Créer un CSV avec vos données
nano historique_brvm_octobre.csv

# Contenu :
# DATE,SYMBOL,CLOSE,VOLUME,VARIATION
# 2025-10-10,SNTS,15400,8200,1.8
# 2025-10-10,BICC,7100,1200,0.9
# ... (ajouter toutes les dates/actions)

# 2. Importer
python collecter_csv_automatique.py

# 3. Vérifier
python verifier_historique_60jours.py
```

### Scénario 2 : Import Multiple (Plusieurs Sources)

```bash
# Structure de dossiers :
# data_import/
#   ├── brvm_2025_10.csv
#   ├── brvm_2025_11.csv
#   ├── brvm_2025_12.csv
#   ├── worldbank_population.csv
#   └── imf_inflation.csv

# Import global
python collecter_csv_automatique.py --dossier ./data_import

# Résultat : Tous les CSV importés avec détection automatique du type
```

### Scénario 3 : Mise à Jour Quotidienne

```bash
# Créer un CSV avec les nouvelles données du jour
echo "DATE,SYMBOL,CLOSE,VOLUME,VARIATION" > update_$(date +%Y-%m-%d).csv
echo "2025-12-08,SNTS,15600,9000,0.6" >> update_$(date +%Y-%m-%d).csv
# ... ajouter autres actions

# Import (upsert automatique = pas de doublons)
python collecter_csv_automatique.py --pattern "update_*.csv"
```

---

## 🧪 Mode Dry-Run (Recommandé)

**Toujours tester avant import réel :**

```bash
# Test sans modification de la base
python collecter_csv_automatique.py --dry-run --dossier ./nouveau_dossier

# Vérifier la sortie :
# ✅ Fichiers détectés
# ✅ Types identifiés
# ✅ Nombre d'observations parsées
# ✅ Pas d'erreurs

# Si OK → Import réel
python collecter_csv_automatique.py --dossier ./nouveau_dossier
```

---

## ✅ Vérifications Post-Import

```bash
# 1. Données BRVM
python verifier_cours_brvm.py
# Attendu : 100% données réelles

# 2. Historique 60 jours
python verifier_historique_60jours.py
# Attendu : ~2820 observations, 42 jours, 47 actions

# 3. Toutes sources
python show_complete_data.py
# Vue d'ensemble de la base

# 4. Historique collecte
python show_ingestion_history.py
# Logs des imports
```

---

## 🔧 Nettoyage & Maintenance

### Supprimer Données Simulées
```bash
python nettoyer_brvm_complet.py
# Garde uniquement data_quality: REAL_MANUAL ou REAL_SCRAPER
```

### Supprimer Doublons
```bash
# Le script fait automatiquement des upserts
# → Pas de doublons possibles (clé unique : source+dataset+key+ts)
```

### Re-import après Erreur
```bash
# L'upsert permet de relancer sans risque
python collecter_csv_automatique.py
# Les données déjà présentes seront mises à jour, pas dupliquées
```

---

## 📋 Checklist Avant Import Massif

- [ ] Vérifier encodage CSV (UTF-8 recommandé)
- [ ] Tester avec `--dry-run` d'abord
- [ ] Backup MongoDB si données critiques existantes
- [ ] Vérifier espace disque (MongoDB)
- [ ] Tester avec 1 petit CSV avant import massif
- [ ] Vérifier les colonnes (noms + types de données)
- [ ] Confirmer que les dates sont au format YYYY-MM-DD

---

## 🎯 Objectif Final : 60 Jours BRVM

**Pour constituer l'historique complet :**

### Option A : CSV Manuel (Plus précis)
```bash
# 1. Créer CSV avec 60 jours
nano historique_brvm_60jours.csv

# Format :
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-10-10,SNTS,15400,8200,1.8
2025-10-10,BICC,7100,1200,0.9
# ... ~2820 lignes (42 jours × 47 actions × 1.4 moyennes)

# 2. Importer
python collecter_csv_automatique.py

# 3. Vérifier
python verifier_historique_60jours.py
```

### Option B : Parser Bulletins PDF (Plus rapide)
```bash
# 1. Télécharger 60 bulletins PDF BRVM
mkdir bulletins_brvm
# Télécharger depuis https://www.brvm.org/fr/actualites-publications

# 2. Parser automatiquement
python parser_bulletins_brvm_pdf.py

# 3. Import du CSV généré
python collecter_csv_automatique.py --pattern "historique_brvm_60jours.csv"

# 4. Vérifier
python verifier_historique_60jours.py
```

---

## 💡 Conseils Pro

1. **Nommer intelligemment vos CSV** :
   - `brvm_2025_12_08.csv` → Détecté automatiquement comme BRVM
   - `worldbank_population_ci.csv` → Détecté comme World Bank

2. **Utiliser des sous-dossiers** :
   ```
   data_import/
   ├── brvm/
   │   ├── octobre_2025.csv
   │   ├── novembre_2025.csv
   │   └── decembre_2025.csv
   ├── macro/
   │   ├── worldbank.csv
   │   └── imf.csv
   ```

3. **Automatiser avec un script** :
   ```bash
   # create_daily_import.sh
   #!/bin/bash
   DATE=$(date +%Y-%m-%d)
   python collecter_csv_automatique.py --pattern "update_$DATE*.csv"
   python verifier_cours_brvm.py
   ```

---

## 🆘 Dépannage

### Erreur : "Aucun fichier CSV trouvé"
```bash
# Vérifier le pattern
python collecter_csv_automatique.py --pattern "*.csv"  # Non récursif
python collecter_csv_automatique.py --pattern "**/*.csv"  # Récursif
```

### Erreur : "Type non supporté"
```bash
# Le CSV sera importé en mode GENERIC
# Ou renommer le fichier : brvm_data.csv, worldbank_data.csv
```

### Erreur : "0 observations parsées"
```bash
# Vérifier :
# 1. Encodage du CSV (UTF-8)
# 2. Séparateur (virgule attendue)
# 3. Présence du header
# 4. Colonnes valides (voir formats ci-dessus)
```

---

## 📚 Résumé des Commandes

```bash
# Test rapide
python collecter_csv_automatique.py --dry-run

# Import réel
python collecter_csv_automatique.py

# Import dossier spécifique
python collecter_csv_automatique.py --dossier ./data

# Vérifications
python verifier_cours_brvm.py
python verifier_historique_60jours.py
python show_complete_data.py

# Nettoyage
python nettoyer_brvm_complet.py
```

---

**🎉 Vous êtes maintenant prêt à importer massivement des données CSV vers votre base MongoDB !**

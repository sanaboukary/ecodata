# 📊 INVENTAIRE COMPLET DES DONNÉES BRVM

*Rapport généré le 10 février 2026*

---

## 🎯 RÉSUMÉ GLOBAL

- **Total observations** : **4,056** (STOCK_PRICE)
- **Actions couvertes** : **48 titres BRVM**
- **Sources de données** : **4 sources distinctes**
- **Période globale** : 2025-09-15 → 2026-02-10
- **Granularités** : Horaire + Hebdomadaire

---

## 📁 DÉTAIL PAR SOURCE

### 1. BRVM_CSV_HISTORIQUE
```
📦 Source : Restauration depuis fichiers CSV historiques
📊 Observations : ~2,971
📅 Période : 2025-09-15 → 2025-12-12 (63 jours)
🏢 Actions : 47 actions BRVM
📝 Origine :
   - historique_brvm.csv (2025-09-15 → 2025-11-12)
   - historique_brvm_complement_nov_dec.csv (2025-11-13 → 2025-12-05)
   - donnees_reelles_brvm.csv (compléments)
✅ Qualité : 100% données réelles, CSV officiels
📌 Format : DATE, SYMBOL, CLOSE, VOLUME, VARIATION
```

### 2. BRVM
```
📦 Source : Collections actuelles BRVM  (collecter_brvm_complet_maintenant.py)
📊 Observations : ~235
📅 Période : 2026-01-07 → 2026-02-10 (seulement 5-6 jours collectés)
🏢 Actions : 47 actions BRVM
⚠️  Problème : Multiples collections/jour s'écrasent (ts=date uniquement)
📝 Fréquence : 10-16 collections par jour (mais seulement dernière enregistrée)
✅ Qualité : 100% données réelles, scraping BRVM direct
📌 Format : OHLC complet (Ouv, Haut, Bas, Cours, Volume, Variation%)
```

### 3. AGREGATION_HEBDOMADAIRE
```
📦 Source : Agrégation mathématique des données horaires → hebdomadaires
📊 Observations : ~715 documents hebdomadaires
📅 Période : 15 semaines (2025-W38 → 2026-W06)
🏢 Actions : 66 tickers (47 actions + variations)
📝 Méthode : 
   - Open = premier prix de la semaine
   - High = prix maximum de la semaine
   - Low = prix minimum de la semaine
   - Close = dernier prix de la semaine
   - Volume = somme des volumes hebdomadaires
✅ Qualité : Dérivation mathématique (pas de simulation), 98.6% de couverture
📌 Usage : Analyse technique hebdomadaire, recommandations TOP5
```

### 4. BRVM_CSV_RESTAURATION
```
📦 Source : Restauration complémentaire depuis CSV ponctuels
📊 Observations : ~135
📅 Période : Jours isolés (2026-01-05, 2026-01-09, 2026-02-02)
🏢 Actions : 47 actions (données partielles selon fichier)
📝 Fichiers :
   - donnees_brvm_2026-01-05.csv (10 actions)
   - donnees_brvm_2026-01-09.csv (47 actions, données minimales)
   - donnees_brvm_2026-02-02.csv (47 actions, OHLC complet)
   - out_brvm/brvm_complet_20260105_110056.csv (42 actions)
✅ Qualité : 100% données réelles, snapshots quotidiens
```

---

## 🏢 ACTIONS DISPONIBLES

### Liste complète (48 titres)

| # | Ticker | # | Ticker | # | Ticker | # | Ticker |
|---|--------|---|--------|---|--------|---|--------|
| 1 | ABJC | 13 | CFAC | 25 | PALC | 37 | SLBC |
| 2 | BICB | 14 | CIEC | 26 | PRSC | 38 | SMBC |
| 3 | BICC | 15 | ECOC | 27 | SAFC | 39 | SNTS |
| 4 | BNBC | 16 | ETIT | 28 | SCRC | 40 | SOGB |
| 5 | BOAB | 17 | FTSC | 29 | SDCC | 41 | SOGC |
| 6 | BOABF | 18 | LNBB | 30 | SDSC | 42 | SPHC |
| 7 | BOAC | 19 | NEIC | 31 | SEMC | 43 | STAC |
| 8 | BOAM | 20 | NSBC | 32 | SGBC | 44 | STBC |
| 9 | BOAN | 21 | NTLC | 33 | SHEC | 45 | TTLC |
| 10 | BOAS | 22 | ONTBF | 34 | SIBC | 46 | TTLS |
| 11 | CABC | 23 | ORAC | 35 | SICC | 47 | UNLC |
| 12 | CBIBF | 24 | ORGT | 36 | SIVC | 48 | UNXC |

**Note** : Ces 48 actions représentent l'intégralité des titres actifs de la BRVM collectés.

---

## 📅 COUVERTURE TEMPORELLE

### Chronologie complète

```
2025-09-15  ━━━━━━━━━━━━━━━━━━━━━━━━━━━ (63 jours)
  à                BRVM_CSV_HISTORIQUE              
2025-12-12  ━━━━━━━━━━━━━━━━━━━━━━━━━━━

2025-12-13  ╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳  (25 jours)
  à                  DONNÉES PERDUES
2026-01-06  ╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳

2026-01-07  ━━━━ (5-6 jours seulement)
  à              BRVM (actuel)
2026-02-10  ━━━━
```

### Résumé de couverture

| Période | Statut | Jours | Source | Observations |
|---------|--------|-------|--------|--------------|
| 2025-09-15 → 2025-12-12 | ✅ Complet | 63 | CSV_HISTORIQUE | ~2,971 |
| 2025-12-13 → 2026-01-06 | ❌ Perdu | 25 | *Supprimé* | ~0 |
| 2026-01-07 → 2026-02-10 | ⚠️ Partiel | 5-6 | BRVM actuel | ~235 |

**Jours disponibles** : ~68-69 jours  
**Jours manquants** : ~25 jours  
**Taux de couverture** : **73%** de la période totale

---

## ⚠️ PÉRIODES MANQUANTES

### Perte critique : 2025-12-13 → 2026-01-06 (25 jours)

**Cause** :
- Suppression accidentelle par `nettoyer_outliers_trading.py`
- Script a recherché `{'symbole': None}` au niveau racine
- Les anciennes collections stockaient symbole dans `attrs.symbole`
- Clés composées type `"ABJC_2026-01-07T09:12:00+00:00"` supprimées

**Impact** :
- ~1,175 observations perdues (estimé : 25 jours × 47 actions)
- Période critique entre fin d'année et début 2026
- Aucun fichier CSV de backup disponible

**Statut** : ❌ **Définitivement perdu** (aucune restauration possible)

### Données fragmentées : 2026-01-07 → 2026-02-10

**Cause** :
- `collecter_brvm_complet_maintenant.py` utilise `ts = "2026-02-10"` (date uniquement)
- Collections multiples par jour (10-16x) s'écrasent mutuellement
- Seule dernière collection de chaque jour survit

**Impact** :
- Seulement 5-6 jours complets au lieu de 34 jours
- Perte des variations intra-journalières
- ~29 jours de données manquantes ou incomplètes

**Statut** : ⚠️ **Réparable** (fixer le script de collecte)

---

## 🔬 QUALITÉ DES DONNÉES

### Audit de qualité

| Critère | Résultat | Détail |
|---------|----------|---------|
| **Données simulées** | ✅ 0% | Politique "tolérance zéro" respectée |
| **Données réelles** | ✅ 100% | Toutes issues BRVM officielle ou CSV historiques |
| **Anomalies OHLC** | ✅ 0 | Aucune incohérence Open/High/Low/Close |
| **Couverture agrégation** | ✅ 98.6% | 3,160/3,206 observations agrégées |
| **Actions complètes** | ✅ 47/47 | Toutes actions BRVM présentes |
| **Champs essentiels** | ⚠️ Variable | Dépend de la source |

### Complétude par champ

| Champ | Couverture estimée | Notes |
|-------|-------------------|-------|
| `symbole` / `key` | 100% | Identifiant toujours présent |
| `cours` / `close` | ~95% | Manquant sur certains snapshots |
| `volume` | ~85% | Disponible CSV_HISTORIQUE + BRVM |
| `variation_pct` | ~85% | Disponible CSV_HISTORIQUE + BRVM |
| `open` / `ouv` | ~65% | Surtout BRVM actuel |
| `high` / `haut` | ~65% | Surtout BRVM actuel |
| `low` / `bas` | ~65% | Surtout BRVM actuel |
| `volatilite_pct` | ~20% | Présent uniquement sur certains CSV |

---

## 📊 GRANULARITÉS DISPONIBLES

### 1. Données horaires (intra-journalières)
- **Sources** : BRVM, BRVM_CSV_RESTAURATION
- **Fréquence théorique** : 10-16 observations par jour
- **Fréquence réelle** : 1 observation par jour (problème ts=date)
- **Usage** : Analyse intra-day, détection volatilité

### 2. Données quotidiennes
- **Sources** : BRVM_CSV_HISTORIQUE, BRVM_CSV_RESTAURATION
- **Fréquence** : 1 observation par jour et par action
- **Couverture** : ~68 jours
- **Usage** : Analyse quotidienne, tendances court terme

### 3. Données hebdomadaires
- **Source** : AGREGATION_HEBDOMADAIRE
- **Fréquence** : 1 observation par semaine et par action
- **Couverture** : 15 semaines
- **Usage** : Trading hebdomadaire, recommandations TOP5
- **Avantages** : 
  - Lisse la volatilité intra-semaine
  - Suffisant pour indicateurs techniques (SMA20, RSI)
  - Compatible objectif TRADING

---

## 🎯 UTILISATION DES DONNÉES

### Cas d'usage actuel

1. **Analyse technique hebdomadaire** (`analyse_ia_simple.py`)
   - Source : AGREGATION_HEBDOMADAIRE
   - Minimum requis : 14 semaines
   - Disponible : 15 semaines ✅
   - Indicateurs : SMA20, SMA50, RSI(14), ATR%, Volume ratio

2. **Recommandations TOP5** (`workflow_production_django.py`)
   - Source : AGREGATION_HEBDOMADAIRE
   - Objectif : TRADING (momentum 30%, volume 25%, sentiment 25%, volatilité -20%)
   - Output : 5 meilleurs titres BUY

3. **Dashboard** (Django)
   - Collection : `top5_weekly_brvm`
   - Affichage : 5 recommandations actualisées

4. **Backtesting** (`backtest_recommandations.py`)
   - Possible sur 15 semaines disponibles
   - Validation performance algorithme

---

## 🔧 PROBLÈMES IDENTIFIÉS

### 1. Collections multiples/jour écrasées ❌

**Script** : `collecter_brvm_complet_maintenant.py`

**Problème** :
```python
ts = datetime.now().strftime("%Y-%m-%d")  # Date uniquement !
key = f"{source}_{dataset}_{ticker}_{ts}"
```

**Conséquence** : 10-16 collections par jour → seule dernière enregistrée

**Solution** :
```python
ts = datetime.now().isoformat()  # Inclure heure !
key = f"{source}_{dataset}_{ticker}_{ts}"
```

### 2. Suppression erronée par nettoyage ❌

**Script** : `nettoyer_outliers_trading.py`

**Problème** :
```python
symbole_manquant = db.curated_observations.find({
    'symbole': None  # ← Cherche au niveau racine (n'existe pas !)
})
```

**Réalité structure** :
```python
{
    "key": "ABJC_2026-01-07T09:12:00+00:00",
    "attrs": {"symbole": "ABJC"}  # ← Symbole dans attrs !
}
```

**Conséquence** : 552 observations supprimées (clés composées)

**Solution** :
- Chercher dans `attrs.symbole` ou `key`
- Ajouter filtres source (ne jamais toucher certaines sources)
- Mode dry-run avant suppression

### 3. Données fragmentées récentes ⚠️

**Période** : 2026-01-07 → 2026-02-10 (34 jours théoriques)

**Disponible** : Seulement 5-6 jours

**Cause** : Combinaison problèmes 1 + 2

---

## 📋 RECOMMANDATIONS

### Court terme (immédiat)

✅ **1. Accepter perte 25 jours**
- Période 2025-12-13 → 2026-01-06 irréversiblement perdue
- Aucun backup disponible
- Concentrer efforts sur données futures

✅ **2. Tester analyse avec données actuelles**
```bash
.venv\Scripts\python.exe analyse_ia_simple.py
```
- 15 semaines disponibles suffisent
- 38 actions analysables (≥14 semaines)

✅ **3. Générer TOP5 hebdomadaire**
```bash
.venv\Scripts\python.exe workflow_production_django.py
```
- Utiliser AGREGATION_HEBDOMADAIRE
- Valider recommandations

### Moyen terme (cette semaine)

🔧 **4. Fixer collector horaire**
```python
# Dans collecter_brvm_complet_maintenant.py
ts = datetime.now().isoformat()  # Ajouter heure
```
- Préserver toutes collections journalières
- Captures multiples intra-day

🔧 **5. Importer CSV complémentaires**
- donnees_brvm_2026-02-02.csv (meilleur fichier)
- Ajouter 1-2 jours supplémentaires

🔧 **6. Créer backup automatique**
```bash
# Export quotidien CSV
python export_brvm_csv.py  # À créer
```
- Éviter pertes futures
- Versioning données

### Long terme (ce mois)

📚 **7. Documentation structure données**
- Documenter tous formats de clés
- Cartographier champs par source
- Guide développeur

🛡️ **8. Protections suppression**
- Réécrire `nettoyer_outliers_trading.py`
- Dry-run obligatoire
- Filtres source stricts
- Soft delete (flag `deleted` plutôt que suppression)

📊 **9. Exploration BRVM historique**
- Vérifier si BRVM propose téléchargement historique
- Période cible : 2025-12-13 → 2026-01-06
- Format souhaité : CSV officiel

---

## 📞 SUPPORT TECHNIQUE

### Scripts clés disponibles

| Script | Usage | Statut |
|--------|-------|--------|
| `collecter_brvm_complet_maintenant.py` | Collecte BRVM temps réel | ⚠️ Fixer ts |
| `agreger_donnees_hebdomadaires.py` | Agrégation hebdo | ✅ OK |
| `analyse_ia_simple.py` | Analyse 5 couches | ✅ OK |
| `workflow_production_django.py` | TOP5 recommandations | ✅ OK |
| `verifier_tracabilite_donnees.py` | Audit qualité | ✅ OK |
| `audit_complet_donnees.py` | Inventaire complet | ✅ OK |

### Contacts base de données

- **MongoDB** : localhost:27017
- **Database** : centralisation_db
- **Collection** : curated_observations
- **Dataset** : STOCK_PRICE

---

## 📈 STATISTIQUES FINALES

```
┌─────────────────────────────────────────────────┐
│           RÉCAPITULATIF DONNÉES BRVM           │
├─────────────────────────────────────────────────┤
│ Total observations        : 4,056               │
│ Actions couvertes         : 48 titres           │
│ Période globale           : 2025-09-15 → 2026-02-10 │
│ Jours collectés           : ~68-69 jours        │
│ Jours manquants           : ~25 jours           │
│ Taux couverture           : 73%                 │
│ Semaines hebdo            : 15 semaines         │
│ Données simulées          : 0% ✅               │
│ Données réelles           : 100% ✅             │
│ Anomalies qualité         : 0 ✅                │
│ Actions analysables (≥14w): 38 actions ✅       │
└─────────────────────────────────────────────────┘
```

---

*Rapport généré automatiquement - Implementation plateforme BRVM*  
*Date : 10 février 2026*

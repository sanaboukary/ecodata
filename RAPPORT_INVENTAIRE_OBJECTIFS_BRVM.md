# 📊 INVENTAIRE BRVM & ANALYSE DES OBJECTIFS

**Date**: 11 février 2026  
**Base de données**: centralisation_db (MongoDB)

---

## 🏗️ ARCHITECTURE DES DONNÉES (3 NIVEAUX)

### 🔴 RAW - prices_intraday_raw
- **564 observations** (collecte en temps réel)
- Période: 2 jours récents (2026-02-10 → 2026-02-11)
- 47 actions cotées
- **Rôle**: Données brutes immuables, append-only

### 🟢 DAILY - prices_daily (SOURCE DE VÉRITÉ)
- **1,342 observations** (OHLC quotidien)
- Période: **29 jours** (2025-09-15 → 2026-02-11)
- **60 symboles** boursiers
- **93% OHLC complet** (1,248/1,342)
- Actions avec historique complet: ETIT, NTLC, BICC, FTSC, BOAS (29j chacune)

### 🔵 WEEKLY - prices_weekly (INDICATEURS TECHNIQUES)
- **235 observations** (agrégation hebdomadaire)
- **5 semaines** disponibles: 2025-W38, W39, W40, W41, 2026-W02
- 56 symboles avec données hebdo
- **38 observations avec indicateurs calculés** (16.2%)
- Indicateurs: RSI, ATR%, SMA5/10, Trend, Volume ratio

---

## 🎯 OBJECTIF 1: TOP5 HEBDOMADAIRE

### 🎯 Cible
**Être dans le TOP5 officiel BRVM ≥60% du temps**

### 📐 Formule de Scoring
```
Score = 30% Expected_Return 
      + 25% Volume 
      + 20% Semantic 
      + 15% WOS 
      + 10% Risk/Reward
```

### 📊 État Actuel
- **5 semaines** de TOP5 générés
- Actions récurrentes: SLBC, BICC, SGBC, STBC, SNTS (1 fois chacune)
- ⚠️ **Performances limitées** (pas de récurrence forte)

### ⚙️ Capacité Technique

#### 🟡 MODE DÉMARRAGE ACTIVÉ (5/14 semaines)
```python
RSI_PERIOD = 5      # Au lieu de 14
ATR_PERIOD = 5      # Au lieu de 8
SMA_FAST = 3        # Au lieu de 5
SMA_SLOW = 5        # Au lieu de 10
MIN_WEEKS = 5       # Au lieu de 14
```

#### 📈 Prêt à: **36%** (5/14 semaines)
- ✅ Prix hebdomadaires: **235 observations**
- ✅ Indicateurs techniques: **38 calculés**
- ✅ Données sémantiques: **246 publications** BRVM
- ⚠️ **Manque 9 semaines** pour mode PRODUCTION complet

### 🚧 Problèmes Identifiés
1. **Historique insuffisant**: Besoin de 14 semaines pour calibration complète
2. **Indicateurs partiels**: Seulement 16.2% des observations ont indicateurs
3. **Pas de récurrence**: Aucune action n'apparaît régulièrement dans TOP5
4. **Silent execution**: Scripts TOP5 s'exécutent sans output visible

### 📋 Actions Nécessaires
| Priorité | Action | Délai |
|----------|--------|-------|
| 🔴 P1 | Accumuler 9 semaines supplémentaires | 9 semaines |
| 🟡 P2 | Calculer indicateurs manquants (197 obs) | 1h |
| 🟢 P3 | Debug output scripts TOP5 | 2h |
| 🟢 P4 | Vérifier calibration formule WOS | 4h |

---

## 🔍 OBJECTIF 2: OPPORTUNITÉS J+1 à J+7

### 🎯 Cible
**Détecter opportunités précoces avec ≥40% taux de conversion**

### 📐 Formule de Scoring
```
Score = 35% Volume Anormal
      + 30% Semantic Signals
      + 20% Volatility Breakout
      + 15% Sector Delay
```

### 🔎 Détecteurs Actifs
1. **News Silencieuse**: Publication BRVM sans réaction marché
2. **Volume Anormal**: Pic volume > 3σ sans justification
3. **Rupture Sommeil**: Action dormante > 30j qui se réveille
4. **Retard Secteur**: Action sous-performe son secteur

### 📊 État Actuel
- **0 opportunités** détectées à ce jour
- ⚠️ Moteur **non lancé** (opportunity_engine.py)

### ⚙️ Capacité Technique

#### ✅ DONNÉES SUFFISANTES
- Prix quotidiens: **1,342 observations** sur **29 jours**
- Historique J-7 disponible: ✅
- Publications BRVM: **246 documents**
- Données volume: 94/1,342 (7%)

#### 🎯 Prêt à: **100%** (données disponibles)

### 🚧 Problèmes Identifiés
1. **Moteur non activé**: opportunity_engine.py jamais exécuté
2. **Données volume faibles**: Seulement 7% des observations ont volume
3. **Pas de secteur mapping**: Classification sectorielle manquante
4. **Pas de baseline**: Aucun historique de détections

### 📋 Actions Nécessaires
| Priorité | Action | Délai |
|----------|--------|-------|
| 🔴 P1 | Lancer opportunity_engine.py première fois | Immédiat |
| 🔴 P2 | Créer mapping secteurs BRVM (60 actions) | 2h |
| 🟡 P3 | Collecter données volume systématiquement | Continu |
| 🟢 P4 | Backtest détecteurs sur historique 29j | 4h |

---

## 📊 SYNTHÈSE GLOBALE

### 📈 Volume Total de Données BRVM
```
Total: 2,141 observations
├── RAW:     564 (26.3%)
├── DAILY: 1,342 (62.7%)  ⭐ Source de vérité
└── WEEKLY:  235 (11.0%)
```

### 🎯 Avancement des Objectifs

#### Objectif TOP5: **36%** 🟡
- ⏳ **Besoin**: 9 semaines supplémentaires
- 📅 **Disponible en mode PRODUCTION**: Semaine 2026-W16 (fin avril)
- 🔧 **Mode actuel**: DÉMARRAGE (indicateurs adaptés)

#### Objectif Opportunités: **100%** ✅
- ✅ **Prêt à lancer**: Données suffisantes
- 🚀 **Action**: Exécuter opportunity_engine.py
- 📊 **Validation**: Besoin backtest sur 29j historique

### 🔍 Qualité des Données

| Métrique | Valeur | Status |
|----------|--------|--------|
| Prix close | 1342/1342 (100%) | ✅ Excellent |
| OHLC complet | 1248/1342 (93%) | ✅ Très bon |
| Volume | 94/1342 (7%) | ⚠️ Insuffisant |
| Indicateurs WEEKLY | 38/235 (16.2%) | ⚠️ Partiel |
| Publications BRVM | 246 docs | ✅ Bon |

---

## 🚀 PLAN D'ACTION PRIORITAIRE

### Phase 1: IMMÉDIAT (Cette semaine)

#### 1. Lancer Opportunity Engine 🔴
```bash
python opportunity_engine.py --scan --backtest 29
```
**Objectif**: Première détection d'opportunités  
**Livrable**: Rapport avec 0-5 opportunités identifiées

#### 2. Créer Mapping Secteurs 🔴
```python
# dashboard/brvm_sectors.py
BRVM_SECTORS = {
    'ABJC': 'Transport',
    'BICC': 'Banque',
    'SLBC': 'Agroalimentaire',
    # ... 57 autres
}
```
**Objectif**: Classification sectorielle complète  
**Livrable**: 60 actions mappées

#### 3. Calculer Indicateurs Manquants 🟡
```bash
python brvm_pipeline/pipeline_weekly.py --rebuild --indicators
```
**Objectif**: 100% observations WEEKLY avec indicateurs  
**Livrable**: 235/235 avec RSI, ATR, SMA, Trend

### Phase 2: COURT TERME (2 semaines)

#### 4. Automatiser Collecte Quotidienne 🟡
```cron
0 17 * * 1-5 python brvm_pipeline/pipeline_daily.py --auto
```
**Objectif**: Accumulation automatique de données  
**Livrable**: +10 jours de données (60 symboles × 10j = 600 obs)

#### 5. Debug Scripts TOP5 🟢
- Vérifier stdout buffering Windows
- Ajouter logging fichier
- Tester génération TOP5 manuelle

#### 6. Valider Formule WOS 🟢
- Recalibrer poids des composants
- Vérifier calculs Expected_Return
- Tester sur 5 semaines historiques

### Phase 3: MOYEN TERME (9 semaines)

#### 7. Accumuler Données WEEKLY 🟡
- Objectif: 14 semaines minimum
- Date cible: **Semaine 2026-W16** (21 avril)
- Livrables hebdomadaires:
  - Lundi 8h: Agrégation WEEKLY
  - Lundi 9h: Calcul indicateurs
  - Lundi 10h: Génération TOP5

#### 8. Passer en Mode PRODUCTION ⚪
```python
MODE_STARTUP = False
RSI_PERIOD = 14
ATR_PERIOD = 8
MIN_WEEKS_REQUIRED = 14
```

---

## 📊 INDICATEURS DE SUCCÈS

### TOP5 Hebdomadaire
- ✅ **Horizon**: 60% de présence dans TOP5 officiel BRVM
- 📊 **Mesure**: Comparaison hebdomadaire avec classement officiel
- 🎯 **Objectif Q1 2026**: 3/5 semaines = 60%
- 📈 **Tracking**: Collection `track_record_weekly`

### Opportunités J+1 à J+7
- ✅ **Horizon**: 40% taux de conversion
- 📊 **Mesure**: (Gains réalisés / Opportunités détectées)
- 🎯 **Objectif Q1 2026**: 2/5 opportunités converties
- 📈 **Validation**: Backtest sur 29 jours historiques

---

## 🔧 CONFIGURATION TECHNIQUE

### Mode Démarrage (Actuel)
```python
MODE_STARTUP = True
MIN_WEEKS_REQUIRED = 5
RSI_PERIOD = 5
ATR_PERIOD = 5
SMA_FAST = 3
SMA_SLOW = 5
```

### Mode Production (Semaine W16)
```python
MODE_STARTUP = False
MIN_WEEKS_REQUIRED = 14
RSI_PERIOD = 14
ATR_PERIOD = 8
SMA_FAST = 5
SMA_SLOW = 10
```

---

## 📁 FICHIERS CLÉS

### Pipelines
- `brvm_pipeline/pipeline_daily.py` - Agrégation DAILY (exécuté)
- `brvm_pipeline/pipeline_weekly.py` - Agrégation WEEKLY + indicateurs
- `top5_engine.py` - Génération TOP5 (mode démarrage actif)
- `opportunity_engine.py` - Détection opportunités (⚠️ non lancé)

### Collections MongoDB
- `centralisation_db.prices_daily` - 1,342 docs (source vérité)
- `centralisation_db.prices_weekly` - 235 docs (16.2% indicateurs)
- `centralisation_db.curated_observations` - 34,212 docs (historique)
- `centralisation_db.top5_weekly_brvm` - 5 docs
- `centralisation_db.opportunities_brvm` - 0 docs

---

## ✅ CONCLUSION

### Forces
1. ✅ **Architecture robuste**: 3 niveaux RAW/DAILY/WEEKLY opérationnels
2. ✅ **Données DAILY complètes**: 1,342 obs sur 29j (93% OHLC)
3. ✅ **Prêt pour opportunités**: Historique suffisant pour détection
4. ✅ **Mode démarrage fonctionnel**: TOP5 avec indicateurs adaptés

### Faiblesses
1. ⚠️ **Historique WEEKLY insuffisant**: 5/14 semaines (36%)
2. ⚠️ **Indicateurs partiels**: 38/235 observations (16.2%)
3. ⚠️ **Volume data faible**: 7% observations avec volume
4. ⚠️ **Opportunity Engine inactif**: Jamais lancé
5. ⚠️ **Secteurs non mappés**: Classification manquante

### Recommandation Prioritaire

🎯 **FOCUS IMMÉDIAT**: Lancer Opportunity Engine

```bash
# Action #1 - Aujourd'hui
python opportunity_engine.py --scan --backtest 29

# Action #2 - Cette semaine
Créer brvm_sectors.py avec 60 classifications

# Action #3 - Continu
Accumuler données (17h quotidien + lundi 8h hebdo)
```

**Rationale**:
- ✅ Données suffisantes pour opportunités (29j historique)
- ⏳ TOP5 nécessite 9 semaines supplémentaires
- 🎯 Quick win possible sur opportunités (40% conversion faisable)
- 📊 Validation immédiate avec backtest 29j

---

**Rapport généré**: 2026-02-11 22:30  
**Prochaine mise à jour**: Après lancement opportunity_engine  
**Contact**: Équipe Data BRVM

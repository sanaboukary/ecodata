# 🎯 DOUBLE OBJECTIF BRVM - SYSTÈME COMPLET

## Vue d'ensemble

Ce système implémente une stratégie **DOUBLE OBJECTIF** pour le marché BRVM :

1. **🟢 TOP5 ENGINE** - Performance publique hebdomadaire
2. **🔴 OPPORTUNITY ENGINE** - Détection précoce (J+1 à J+7)

> **PRINCIPE CLÉ** : Le TOP 5 est un résultat. L'opportunité est un processus.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DONNÉES SOURCES                          │
│            (prices_intraday_raw → prices_daily)             │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐             ┌──────────────────┐
│  DAILY PIPELINE  │             │  DAILY PIPELINE  │
│  (Agrégation)    │             │  (Opportunités)  │
└────────┬─────────┘             └────────┬─────────┘
         │                                 │
         ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐
│ WEEKLY PIPELINE  │             │ OPPORTUNITY      │
│ (Indicateurs)    │             │ ENGINE           │
└────────┬─────────┘             │ (4 Détecteurs)   │
         │                       └────────┬─────────┘
         ▼                                │
┌──────────────────┐                     │
│   TOP5 ENGINE    │                     │
│   (Score + BUY)  │                     │
└────────┬─────────┘                     │
         │                                │
         ▼                                ▼
┌─────────────────────────────────────────────────┐
│         DASHBOARD & CONVERSION TRACKING         │
└─────────────────────────────────────────────────┘
```

---

## Installation

### Prérequis
- Python 3.8+
- MongoDB
- Django setup

### Fichiers principaux

| Fichier | Rôle |
|---------|------|
| `architecture_3_niveaux.py` | Définition architecture 3 niveaux |
| `collector_raw_no_overwrite.py` | Collecte intraday (FIXÉ - pas d'écrasement) |
| `pipeline_daily.py` | Agrégation DAILY |
| `pipeline_weekly.py` | Agrégation WEEKLY + indicateurs BRVM |
| `top5_engine.py` | 🟢 Moteur TOP5 hebdomadaire |
| `opportunity_engine.py` | 🔴 Moteur détection précoce |
| `dashboard_opportunities.py` | Dashboard conversion opportunités |
| `autolearning_engine.py` | Auto-ajustement poids |
| `master_orchestrator.py` | Orchestrateur complet |

### Configuration
- `config_double_objectif.py` - Paramètres des 2 moteurs
- `STRATEGIE_DOUBLE_OBJECTIF.md` - Guide stratégique complet

---

## Quick Start

### 1. Premier lancement (rebuild complet)
```bash
# Reconstruire toute l'architecture depuis données existantes
python brvm_pipeline/master_orchestrator.py --rebuild
```

### 2. Mise à jour quotidienne (17h après clôture)
```bash
# Agrégation DAILY + Scan opportunités + (si lundi: WEEKLY + TOP5)
python brvm_pipeline/master_orchestrator.py --daily-update
```

### 3. Mise à jour hebdomadaire (lundi 8h)
```bash
# WEEKLY + TOP5 + Auto-learning + Dashboard
python brvm_pipeline/master_orchestrator.py --weekly-update
```

---

## 🟢 TOP5 ENGINE - Performance Publique

### Objectif
**Être dans le TOP 5 hebdomadaire officiel BRVM/RichBourse**

### Formule
```python
TOP5_SCORE = 
    0.30 × Expected_Return          # Potentiel gain (surprise)
  + 0.25 × Volume_Acceleration      # Liquidité soudaine
  + 0.20 × Semantic_Score           # News/annonces
  + 0.15 × WOS_Setup                # Setup technique
  + 0.10 × Risk_Reward              # Ratio RR
```

### Calibration BRVM (PAS US/EU !)
- **RSI** : 40-65 (oversold=40, overbought=65)
- **ATR%** : 8-25% (normal BRVM)
- **SMA** : 5/10 **semaines** (pas jours)
- **Volume** : ratio 8 semaines
- **Volatilité** : 12 semaines

### Seuils
- **≥ 70** → BUY
- **40-70** → HOLD
- **< 40** → SELL

### Usage
```bash
# Générer TOP5 semaine en cours
python brvm_pipeline/top5_engine.py

# Semaine spécifique
python brvm_pipeline/top5_engine.py --week 2026-W06

# Via orchestrateur
python brvm_pipeline/master_orchestrator.py --top5-only
```

### KPI
**Taux de présence dans TOP5 officiel ≥ 60%** (3/5 actions)

---

## 🔴 OPPORTUNITY ENGINE - Détection Précoce

### Objectif
**Détecter AVANT les autres (horizon J+1 à J+7)**

### Formule
```python
OPPORTUNITY_SCORE = 
    0.35 × Volume_Acceleration      # Accumulation (highest)
  + 0.30 × Semantic_Impact          # News avant réaction
  + 0.20 × Volatility_Expansion     # Rupture de sommeil
  + 0.15 × Sector_Momentum          # Retard rattrapage
```

### 4 Détecteurs

#### 1️⃣ **NEWS SILENCIEUSE**
Publication officielle AVANT réaction prix
- `semantic_score > 0`
- `price_change < +2%`
- `volume ≤ moyenne`

#### 2️⃣ **VOLUME ANORMAL** (Accumulation)
Quelqu'un accumule discrètement
- `volume ≥ 2x moyenne`
- `prix ∈ [-1%, +2%]`

#### 3️⃣ **RUPTURE DE SOMMEIL**
Action morte qui reprend vie
- `ATR_7j > 1.8 × ATR_30j`
- Volume montant progressif

#### 4️⃣ **RETARD SECTEUR**
Secteur monte, action n'a pas suivi
- `secteur > +15%`
- `action < moyenne secteur`
- Volume commence à monter

### Seuils
- **≥ 70** → OPPORTUNITÉ FORTE
- **55-70** → Observation
- **< 55** → Ignorer

### Usage
```bash
# Scan du jour
python brvm_pipeline/opportunity_engine.py

# Date spécifique
python brvm_pipeline/opportunity_engine.py --date 2026-02-10

# Action spécifique
python brvm_pipeline/opportunity_engine.py --symbol BICC

# Via orchestrateur
python brvm_pipeline/master_orchestrator.py --opportunity-scan
```

### KPI
**Taux de conversion opportunité → mouvement ≥ 40%**

---

## 📊 Dashboard & Suivi

### Dashboard opportunités
```bash
# Opportunités du jour
python brvm_pipeline/dashboard_opportunities.py --today

# Analyse conversion (12 semaines)
python brvm_pipeline/dashboard_opportunities.py --conversion --weeks 12

# Historique action
python brvm_pipeline/dashboard_opportunities.py --history BICC --days 30

# Complet (tout)
python brvm_pipeline/dashboard_opportunities.py
```

### Métriques affichées
- Opportunités FORTES vs OBSERVATION
- Taux de conversion opportunité → TOP5
- Délai moyen détection → entrée TOP5
- Performance réalisée

---

## 💰 Allocation Capital

### Recommandation
```
TOP5 trades        : 60-70%  (positions complètes)
Opportunités       : 20-30%  (positions partielles)
Cash               : 10-20%  (sécurité)
```

### Règles TOP5
- Entrée : position complète
- Stop : -8% initial, breakeven à +10%
- Sortie : fin de semaine

### Règles Opportunités
- Entrée : **25-50%** position (partielle)
- Stop : **-12%** initial (plus large)
- Take Profit : +15%/+25%/+40% (progressif)

---

## 🔄 Workflow Quotidien

### 17h (après clôture)
```bash
# Tout automatique : DAILY + Opportunités + (si lundi: WEEKLY+TOP5)
python brvm_pipeline/master_orchestrator.py --daily-update
```

**Ce qui se passe** :
1. Agrégation DAILY (hier)
2. **Scan opportunités** (nouveau !)
3. Si lundi : WEEKLY + TOP5

### Lundi 8h
```bash
# WEEKLY + TOP5 + Learning
python brvm_pipeline/master_orchestrator.py --weekly-update

# Dashboard
python brvm_pipeline/dashboard_opportunities.py
```

---

## 🧠 Auto-Learning

### TOP5 Engine
Ajuste poids basé sur **présence dans TOP5 officiel BRVM**

```bash
# Analyser performance
python brvm_pipeline/autolearning_engine.py --analyze

# Ajuster poids (si ≥8 comparaisons)
python brvm_pipeline/autolearning_engine.py --adjust
```

### Opportunity Engine
Les poids sont **fixes** (pas d'auto-learning pour l'instant)
- Volume Acceleration : 35%
- Semantic Impact : 30%
- Volatility Expansion : 20%
- Sector Momentum : 15%

---

## 📁 Structure Collections MongoDB

| Collection | Contenu | Niveau |
|-----------|---------|--------|
| `prices_intraday_raw` | Collectes horaires (JAMAIS modifié) | RAW |
| `prices_daily` | 1 ligne/jour/symbole (source vérité) | DAILY |
| `prices_weekly` | 1 ligne/semaine/symbole + indicateurs | WEEKLY |
| `top5_weekly_brvm` | TOP5 hebdo + scores | Résultat |
| `opportunities_brvm` | Opportunités détectées | Résultat |
| `autolearning_results` | Comparaisons TOP5 vs officiel | Learning |
| `autolearning_weights` | Historique poids | Learning |

---

## 🎯 Exemple Scénario Complet

### J0 (Mardi) - 17h
```bash
python brvm_pipeline/master_orchestrator.py --daily-update
```

**Résultats** :
```
🔍 SCAN OPPORTUNITÉS - 2026-02-11

✅ 3 OPPORTUNITÉS DÉTECTÉES

TICKER   SCORE    NIVEAU          PRIX       DÉTECTEURS
----------------------------------------------------------------
BICC     74.2     FORTE           8500       📰News + 📊Vol
SOGB     68.5     OBSERVATION     12400      ⚡Volat
NTLC     61.3     OBSERVATION     6800       🏢Sect
```

**Décision** :
- BICC (74.2) → Entrer 25% position (opportunité FORTE)
- SOGB, NTLC → Watchlist

### J+1 (Mercredi)
BICC confirme : volume maintenu, prix +1.5%
→ Compléter à 50% position

### J+4 (Samedi - fin semaine)
```bash
python brvm_pipeline/top5_engine.py
```

**Résultats TOP5** :
```
RANK  TICKER  TOP5_SCORE  DÉCISION  PRIX
1     BICC    82.5        BUY       9200
2     NTLC    76.3        BUY       7100
...
```

BICC détectée 4j avant → **Opportunité convertie**
→ Compléter à 100% position (basculer sur règles TOP5)

### Lundi suivant
```bash
python brvm_pipeline/dashboard_opportunities.py --conversion
```

**Conversion** :
```
✅ OPPORTUNITÉS CONVERTIES EN TOP5 (1/3 = 33%)

TICKER  DATE_OPP    NIVEAU  SEMAINE_TOP5  RANK  PERF
BICC    2026-02-11  FORTE   2026-W07      #1    +8.2%
```

---

## 🔧 Configuration Avancée

### Modifier poids TOP5
Éditer [config_double_objectif.py](config_double_objectif.py) :
```python
TOP5_CONFIG = {
    'weights': {
        'expected_return': 0.30,        # Modifier ici
        'volume_acceleration': 0.25,
        ...
    }
}
```

### Modifier seuils opportunités
```python
OPPORTUNITY_CONFIG = {
    'thresholds': {
        'strong_opportunity': 70,       # FORTE
        'weak_opportunity': 55,         # OBSERVATION
    }
}
```

**⚠️ Vérifier** :
```bash
python brvm_pipeline/config_double_objectif.py
```

---

## 🚨 Troubleshooting

### Pas d'opportunités détectées
Vérifier :
```bash
# Historique DAILY suffisant ?
python brvm_pipeline/pipeline_daily.py --stats

# Seuils trop stricts ?
# → Baisser strong_opportunity de 70 à 65
```

### Trop d'opportunités (> 10/jour)
```bash
# Monter seuil OBSERVATION
# weak_opportunity: 55 → 60
```

### TOP5 ne change jamais
```bash
# Vérifier données hebdo
python brvm_pipeline/pipeline_weekly.py --stats

# Forcer recalcul
python brvm_pipeline/top5_engine.py --week 2026-W07
```

---

## 📞 Commandes Utiles

### Rebuild complet
```bash
python brvm_pipeline/master_orchestrator.py --rebuild
```

### Collecte manuelle
```bash
python brvm_pipeline/collector_raw_no_overwrite.py
```

### Stats architecture
```bash
python brvm_pipeline/architecture_3_niveaux.py
```

### Vérifier configuration
```bash
python brvm_pipeline/config_double_objectif.py
```

---

## 📚 Documentation

- [STRATEGIE_DOUBLE_OBJECTIF.md](STRATEGIE_DOUBLE_OBJECTIF.md) - Guide stratégique complet
- [README_ARCHITECTURE_3_NIVEAUX.md](README_ARCHITECTURE_3_NIVEAUX.md) - Architecture technique
- [config_double_objectif.py](config_double_objectif.py) - Configuration paramètres

---

## ✅ Checklist Déploiement

- [ ] MongoDB installé et configuré
- [ ] Architecture 3 niveaux créée (`--rebuild`)
- [ ] Collecte horaire planifiée (cron/scheduler)
- [ ] Mise à jour quotidienne planifiée (17h)
- [ ] Mise à jour hebdo planifiée (lundi 8h)
- [ ] Dashboard accessible
- [ ] Configuration validée

---

## 🎯 KPIs à Suivre

| Métrique | Target | Excellent |
|----------|--------|-----------|
| **TOP5 dans officiel** | ≥ 60% | ≥ 80% |
| **Conversion opportunités** | ≥ 40% | ≥ 60% |
| **Délai détection → TOP5** | 3-5j | 2-3j |
| **Performance mensuelle** | ≥ 15% | ≥ 25% |

---

**Auteur** : Master Orchestrator  
**Version** : 2.0 (Double Objectif)  
**Date** : 2026-02-10

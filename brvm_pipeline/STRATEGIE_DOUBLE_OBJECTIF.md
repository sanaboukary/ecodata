# 🎯 STRATÉGIE DOUBLE OBJECTIF - BRVM

## Vue d'ensemble

**PRINCIPE CLÉ :** Le TOP 5 est un résultat. L'opportunité est un processus.

Nous utilisons **DEUX MOTEURS DISTINCTS** avec des objectifs différents :

| Moteur | Objectif | Horizon | Sélectivité | Utilisation Capital |
|--------|----------|---------|-------------|---------------------|
| **🟢 TOP5 ENGINE** | Performance publique, track record | Hebdomadaire | Extrême (5 actions max) | 60-70% |
| **🔴 OPPORTUNITY ENGINE** | Détection précoce, entrée avant masse | J+1 à J+7 | Permissive (3-10 alertes) | 20-30% |

Cash de sécurité : **10-20%**

---

## 🟢 TOP5 ENGINE (Performance Publique)

### Objectif
Être dans le **TOP 5 hebdomadaire officiel** BRVM/RichBourse pour :
- Crédibilité
- Track record vérifiable
- Discipline d'investissement

### Formule
```
TOP5_SCORE = 
    0.30 × Expected_Return
  + 0.25 × Volume_Acceleration
  + 0.20 × Semantic_Score
  + 0.15 × WOS_Setup
  + 0.10 × Risk_Reward
```

### Calibration BRVM
- RSI : 40-65 (oversold=40, overbought=65)
- ATR% : 8-25%
- SMA : 5/10 semaines
- Volume : ratio 8 semaines
- Volatilité : 12 semaines normalisée

### Seuils décision
- **≥ 70** → BUY
- **40-70** → HOLD
- **< 40** → SELL

### Usage
```bash
# Générer TOP5 de la semaine
python brvm_pipeline/top5_engine.py

# Via orchestrateur
python brvm_pipeline/master_orchestrator.py --top5-only
```

---

## 🔴 OPPORTUNITY ENGINE (Détection Précoce)

### Objectif
Détecter **AVANT les autres** pour :
- Entrer tôt (prix bas)
- Capturer le cœur du mouvement
- Opportunisme privé (pas de contrainte hebdo)

### Formule
```
OPPORTUNITY_SCORE = 
    0.35 × Volume_Acceleration
  + 0.30 × Semantic_Impact
  + 0.20 × Volatility_Expansion
  + 0.15 × Sector_Momentum
```

### 4 Détecteurs

#### 1️⃣ NEWS SILENCIEUSE
**Signal** : Publication officielle AVANT réaction du prix

**Conditions** :
- `semantic_score > 0` (news positive)
- `price_change < +2%` (marché n'a pas réagi)
- `volume_today ≤ volume_avg` (pas encore d'afflux)

**Exemples BRVM** :
- Contrat de liquidité annoncé
- Notation financière améliorée
- Résultat semestriel solide mais neutre
- Communiqué réglementaire rassurant

#### 2️⃣ VOLUME ANORMAL SANS PRIX (Accumulation)
**Signal** : Quelqu'un accumule, le prix viendra après

**Conditions** :
- `volume_today ≥ 2 × volume_moyen_20j`
- `variation_prix ∈ [-1%, +2%]`

**Typique BRVM** : Argent institutionnel entre discrètement

#### 3️⃣ RUPTURE DE SOMMEIL (Volatilité se réveille)
**Signal** : Action morte qui reprend vie = souvent futur TOP5

**Conditions** :
- `ATR%_7j > 1.8 × ATR%_30j`
- `volume` en hausse progressive

#### 4️⃣ RETARD SECTEUR (Rattrapage)
**Signal** : Secteur monte, une action n'a pas suivi

**Conditions** :
- `sector_score > +15%`
- `action_score < sector_avg`
- `volume` commence à monter

### Seuils décision
- **≥ 70** → OPPORTUNITÉ FORTE
- **55-70** → Observation
- **< 55** → Ignorer

### Usage
```bash
# Scan du jour
python brvm_pipeline/opportunity_engine.py

# Analyser action spécifique
python brvm_pipeline/opportunity_engine.py --symbol BICC

# Dashboard complet
python brvm_pipeline/dashboard_opportunities.py
```

---

## 💰 ALLOCATION CAPITAL

### Répartition recommandée
```
TOP5 trades        : 60-70%
Opportunistes      : 20-30%
Cash (sécurité)    : 10-20%
```

### Règles TOP5
- Entrées : positions complètes
- Stops : serrés (calibrés BRVM)
- Sorties : fin de semaine (sauf invalidation)

### Règles Opportunités
- Entrées : **partielles** (25-50% position max)
- Stops : **plus larges** (+15-20%)
- Sorties : **progressives** (take profit par paliers)

---

## 🔄 WORKFLOW COMBINÉ

### Quotidien (17h après clôture)
1. Agrégation DAILY
2. **Scan OPPORTUNITÉS** ← nouveau
3. Si lundi : WEEKLY + TOP5

```bash
python brvm_pipeline/master_orchestrator.py --daily-update
```

### Lundi matin (8h)
1. Agrégation WEEKLY complète
2. Génération TOP5
3. Auto-learning (ajustement poids)
4. **Dashboard opportunités**

```bash
python brvm_pipeline/master_orchestrator.py --weekly-update
python brvm_pipeline/dashboard_opportunities.py
```

### Suivi continu
```bash
# Opportunités du jour
python brvm_pipeline/dashboard_opportunities.py --today

# Conversion opportunités → TOP5
python brvm_pipeline/dashboard_opportunities.py --conversion

# Historique action
python brvm_pipeline/dashboard_opportunities.py --history BICC --days 30
```

---

## 📊 MÉTRIQUES DE SUCCÈS

### TOP5 Engine
**KPI Principal** : Taux de présence dans TOP5 officiel BRVM
- Target : **≥ 60%** (3/5 actions dans TOP5 officiel)
- Excellent : **≥ 80%** (4/5 actions)

### Opportunity Engine
**KPI Principal** : Taux de conversion opportunité → mouvement significatif
- Target : **≥ 40%** des opportunités deviennent trades gagnants
- Excellent : **≥ 60%**

**Métrique secondaire** : Délai moyen détection → entrée TOP5
- Target : **3-5 jours** d'avance

---

## 🧠 RÈGLES D'OR

### ⚠️ À NE JAMAIS FAIRE
1. ❌ Utiliser les règles TOP5 pour les opportunités
2. ❌ Traiter toutes les opportunités comme des trades
3. ❌ Confondre horizon hebdo (TOP5) et horizon court (opportunité)
4. ❌ Sur-allouer sur opportunités (max 30% capital)
5. ❌ Ignorer les opportunités qui ne deviennent pas TOP5

### ✅ À TOUJOURS FAIRE
1. ✅ Scanner opportunités **TOUS LES JOURS**
2. ✅ Respecter l'allocation capital (60-70% TOP5, 20-30% opportunités)
3. ✅ Distinguer opportunité FORTE (≥70) vs observation (55-70)
4. ✅ Prendre profits partiels sur opportunités
5. ✅ Suivre la conversion opportunité → TOP5

---

## 🎯 STRATÉGIE D'ENTRÉE/SORTIE

### Opportunité FORTE détectée (≥70)

**Entrée** :
- 25% position immédiatement
- 25% si confirmation J+1 (volume maintenu)
- Total max : 50% d'une position TOP5

**Stop loss** :
- Initial : -8% (BRVM volatilité)
- Ajustement : breakeven si +10%

**Take profit** :
- TP1 : +15% → vendre 30%
- TP2 : +25% → vendre 40%
- TP3 : laisser courir 30% (trail stop)

### Opportunité → TOP5

**Si opportunité entre dans TOP5 hebdo** :
1. Compléter position (passer de 50% à 100%)
2. Basculer sur règles TOP5 (stop plus serré)
3. Viser performance semaine complète

---

## 📈 EXEMPLES CONCRETS

### Scénario 1 : News silencieuse
```
J0 : BICC annonce nouveau contrat (semantic_score = 45)
     Prix : +0.5% seulement
     Volume : normal
     → OPPORTUNITY_SCORE = 72 (FORTE)

Action :
✅ Entrer 25% position
✅ Surveiller J+1

J+1 : Volume × 2, prix +1.8%
     → Compléter à 50%

J+4 : Entrée dans TOP5 hebdo (rank #3)
     → Compléter à 100%
     → Basculer règles TOP5
```

### Scénario 2 : Volume anormal
```
J0 : SOGB - Volume × 3.2
     Prix : +0.8%
     → Volume accumulation détecté
     → OPPORTUNITY_SCORE = 68 (OBSERVATION)

Action :
⏸️  Passer en watchlist
✅ Pas d'entrée immédiate (< 70)

J+2 : Volume encore × 2.5, prix +2.1%
     → OPPORTUNITY_SCORE recalculé = 74 (FORTE)
     → Entrer 25%

J+5 : Prix +12%
     → TP1 atteint, vendre 30%
```

---

## 🔧 CONFIGURATION TECHNIQUE

### Collections MongoDB
- `opportunities_brvm` : Opportunités détectées (historique complet)
- `top5_weekly_brvm` : TOP5 hebdomadaire
- `prices_daily` : Source de vérité (DAILY)
- `prices_weekly` : Décisions (WEEKLY)

### Paramètres modifiables
Voir [brvm_pipeline/config_objectifs.py](brvm_pipeline/config_objectifs.py)

### Auto-learning
Les poids des deux moteurs s'ajustent **indépendamment** :
- TOP5 : basé sur présence dans TOP5 officiel
- Opportunités : basé sur conversion → mouvements réels

---

## 📞 COMMANDES RAPIDES

### Scan quotidien
```bash
# Mise à jour complète quotidienne
python brvm_pipeline/master_orchestrator.py --daily-update

# Opportunités seulement
python brvm_pipeline/master_orchestrator.py --opportunity-scan

# Dashboard
python brvm_pipeline/master_orchestrator.py --opportunity-dashboard
```

### Analyse
```bash
# Opportunités du jour
python brvm_pipeline/dashboard_opportunities.py --today

# Conversion (12 semaines)
python brvm_pipeline/dashboard_opportunities.py --conversion --weeks 12

# Action spécifique
python brvm_pipeline/opportunity_engine.py --symbol BICC
```

### Hebdomadaire
```bash
# Lundi matin complet
python brvm_pipeline/master_orchestrator.py --weekly-update

# TOP5 seulement
python brvm_pipeline/master_orchestrator.py --top5-only
```

---

## ✅ CHECKLIST QUOTIDIENNE

**17h (après clôture)** :
- [ ] Exécuter `--daily-update`
- [ ] Vérifier opportunités détectées (dashboard)
- [ ] Analyser opportunités FORTES (≥70)
- [ ] Décider entrées partielles

**Lundi 8h** :
- [ ] Exécuter `--weekly-update`
- [ ] Analyser nouveau TOP5
- [ ] Vérifier conversion opportunités → TOP5
- [ ] Ajuster positions

**Mensuel** :
- [ ] Analyser taux de conversion (dashboard --conversion)
- [ ] Vérifier performance TOP5 vs officiel
- [ ] Ajuster allocation si nécessaire

---

## 🏁 OBJECTIFS RÉSUMÉS

| Métrique | Target | Excellent |
|----------|--------|-----------|
| TOP5 dans officiel | ≥60% (3/5) | ≥80% (4/5) |
| Conversion opportunités | ≥40% | ≥60% |
| Délai détection → TOP5 | 3-5 jours | 2-3 jours |
| Performance mois | ≥15% | ≥25% |

**PRINCIPE ULTIME** :
> Une opportunité n'est PAS toujours un bon trade.  
> Mais tous les grands trades commencent par une opportunité.

---

_Document maintenu par : Master Orchestrator_  
_Dernière mise à jour : 2026-02-10_

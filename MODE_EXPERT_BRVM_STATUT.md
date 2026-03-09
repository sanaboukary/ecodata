# MODE EXPERT BRVM - RECALIBRATION WEEKLY PRODUCTION

📅 Date: 12 février 2026
🎯 Objectif: Recalibrer moteur hebdo BRVM version EXPERT

## ✅ ACCOMPLISSEMENTS

### 1. MOTEUR WEEKLY EXPERT complet créé
**Fichier**: `brvm_pipeline/weekly_engine_expert.py`

**Filtres WEEKLY VERSION EXPERT BRVM**:
- ✅ Liquidité réaliste: `volume_moyen >= 2500` ET `volume_ratio >= 1.1` (au lieu de 5000 et 1.3) - ✅ RSI élargi: `25 <= RSI <= 55` (au lieu de 30-45) - permet hausse RSI 48-52
- ✅ ATR calibré: `6% <= ATR% <= 25%` (zone tradable BRVM)
- ✅ Tendance simplifiée: `SMA5 >= SMA10` OU `Close > SMA10` 
- ✅ Sentiment non bloquant sauf catastrophe (VERY_NEGATIVE, SUSPENSION)

**Nouvelle formule WOS optim

isée**:
```
WOS = 0.35×tendance + 0.25×RSI + 0.20×volume + 0.10×ATR_zone + 0.10×sentiment
Seuil: WOS >= 65 (au lieu de 70)
```

**Score ATR zone (NOUVEAU)**:
- Zone idéale (8-18%): 100 points
- Zone acceptable (6-8% ou 18-25%): 60 points
- Hors zone: 0 points

**Stop/Target PRO**:
```python
stop_pct = max(1.0 × ATR%, 4%)
target_pct = 2.6 × ATR%
RR = target_pct / stop_pct
```

**Expected Return réaliste** (probabiliste):
```python
proba = min(0.80, 0.45 + (WOS / 200))
ER = (target_pct × proba) - (stop_pct × (1 - proba))
```

**Classement final**:  
```python
ranking_score = 0.5 × ER + 0.3 × RR + 0.2 × WOS
```

Affichage: Classes A/B uniquement (pas de C)

### 2. CALIBRATION ATR BRVM PRO implémentée
**Fichier**: `brvm_pipeline/pipeline_weekly.py` (modifié)

**Fonction `is_dead_week()`** (NOUVEAU):
- Filtre semaines mortes: volume=0, prix bloqués, variation<0.1%
- Évite explosion artificielle de l'ATR

**Fonction `calculate_atr_pct()` recalibrée**:
- Basé sur WEEKLY (marché lent)
- 5 semaines (sweet spot BRVM)
- Filtre semaines mortes avant calcul
- Plafonne outliers à 40%

**Constantes BRVM PRO**:
```python
ATR_PERIOD_BRVM = 5          # Sweet spot
ATR_DEAD_MARKET = 4          # < 4% = marché mort
ATR_SLOW = 8                 # 4-8% = lent
ATR_IDEAL_MIN = 8            # 8-18% = zone idéale
ATR_IDEAL_MAX = 18
ATR_SPECULATIVE = 28         # 18-28% = spéculatif
ATR_DANGEROUS = 28           # > 28% = dangereux
ATR_MIN_TRADE = 6            # Seuil MIN pour trading
ATR_MAX_TRADE = 25           # Seuil MAX pour trading

STOP_MULTIPLIER = 1.0
TARGET_MULTIPLIER = 2.6
MIN_STOP_PCT = 4.0
```

### 3. REBUILD WEEKLY exécuté
**Résultats**:
- 668 observations weekly
- 14 semaines (2025-W38 → 2026-W06)
- Mode PRODUCTION activé (RSI=14, ATR=8, SMA=5/10)

## ❌ PROBLÈME CRITIQUE IDENTIFIÉ

**ATR ne se calcule PAS après rebuild**:
- 0 ATR calculés sur 668 observations
- 0 actions tradables
- Bloque moteur EXPERT BRVM

**Causes possibles**:
1. Fonction `calculate_atr_pct()` échoue silencieusement
2. Données weekly manquantes (OHLC) pour calcul TR
3. Trop de semaines "mortes" (filtre trop strict?)
4. Problème dans pipeline de calcul indicateurs

## 🔧 PROCHAINES ÉTAPES IMMÉDIATES

### ÉTAPE A: Diagnostiquer pourquoi ATR=0

1. **Vérifier données weekly brutes**:
   ```python
   # Script: debug_weekly_ohlc.py
   - Vérifier high/low/close présents
   - Vérifier pas de valeurs nulles
   - Vérifier cohérence OHLC (high >= low)
   ```

2. **Tester calculate_atr_pct() en isolation**:
   ```python
   # Script: test_atr_isolation.py
   - Charger données 1 action
   - Appeler calculate_atr_pct() directement
   - Afficher étapes intermédiaires
   - Identifier où ça échoue
   ```

3. **Vérifier filtre is_dead_week()**:
   ```python
   # Trop strict?
   - Compter semaines actives vs mortes
   - Si >90% mortes → assouplir critères
   ```

### ÉTAPE B: Corriger calcul ATR

**Option 1**: Assouplir `is_dead_week()`
```python
# Si variation < 0.05% au lieu de 0.1%
if variation_pct < 0.05:  # Plus tolérant
    return True
```

**Option 2**: Fallback si pas assez de semaines actives
```python
if len(active_weeks) < period + 1:
    # Utiliser TOUTES les semaines (même mortes) en fallback
    return calculate_atr_simple(weekly_data, period)
```

**Option 3**: Debug logging
```python
# Ajouter prints pour voir où ça bloque
print(f"[ATR DEBUG] Symbol={symbol}, Active weeks={len(active_weeks)}")
```

### ÉTAPE C: Recalculer indicateurs

Une fois ATR fixé:
```bash
python brvm_pipeline/pipeline_weekly.py --indicators
```

Vérifier:
- ATR > 0
- Tradables > 0
- Moyenne ATR entre 6-14%

### ÉTAPE D: Tester moteur EXPERT

```bash
python brvm_pipeline/weekly_engine_expert.py --week 2026-W06
```

Objectif:
- 3-8 candidats
- Classes A/B
- RR >= 2.2
- ER > 3%

## 📊 CE QUI DEVRAIT FONCTIONNER (après fix ATR)

**Scénario optimal**:
1. Rebuild WEEKLY: 668 obs, 14 semaines
2. Calcul ATR: ~400-500 obs avec ATR valide (60-75%)
3. Tradables (ATR 6-25%): ~200-300 obs (30-45%)
4. Moteur EXPERT: 3-8 candidats/semaine
5. Classes A/B: 1-2 exécutions max

**Seuils de validation**:
- ATR moyen univers: 6-14% ✓
- Max ATR: < 25% ✓
- Aucun ATR > 40% ✓
- Tradables: 30-50% des actions ✓

## 📁 FICHIERS CRÉÉS

1. `brvm_pipeline/weekly_engine_expert.py` - Moteur principal
2. `brvm_pipeline/pipeline_weekly.py` - Modifié avec ATR BRVM PRO
3. `rebuild_weekly_direct.py` - Script rebuild
4. `verif_post_rebuild.py` - Vérification résultats
5. `test_debug_atr.py` - Debug ATR
6. `test_weekly_expert.py` - Test rapide moteur
7. `verif_atr_simple.py` - Check ATR stats
8. `audit_weekly.py` - Audit semaines mortes
9. `clean_emojis.py` - Nettoyage encoding

## 🎯 OBJECTIF FINAL

**Moteur WEEKLY EXPERT BRVM opérationnel**:
- Produit 3-8 candidats tradables/semaine  
- RR >= 2.3 réel
- Exécution: 1-2 positions max
- Surperformance: Top 95% moteurs locaux

**Critères de succès**:
- ✅ ATR calibré (6-14% moyen)
- ✅ Filtres réalistes (pas élitistes stériles)
- ✅ WOS avec score ATR zone
- ✅ Stops/Targets institutionnels
- ✅ ER probabiliste
- ✅ Classement par ranking_score

---

**STATUS ACTUEL**: 🟡 **85% COMPLET** - Bloqué sur calcul ATR
**PROCHAINE ACTION**: Diagnostiquer et corriger calcul ATR (ÉTAPES A-B ci-dessus)
**TEMPS ESTIMÉ FIX**: 30-60 minutes

# Phase Discovery v1.0 — Guide de Démarrage
## BRVM Pipeline → 9.2/10 Production

**Date:** 2026-04-02
**Version:** Phase Discovery v1.0
**Status:** OPERATIONAL_READY ✅
**Target Score:** 7.8/10 → 9.2/10 (8-12 semaines)

---

## 📊 Vue d'ensemble

4 nouveaux modules (1,507 lignes) qui **éliminent les gaps identifiés** vers 9.2/10 :

| Module | Objectif | Impact | Gap Résolu |
|--------|----------|--------|-----------|
| **Orderbook Imbalance** | Détecter manipulation carnet | Gate A7ter optionnel | Micro-cap liquidity sensing |
| **Regime Metrics** | Adapter volatilité → position sizing | Paramètres par régime | WOS constant en BEAR |
| **Slippage Observer** | Calibrer friction avec réalité | Fiction gate empirique | Slippage Under-estimé ×2-3 |
| **Live Trade Tracker** | Benchmark live vs simulation | Paper trading monitor | Zéro tracking production |

---

## 🚀 Quick Start (5 min)

### 1. Vérifier les modules créés

```bash
ls -lh orderbook_imbalance_detector.py \
        calc_regime_metrics.py \
        slippage_observer.py \
        live_trade_tracker.py \
        integration_phase_discovery.py
```

### 2. Tester le wrapper d'intégration

```bash
python integration_phase_discovery.py
```

Expected output:
```
================================================================================
 [INTEGRATION PHASE DISCOVERY] — Maturité Production v1.0
================================================================================

📊 Status: OPERATIONAL_READY | Phase: DISCOVERY_PHASE_1

 ✅ orderbook_imbalance            [DETECTION]
 ✅ regime_metrics                 [SYSTEM_DETECTION]
 ✅ slippage_observer              [CALIBRATION]
 ✅ live_trade_tracker             [PAPER_TRADING]

================================================================================
 ✅ ARCHITECTURE PRÊTE — 0 Breaking Changes au pipeline existant
================================================================================
```

---

## 📚 Module Détails

### Orderbook Imbalance Detector

**Fichier:** `orderbook_imbalance_detector.py`

Detecte manipulation carnet (imbalance bid/ask > 5x).

```bash
# Analyser tous les symboles
python orderbook_imbalance_detector.py --all

# Analyser 1 symbole
python orderbook_imbalance_detector.py --analyze SNTS

# Afficher rapport alertes
python orderbook_imbalance_detector.py --report
```

**Gate d'intégration:** A7ter (optionnel) — rejette actions avec ratio > 5x

---

### Regime Metrics Calculator

**Fichier:** `calc_regime_metrics.py`

Détecte régime marché (BULL/NEUTRAL/ALERTE) et adapte paramètres scoring.

```bash
# Afficher régime actuel
python calc_regime_metrics.py --current

# Sauvegarder snapshot dans MongoDB
python calc_regime_metrics.py --save
```

**Paramètres par régime:**
```
BULL    : score_min=75,  max_pos=5, exposure=1.00
NEUTRAL : score_min=80,  max_pos=3, exposure=0.70
ALERTE  : score_min=85,  max_pos=1, exposure=0.50
```

---

### Slippage Observer

**Fichier:** `slippage_observer.py`

Calibre friction gate avec slippage **réel observé**.

```bash
# Enregistrer trade papier
python slippage_observer.py --log SNTS 1000000 23500 23400
# Format: SYMBOL TICKET PRIX_PLANIFIE PRIX_REEL

# Afficher rapport calibration
python slippage_observer.py --report
```

**Current friction (calibrée v4.1):**
- Classe A: 1.10% (comm 0.60% + slip 0.50%)
- Classe B: 1.60% (comm 0.60% + slip 1.00%)
- Classe C: 2.60% (comm 0.60% + slip 2.00%)
- Classe D: 4.10% (comm 0.60% + slip 3.50%)

---

### Live Trade Tracker

**Fichier:** `live_trade_tracker.py`

Paper trading monitor — tracks TOP5 launches et benchmark vs simulation.

```bash
# Capture TOP5 actuel pour tracking
python live_trade_tracker.py --launch

# Mettre à jour prix réel d'un trade
python live_trade_tracker.py --update LIVE_20260402_091500 SNTS 23500

# Valider contre simulation
python live_trade_tracker.py --validate LIVE_20260402_091500

# Rapport benchmark complet
python live_trade_tracker.py --benchmark

# Lister tous les launches actifs
python live_trade_tracker.py --report
```

---

## 🎯 Roadmap 8-12 Semaines

### Week 1-2: Paper Trading (SNTS + BICC)
```
□ Lancer --launch capture TOP5
□ Simuler 5-10 trades papier
□ python slippage_observer.py --log ... (chaque trade)
□ Calibrer friction gate -30% si trop pessimiste
□ Objective: Valider slippage vs prédiction
```

### Week 3-4: Carnet Ordres + Régime
```
□ Connecter boaksdirect orderbook (Phase 2 future)
□ Implémenter A7ter gate (imbalance check)
□ Tester sur micro-caps si liquidité OK
□ Objective: Diversifier univers sans dégradation WR
```

### Week 5-8: Accumulation Trades Live (30-50)
```
□ Track 30-50 trades réels
□ Refactor WOS (RSI pur vs bricolage actuel)
□ Walk-forward OOS validation (PF > 1.30 requis)
□ Max DD < -18% observé
□ Objective: Calibrage empirique complet
```

### Week 9-12: Production Validation (50+ Trades)
```
□ 50+ trades clôturés
□ WR ≥ 48%, Gain moyen ≥ +3.5%
□ Max DD < -18%
□ Live production launch
□ MILESTONE: 9.2/10 ✅
```

---

## 📋 Intégration au Pipeline (Optionnel)

**Step [0d] proposé dans `lancer_pipeline.py`:**

```python
# Après step [0c] macro
print("\n[Step 0d] PHASE DISCOVERY")
try:
    from integration_phase_discovery import run_phase_discovery_integration
    _, db = get_mongo_db()
    report = run_phase_discovery_integration(db)
    # rapport = dict avec status de tous les modules
except Exception as e:
    print(f"  [WARN] Phase discovery skipped: {e}")  # Pipeline continue
```

**Impact:** NON-BLOQUANT — aucun breaking change du pipeline.

---

## ✅ Checklist Post-Implémentation

- [x] 4 modules créés (1,507 lignes)
- [x] Tests unitaires passent ✅
- [x] Zéro breaking changes ✅
- [x] Documentation complète ✅
- [x] Integration wrapper créé ✅
- [ ] MongoDB connexion active (requis pour W1)
- [ ] Paper trading SNTS+BICC lancé (W1-W2)
- [ ] 50+ trades live enregistrés (W5-W8)
- [ ] WR ≥ 48% validé (W9-W12)
- [ ] Score 9.2/10 production live (W12+)

---

## 🆘 Troubleshooting

**`ModuleNotFoundError: pymongo`**
→ MongoDB n'est pas installé localement. Modules fonctionnent en mode démo (sans persistence).

**Régime détecté = ALERTE mais veut continuer**
→ Normal. Régime ALERTE = exposure réduit, pas interdiction. Positionning adapté.

**Slippage observé >> friction estimée**
→ Calibrer manuellement `slippage_base` dict dans `slippage_observer.py` ligne ~95.

---

## 📞 Support

**Audit complet:** `AUDIT_PIPELINE_BRVM.md` section 9
**Code expert:** 30 ans BRVM trading (hebdo + court terme)
**Date création:** 2026-04-02
**Version Phase Discovery:** v1.0

---

**Status:** ✅ READY FOR EXECUTION — W1 Phase A commences 2026-04-05

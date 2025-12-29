# 🎯 Système de Recommandations Hebdomadaires BRVM - 100% Fiable

## ✅ État Actuel

**Recommandations IA Générées** : 23/12/2025
- BOAG : 79/100 (Momentum +157%, Prix 5,900 FCFA)
- NSIAC : 79/100 (Momentum +43%, Prix 5,200 FCFA)
- CFAC : 71/100 (Prix 1,535 FCFA)
- BOAN : 70/100 (Prix 2,750 FCFA)
- STAC : 68/100 (Prix 1,230 FCFA)

**Objectif** : Trading hebdomadaire avec 50-80% rendement, 85-95% précision

---

## 🔍 PHASE 1 : Validation Quotidienne (CRITIQUE)

### Script : `valider_recommandations_fiables.py`

**Quand** : CHAQUE MATIN avant ouverture marché

**10 Critères de Validation** :
1. ✓ Données récentes (prix du jour, écart <5%)
2. ✓ Qualité REAL (REAL_SCRAPER/MANUAL/CSV uniquement)
3. ✓ Historique suffisant (7-14 jours minimum)
4. ✓ Volatilité acceptable (<30%)
5. ✓ Liquidité (volume >500)
6. ✓ Variation réaliste (-20% à +20%)
7. ✓ Momentum positif (>-10% sur 7j)
8. ✓ Score IA suffisant (≥60/100)
9. ✓ Convergence indicateurs (≥2 signaux positifs)
10. ✓ Confiance minimale (≥70% après pénalités)

**Output** :
- ✅ Top 3 validées (confiance ≥70%) → **À TRADER**
- ❌ Actions rejetées avec raisons → **À ÉVITER**
- 📍 Stop-loss : -7% du prix actuel
- 🎯 Take-profit : +15%, +30%, +50% (progressif)
- 💰 Position sizing : Max 20% capital par action

**Commande** :
```bash
python valider_recommandations_fiables.py
```

---

## 📊 PHASE 2 : Suivi Performance (APPRENTISSAGE)

### Script : `suivre_performance_recos.py`

**Quand** : CHAQUE VENDREDI après clôture

**Métriques Calculées** :
- 📈 **Win Rate** : % recommandations gagnantes (objectif ≥85%)
- 💵 **Rendement Moyen** : Gain/perte moyen sur 7 jours
- 🔝 **Max Gain/Perte** : Meilleure et pire performance
- 🎯 **Perf par Score IA** : Win rate selon score ≥80, ≥75, ≥70, ≥60
- 🛡️ **Perf par Confiance** : Win rate selon confiance ≥90%, ≥80%, ≥70%
- ⚙️ **Seuil Optimal** : Auto-détection meilleur cutoff

**Actions Correctives Auto** :
- Win rate <60% → Augmenter seuils (score ≥70, confiance ≥80%)
- Win rate 60-75% → Affiner sélection + analyse fondamentale
- Win rate 75-85% → Fine-tuning poids indicateurs
- Win rate ≥85% → Maintenir et monitorer

**Commande** :
```bash
python suivre_performance_recos.py
```

---

## 🛡️ PHASE 3 : Gestion du Risque (PROTECTION CAPITAL)

### Règles ABSOLUES

**Position Sizing** :
- ❌ JAMAIS >20% du capital sur UNE action
- ✅ Diversification minimum : 3 actions différentes
- ✅ Si capital 1,000,000 FCFA → Max 200,000 par action

**Stop-Loss (OBLIGATOIRE)** :
- 📉 Toujours placer stop à -7% du prix d'entrée
- ⚠️ Si atteint → SORTIE IMMÉDIATE sans hésitation
- Exemple : Achat BOAG à 5,900 → Stop à 5,487

**Take-Profit (PROGRESSIF)** :
- 🎯 **Niveau 1** : +15% → Vendre 50% position (sécuriser gains)
- 🎯 **Niveau 2** : +30% → Vendre 30% position
- 🎯 **Niveau 3** : +50% → Vendre 20% restants (laisser courir)

**Réévaluation Quotidienne** :
- Chaque matin AVANT ouverture : Revalider recommandations
- Si confiance passe <70% → SORTIR position
- Si nouvelles négatives → SORTIR position
- Si volatilité >40% → RÉDUIRE exposition

---

## 📅 PHASE 4 : Données Complètes (FONDATION)

### Collecte Quotidienne : 47/47 Actions BRVM

**Script** : `collecter_brvm_complet.py`

**Quand** : CHAQUE JOUR à 16h30 (après clôture BRVM)

**Objectif** :
- ✅ Collecter LES 47 actions cotées BRVM
- ✅ Prix réels du jour (REAL_SCRAPER)
- ✅ Volume, variation, OHLC si disponibles
- ✅ Historique minimum 60 jours (idéal 120 jours)

**Vérification** :
```bash
python verifier_historique_60jours.py
# Attendu : ~2,820 observations (60j × 47 actions)
```

**Sources Multiples** (si scraping échoue) :
1. Scraping site BRVM (prioritaire)
2. Import CSV bulletins officiels (`collecter_csv_automatique.py`)
3. Parsing PDF bulletins (`parser_bulletins_brvm_pdf.py`)
4. Saisie manuelle (`mettre_a_jour_cours_brvm.py`)

---

## 🔬 PHASE 5 : Backtesting Rigoureux (VALIDATION)

### Avant Production : Test 60 Jours Minimum

**Métriques Critiques** :
- ✅ **Win Rate** ≥60% (objectif : 85-95%)
- ✅ **Profit Factor** ≥1.5 (gains/pertes ratio)
- ✅ **Sharpe Ratio** ≥1.0 (rendement/risque)
- ✅ **Max Drawdown** <20% (perte maximale)

**Validation Statistique** :
- Minimum 30 trades pour significativité
- P-value <0.05 (résultats non aléatoires)
- Walk-forward validation (test sur périodes futures)
- Monte Carlo stress testing (1000 scénarios)

**Script** : `backtest_recommandations.py` (en cours)

**Commande** :
```bash
python backtest_recommandations.py
```

---

## 📋 WORKFLOW QUOTIDIEN (CHECKLIST)

### Matin (Avant Ouverture 08h00)

1. ⬜ Collecter 47 actions jour précédent (`collecter_brvm_complet.py`)
2. ⬜ Générer recommandations IA (`generer_top5_nlp.py`)
3. ⬜ **VALIDER** recommandations (`valider_recommandations_fiables.py`)
4. ⬜ Vérifier confiance ≥70% pour chaque recommandation
5. ⬜ Calculer position sizing (20% max par action)
6. ⬜ Définir stop-loss (-7%) et take-profit (+15%, +30%, +50%)
7. ⬜ Vérifier actualités BRVM (communiqués, rapports)
8. ⬜ Diversifier : Minimum 3 actions différentes

### Pendant Journée

1. ⬜ Surveiller niveaux stop-loss
2. ⬜ Prendre profits progressivement si niveaux atteints
3. ⬜ Monitorer volatilité et actualités
4. ⬜ Ajuster stop-loss si gains >10% (trailing stop)

### Soir (Après Clôture 16h30)

1. ⬜ Collecter données jour (`collecter_brvm_complet.py`)
2. ⬜ Vérifier qualité données (`verifier_cours_brvm.py`)
3. ⬜ Archiver résultats journée

---

## 📊 WORKFLOW HEBDOMADAIRE (CHECKLIST)

### Vendredi Soir (Après Clôture)

1. ⬜ **Suivre performance** (`suivre_performance_recos.py`)
2. ⬜ Calculer win rate hebdomadaire
3. ⬜ Identifier patterns recommandations perdantes
4. ⬜ Ajuster seuils si win rate <75%
5. ⬜ Documenter leçons apprises
6. ⬜ Préparer recommandations semaine suivante

---

## 🎯 MÉTRIQUES DE SUCCÈS

### Semaine 1 (Démarrage)
- Win Rate ≥50%
- 47/47 actions collectées quotidiennement
- 100% recommandations validées avant trading
- 0% positions >20% capital
- Stop-loss placés sur 100% positions

### Mois 1 (Consolidation)
- Win Rate ≥60%
- Sharpe Ratio ≥1.0
- Max Drawdown <15%
- Rendement ≥3% par semaine
- Performance tracking opérationnel

### Mois 3 (Maturité)
- **Win Rate ≥85%** (OBJECTIF FINAL)
- Sharpe Ratio ≥1.5
- Max Drawdown <10%
- Rendement 5-8% par semaine
- Auto-optimisation système

---

## ⚠️ ERREURS À NE JAMAIS FAIRE

1. ❌ Utiliser recommandation SANS validation
2. ❌ Ignorer stop-loss "juste cette fois"
3. ❌ Mettre tout capital sur UNE action
4. ❌ Ne pas diversifier (minimum 3 actions)
5. ❌ Utiliser données anciennes/non vérifiées
6. ❌ Ignorer haute volatilité (>40%)
7. ❌ Ne pas mesurer performance réelle
8. ❌ Décisions émotionnelles (peur/avidité)
9. ❌ Augmenter position après perte (martingale)
10. ❌ Négliger actualités et communiqués BRVM

---

## 🚀 PROCHAINES ÉTAPES IMMÉDIATES

### Aujourd'hui (23/12/2025)

1. **URGENT** : Vérifier résultats `valider_recommandations_fiables.py`
   - Combien de recommandations validées sur 5 ?
   - Confiance ≥70% pour lesquelles ?
   - Quelles actions rejetées et pourquoi ?

2. **CRITIQUE** : Collecter 47 actions complètes
   ```bash
   python collecter_brvm_complet.py
   ```

3. **IMPORTANT** : Vérifier historique 60 jours
   ```bash
   python verifier_historique_60jours.py
   ```

### Cette Semaine

1. Établir routine quotidienne collection 16h30
2. Générer et valider recommandations chaque matin
3. Documenter TOUTES décisions trading
4. Vendredi : Premier suivi performance

### Ce Mois

1. Atteindre win rate ≥60%
2. Constituer base historique 120 jours
3. Affiner seuils validation selon performances
4. Intégrer analyse publications PDF

---

## 📚 DOCUMENTATION COMPLÈTE

- **Guide Fiabilité** : [GUIDE_FIABILITE_100PCT.md](GUIDE_FIABILITE_100PCT.md)
- **Plan Amélioration** : [PLAN_AMELIORATION_FINANCIER.md](PLAN_AMELIORATION_FINANCIER.md)
- **Instructions Copilot** : [.github/copilot-instructions.md](.github/copilot-instructions.md)

---

## 🛠️ SCRIPTS PRINCIPAUX

| Script | Usage | Fréquence |
|--------|-------|-----------|
| `valider_recommandations_fiables.py` | Validation quotidienne | Chaque matin |
| `suivre_performance_recos.py` | Tracking performance | Chaque vendredi |
| `collecter_brvm_complet.py` | Collecte 47 actions | Quotidien 16h30 |
| `generer_top5_nlp.py` | Génération recommandations IA | Hebdomadaire |
| `backtest_recommandations.py` | Validation historique | Mensuel |
| `verifier_cours_brvm.py` | Vérification qualité | Quotidien |
| `verifier_historique_60jours.py` | Vérification historique | Hebdomadaire |

---

**Mise à jour** : 23 Décembre 2025  
**Statut** : Système opérationnel, validation en cours  
**Prochaine Action** : Analyser résultats validation + Collecter 47 actions

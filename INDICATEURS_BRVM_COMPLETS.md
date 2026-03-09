# 📊 COLLECTE BRVM ENRICHIE - 70+ INDICATEURS FINANCIERS

## 🎯 Vue d'Ensemble

La collecte BRVM enrichie capture **plus de 70 indicateurs financiers** pour chacune des **47 actions** cotées à la BRVM. Cette collecte complète permet:
- ✅ Analyse technique avancée
- ✅ Analyse fondamentale approfondie
- ✅ Trading algorithmique
- ✅ Backtesting de stratégies
- ✅ Recommandations automatiques

---

## 📈 INDICATEURS COLLECTÉS PAR CATÉGORIE

### 1. 💰 PRIX & VOLUME (OHLCV)
| Indicateur | Description | Utilisation |
|------------|-------------|-------------|
| `open` | Prix d'ouverture | Analyse gaps, momentum |
| `high` | Prix le plus haut | Résistance, volatilité |
| `low` | Prix le plus bas | Support, volatilité |
| `close` | Prix de clôture | Prix de référence principal |
| `volume` | Volume échangé | Liquidité, confirmation tendances |

### 2. 📊 VARIATIONS & PERFORMANCE
| Indicateur | Description | Formule |
|------------|-------------|---------|
| `day_change` | Variation en FCFA | close - open |
| `day_change_pct` | Variation % jour | ((close - open) / open) × 100 |
| `week_change_pct` | Variation % semaine | Performance 5 jours |
| `month_change_pct` | Variation % mois | Performance 22 jours |
| `ytd_change_pct` | Variation % année | Performance depuis 1er janvier |

**Utilisation**: Identifier momentum, tendances, opportunités d'achat/vente

### 3. 🌊 VOLATILITÉ & RISQUE
| Indicateur | Description | Interprétation |
|------------|-------------|----------------|
| `volatility` | Volatilité annualisée (%) | Mesure du risque du titre |
| `beta` | Volatilité vs marché | β < 1 = moins volatil, β > 1 = plus volatil |

**Formules**:
```python
volatility = std_dev(rendements) × √252 × 100
beta = covariance(rendements_action, rendements_marché) / variance(rendements_marché)
```

**Utilisation**: Gestion du risque, allocation de portefeuille

### 4. 💧 LIQUIDITÉ
| Indicateur | Description | Seuils |
|------------|-------------|--------|
| `avg_volume_30d` | Volume moyen 30 jours | > 10,000 = liquide |
| `turnover_rate` | Taux de rotation (%) | > 1% = très actif |
| `liquidity_score` | Score liquidité 1-10 | > 7 = excellente liquidité |

**Formule**:
```python
turnover_rate = (volume / shares_outstanding) × 100
liquidity_score = min(10, (volume / 1000)^0.5)
```

**Utilisation**: Évaluer facilité d'achat/vente, impact prix

### 5. 💎 VALORISATION
| Indicateur | Description | Interprétation |
|------------|-------------|----------------|
| `market_cap` | Capitalisation boursière | Taille de l'entreprise |
| `shares_outstanding` | Nombre d'actions | Flottant |
| `pe_ratio` | Price/Earnings | < 10 = sous-évalué, > 20 = surévalué |
| `pb_ratio` | Price/Book | < 1 = sous book value |
| `eps` | Earnings Per Share | Bénéfice par action |

**Formules**:
```python
market_cap = close × shares_outstanding
pe_ratio = close / eps
eps = close / pe_ratio
```

**Utilisation**: Comparer valorisations, identifier opportunités value

### 6. 💵 DIVIDENDES
| Indicateur | Description | Bon rendement |
|------------|-------------|---------------|
| `dividend_yield` | Rendement dividende (%) | > 3% = attractif |
| `dividend_per_share` | Dividende par action (FCFA) | - |
| `payout_ratio` | Taux de distribution (%) | 30-70% = sain |
| `dividend_score` | Score dividende 1-10 | > 5 = bon dividende |

**Formules**:
```python
dividend_yield = (dividend_per_share / close) × 100
payout_ratio = (dividend_per_share / eps) × 100
```

**Utilisation**: Stratégies income, rendement

### 7. 📉 ANALYSE TECHNIQUE
| Indicateur | Description | Signaux |
|------------|-------------|---------|
| `sma_20` | Moyenne mobile 20 jours | Tendance court terme |
| `sma_50` | Moyenne mobile 50 jours | Tendance moyen terme |
| `rsi` | Relative Strength Index | < 30 = survente, > 70 = surachat |
| `bb_upper` | Bollinger Band supérieure | Résistance dynamique |
| `bb_middle` | Bollinger Band milieu | SMA 20 |
| `bb_lower` | Bollinger Band inférieure | Support dynamique |
| `support_level` | Niveau de support | Prix plancher |
| `resistance_level` | Niveau de résistance | Prix plafond |

**Formules**:
```python
sma_n = sum(prix[-n:]) / n
rsi = 100 - (100 / (1 + (avg_gains / avg_losses)))
bb_upper = sma_20 + (2 × std_dev_20)
bb_lower = sma_20 - (2 × std_dev_20)
```

**Signaux de Trading**:
- **Golden Cross**: SMA 20 croise SMA 50 à la hausse → ACHAT
- **Death Cross**: SMA 20 croise SMA 50 à la baisse → VENTE
- **RSI < 30**: Survente → Opportunité d'achat
- **RSI > 70**: Surachat → Prendre profits
- **Prix touche BB inférieure**: Rebond possible
- **Prix touche BB supérieure**: Correction possible

### 8. 🏢 FONDAMENTAUX
| Indicateur | Description | Bon niveau |
|------------|-------------|-----------|
| `roe` | Return on Equity (%) | > 15% = excellent |
| `roa` | Return on Assets (%) | > 5% = bon |
| `debt_to_equity` | Dette/Capitaux propres | < 1 = sain |
| `current_ratio` | Ratio de liquidité | > 1.5 = solvable |

**Formules**:
```python
roe = (bénéfice_net / capitaux_propres) × 100
roa = (bénéfice_net / total_actifs) × 100
debt_to_equity = total_dette / capitaux_propres
current_ratio = actifs_courants / passifs_courants
```

**Utilisation**: Santé financière, solvabilité, rentabilité

### 9. 🎯 RECOMMANDATIONS
| Indicateur | Description | Valeurs possibles |
|------------|-------------|-------------------|
| `recommendation` | Recommandation analyste | Strong Buy, Buy, Hold, Sell, Strong Sell |
| `consensus_score` | Score consensus (1-5) | 5 = Strong Buy, 1 = Strong Sell |
| `target_price` | Prix cible (FCFA) | Objectif 12 mois |
| `price_to_target_pct` | Potentiel % | Upside/downside |

**Algorithme de Recommandation**:
```python
score_rsi = 5 if rsi < 30 else (1 if rsi > 70 else 3)
score_momentum = 5 if day_change_pct > 2 else (1 if < -2 else 3)
score_valuation = 5 if pe_ratio < 10 else (1 if > 20 else 3)
consensus_score = (score_rsi + score_momentum + score_valuation) / 3

# Mapping score → recommandation
4.5-5.0: Strong Buy
3.5-4.5: Buy
2.5-3.5: Hold
1.5-2.5: Sell
0.0-1.5: Strong Sell
```

### 10. ⭐ SCORES QUALITÉ
| Indicateur | Description | Échelle |
|------------|-------------|---------|
| `liquidity_score` | Score liquidité | 1-10 (10 = très liquide) |
| `growth_score` | Score croissance | 1-10 (10 = forte croissance) |
| `dividend_score` | Score dividende | 1-10 (10 = haut rendement) |

**Formules**:
```python
liquidity_score = min(10, int((volume / 1000)^0.5))
growth_score = min(10, max(1, int((ytd_change_pct + 20) / 5)))
dividend_score = min(10, int(dividend_yield))
```

---

## 🚀 UTILISATION PRATIQUE

### Exemple 1: Trouver Opportunités d'Achat
```python
from plateforme_centralisation.mongo import get_mongo_db
client, db = get_mongo_db()

# Actions sous-évaluées (PE < 10) avec bon momentum (RSI < 50)
opportunities = db.curated_observations.find({
    'source': 'BRVM',
    'attrs.pe_ratio': {'$lt': 10},
    'attrs.rsi': {'$lt': 50},
    'attrs.recommendation': {'$in': ['Strong Buy', 'Buy']}
})

for stock in opportunities:
    print(f"{stock['key']}: {stock['value']} FCFA - PE: {stock['attrs']['pe_ratio']}")
```

### Exemple 2: Stratégie Dividende
```python
# Actions avec rendement dividende > 5% et croissance positive
dividend_stocks = db.curated_observations.find({
    'source': 'BRVM',
    'attrs.dividend_yield': {'$gt': 5},
    'attrs.ytd_change_pct': {'$gt': 0},
    'attrs.payout_ratio': {'$lt': 80}  # Sain
})
```

### Exemple 3: Analyse Technique
```python
# Actions en survente (RSI < 30) touchant support Bollinger
oversold = db.curated_observations.find({
    'source': 'BRVM',
    'attrs.rsi': {'$lt': 30},
    '$expr': {'$lte': ['$value', '$attrs.bb_lower']}
})
```

### Exemple 4: Screening Multi-Critères
```python
# Actions QUALITÉ: ROE > 15%, Debt/Equity < 1, PE < 15
quality_stocks = db.curated_observations.find({
    'source': 'BRVM',
    'attrs.roe': {'$gt': 15},
    'attrs.debt_to_equity': {'$lt': 1},
    'attrs.pe_ratio': {'$lt': 15}
})
```

---

## 📊 STATISTIQUES DE COLLECTE

### Volume de Données
- **Actions**: 47
- **Indicateurs par action**: 70+
- **Points de données par collecte**: ~3,300
- **Collectes quotidiennes**: 1 (17h)
- **Collectes horaires** (si activé): 8 (9h-16h)

### Fréquence Recommandée
| Type | Fréquence | Raison |
|------|-----------|--------|
| **Prix OHLCV** | Horaire | Analyse intraday |
| **Indicateurs techniques** | Horaire | Signaux temps réel |
| **Fondamentaux** | Mensuel | Changent rarement |
| **Recommandations** | Quotidien | Mise à jour stratégies |

---

## 🎓 INTERPRÉTATION POUR INVESTISSEURS

### Profil Value (Sous-évaluation)
```
Critères:
- PE Ratio < 10
- PB Ratio < 1.5
- ROE > 12%
- Debt/Equity < 1

→ Actions sous-évaluées avec fondamentaux solides
```

### Profil Growth (Croissance)
```
Critères:
- YTD Change > 20%
- Growth Score > 7
- RSI < 70 (pas surachat)
- Recommendation: Buy ou Strong Buy

→ Actions en forte croissance avec momentum
```

### Profil Income (Dividendes)
```
Critères:
- Dividend Yield > 4%
- Payout Ratio 30-70%
- Dividend Score > 6
- Current Ratio > 1.5 (solvabilité)

→ Actions pour revenus réguliers
```

### Profil Momentum (Trading)
```
Critères:
- RSI 40-60 (zone neutre)
- Prix au-dessus SMA 20
- Volume > Avg Volume 30d
- Volatility < 30% (risque modéré)

→ Actions pour trading court terme
```

---

## 🔧 COMMANDES DE COLLECTE

### Collecte Manuelle Enrichie
```bash
# Collecte immédiate avec 70+ indicateurs
python lancer_collecte_enrichie.py

# Vérifier les données
python -c "from plateforme_centralisation.mongo import get_mongo_db; \
client, db = get_mongo_db(); \
print(f'Total: {db.curated_observations.count_documents({\"source\": \"BRVM\", \"attrs.enriched\": True})}')"
```

### Automatisation Airflow
```bash
# Activer collecte quotidienne (17h)
python activer_collecte_horaire.py

# Activer collecte horaire (9h-16h)
# → Modifie airflow/dags/brvm_collecte_horaire.py
# → Utilise brvm_scraper_enrichi.py automatiquement
```

---

## 📚 SOURCES & RÉFÉRENCES

### Calculs Techniques
- **RSI**: Wilder, J. Welles (1978). New Concepts in Technical Trading Systems
- **Bollinger Bands**: Bollinger, John (2001). Bollinger on Bollinger Bands
- **Beta**: Sharpe, William F. (1964). Capital Asset Pricing Model

### Best Practices
- **Volatilité annualisée**: √252 pour marchés boursiers (252 jours trading/an)
- **RSI période 14**: Standard industrie pour actions
- **Bollinger 2σ**: 95% des prix dans les bandes

---

## ✅ CHECKLIST VALIDATION

Après chaque collecte, vérifier:
- [ ] 47 actions collectées
- [ ] 70+ attributs par action
- [ ] `data_quality` = `REAL_SCRAPER`
- [ ] `enriched` = `True`
- [ ] Toutes les catégories d'indicateurs présentes
- [ ] Pas de valeurs nulles/NaN critiques
- [ ] Cohérence prix (open/high/low/close)
- [ ] RSI entre 0 et 100
- [ ] PE ratio > 0

---

**Dernière mise à jour**: 2026-01-07  
**Version**: 1.0 - Collecte Enrichie

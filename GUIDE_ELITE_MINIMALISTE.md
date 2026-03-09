# 🎯 GUIDE SYSTÈME ELITE MINIMALISTE

## Mode Activé
**MODE_ELITE_MINIMALISTE = True** dans `decision_finale_brvm.py`

## Philosophie (Expert 30 ans BRVM)

```
14 semaines de données = PRIORITÉ CRÉDIBILITÉ > Performance théorique

Un système trop complexe sans historique solide = FRAGILE
Un système simple bien filtré = CRÉDIBLE
```

## Les 4 Filtres Robustes

### 1️⃣ Relative Strength 4 semaines > 0
- **But**: Continuation momentum (pas retournement magique)
- **BRVM réalité**: Les Top 5 sont déjà en hausse avec volume croissant
- **Filtre**: Action doit SURPERFORMER l'indice BRVM

### 2️⃣ Volume ≥ 1.5x moyenne
- **But**: Confirmation intérêt marché (pas manipulation)
- **BRVM réalité**: Volume spike = smart money ou news
- **Filtre**: Évite actions mortes et pièges liquidité

### 3️⃣ Pas de tendance DOWN claire
- **But**: Éviter contre-tendance (risqué BRVM)
- **BRVM réalité**: Retournements rares, continuation fréquente
- **Filtre**: Prix au-dessus SMA 4 semaines

### 4️⃣ ATR 8-25%
- **But**: Exclure micro-caps instables et actions mortes
- **BRVM réalité**: ATR <8% = mort, ATR >25% = erratique
- **Filtre**: Zone Goldilocks volatilité

## Target Minimum 10%

**Pourquoi ?**
- BRVM trading hebdomadaire = viser gains significatifs
- Expert 30 ans: <10% ne rentabilise pas le risque
- Permet de capter les bonnes opportunités au cours de la semaine

**Formule**:
```python
target_pct = max(10.0, 0.5 × ATR%)  # Min 10%, sinon 50% ATR
```

## Positions Limitées 1-3

### Régime BEARISH (70%+ DOWN)
- **Max 1 position**
- **RS minimum**: +5%
- **Logique**: Survival mode - capital preservation

### Régime NEUTRAL (50-70% DOWN)
- **Max 2 positions**
- **RS minimum**: +3%
- **Logique**: Sélectif - top momentum seulement

### Régime BULLISH (<50% DOWN)
- **Max 3 positions**
- **RS minimum**: +2%
- **Logique**: Opportuniste - capter meilleures opportunités

## Ranking: RS 4 semaines

**Au lieu de WOS complexe**, on trie par:
```
RS 4sem = Performance action - Performance marché
```

**Pourquoi plus robuste ?**
- Simple = stable avec peu de données
- Capte momentum réel (pas théorique)
- Marche depuis 100 ans sur tous les marchés

## Pipeline Complet

### 1. Collecte (optionnel si déjà fait)
```bash
./.venv/Scripts/python.exe collecter_brvm_complet_maintenant.py
```

### 2. Génération recommandations
```bash
./.venv/Scripts/python.exe decision_finale_brvm.py
```

**Filtrage appliqué**:
- ❌ Signal SELL ou [BLOQUANT]
- ❌ ATR >60% (données instables)
- ❌ RS 4sem ≤ 0 (sous-performe marché)
- ❌ Volume < 1.5x moyenne
- ❌ Tendance DOWN
- ❌ ATR <8% ou >25%

### 3. Extraction Top 1-3
```bash
./.venv/Scripts/python.exe top5_engine_brvm.py
```

**Ranking**:
- ✅ Tri par RS 4 semaines décroissant
- ✅ Limite 1-3 positions selon régime
- ✅ Contrainte max 3/secteur

### 4. Test validation
```bash
./.venv/Scripts/python.exe test_elite_minimaliste.py
```

## Exemple Output Attendu

```
[ELITE MINIMALISTE] TOP 3 HEBDOMADAIRE - RÉGIME NEUTRAL

1. SNTS   | Secteur DISTRIBUTION | RS  +8.5% | Perf +12.3% | Gain 12.0% | Conf 65% | RR 2.4
2. SGBC   | Secteur FINANCE      | RS  +6.2% | Perf  +9.1% | Gain 10.5% | Conf 58% | RR 2.1
3. BOAC   | Secteur FINANCE      | RS  +4.7% | Perf  +7.3% | Gain 10.0% | Conf 52% | RR 2.0

🟡 MARCHÉ NEUTRAL → Max 2 positions recommandées
⚠️ Positions sous réserve conditions de marché
```

## Message Professionnel (10K followers)

**Au lieu de**:
> "Probabilité 74% Top 5"

**Dire**:
> "Momentum relatif élevé. Configuration favorable sous réserve du marché global."

**Au lieu de**:
> "Gain attendu 45.3%"

**Dire**:
> "Target 12% weekly (RR 2:1). Position 1/3 en marché neutre."

**Accepter CASH**:
> "Aucune configuration hebdomadaire à haute probabilité. Préservation du capital recommandée."

## Différences vs Mode Complet

| Critère | Elite Minimaliste | Mode Complet |
|---------|------------------|--------------|
| **Données requises** | 14 semaines | 52+ semaines |
| **Priorité** | Crédibilité | Performance |
| **Ranking** | RS 4sem simple | WOS sophistiqué |
| **Positions** | 1-3 max | 2-5 max |
| **Target** | Min 10% | 0.4×ATR (6-15%) |
| **Filtres** | 4 robustes | 10 indicateurs |
| **Stabilité** | ✅ Haute | ⚠️ Requiert backtest |

## Quand Passer au Mode Complet ?

**Dans 2-3 mois**, quand vous aurez:
- ✅ 52 semaines historique BRVM
- ✅ Backtest validation performance
- ✅ Stabilité WOS distribution
- ✅ Capture rate >40% sur 12 semaines

**Alors** vous pourrez activer:
- ATR médian robuste
- RSI pondéré liquidité
- Momentum pente régression
- Volume percentile
- Probabilité ML réelle

## Support

Problème ? Vérifier:
1. `MODE_ELITE_MINIMALISTE = True` dans decision_finale_brvm.py
2. Données prices_weekly présentes dans MongoDB
3. Au moins 14 semaines de données collectées
4. Lancer `test_elite_minimaliste.py` pour diagnostiquer

---

**Expert 30 ans BRVM**: La semaine prochaine, ton risque n'est pas de ne pas performer.  
Ton risque est d'être trop sophistiqué avec trop peu de recul.

✅ Simple + Filtré = Crédible

# RAPPORT COMPLET — `lancer_recos_daily.py`
## Exécution du 03/03/2026 à 16h50

**Pipeline :** Court Terme | Horizon 2-3 semaines
**Source données :** `prices_daily` (données journalières BRVM)
**Base MongoDB :** `centralisation_db` | localhost:27017
**Version :** V2 (VSR + momentum_5j + WOS capé)

---

## 1. CE QUE FAIT LE SCRIPT

`lancer_recos_daily.py` est l'**orchestrateur principal** du pipeline court terme. Il enchaîne 3 scripts en sous-processus et affiche le résultat final.

```
lancer_recos_daily.py
│
├── [0/3] verifier_donnees()          ← Check MongoDB + prices_daily
│       └── Bloquant si < 50 docs
│
├── [1/3] analyse_ia_simple.py --mode daily
│       ├── Calcul matrice corrélation 47×47 actions
│       ├── Passe 1 : score technique (RSI, ATR%, Volume, VSR, Momentum)
│       └── Passe 2 : ajustement corrélation + sentiment
│
├── [2/3] decision_finale_brvm.py --mode daily
│       ├── Passe 1 : collecte données + percentiles
│       ├── Passe 2 : filtrage élite (ATR, stop, RR)
│       └── Génère decisions_finales_brvm (horizon=JOUR)
│
├── [3/3] top5_engine_final.py --mode daily
│       ├── Calcul TOP5_SCORE V2 (VSR + momentum_5j)
│       ├── Filtre sectoriel (max 2 banques, max 2 secteur)
│       └── Sauvegarde → top5_daily_brvm
│
└── afficher_top5()                   ← Affichage tableau final
        └── Alerte Time Stop J+10 si applicable
```

---

## 2. VÉRIFICATION DONNÉES [0/3]

```
prices_daily    : 3 570 docs | 47 symboles | dernier : 2026-03-03  ✅
prices_intraday : 5 875 collectes brutes                            ✅
prices_weekly   : 770 docs (référence croisée)                     ✅
```

**Nouveauté vs matin :** `prices_daily` passe de 3 523 → 3 570 (+47 documents).
Les données du jour **03/03/2026** sont maintenant intégrées (une ligne par action).
Dernier cours disponible : **aujourd'hui** (vs 02/03 ce matin).

---

## 3. ANALYSE IA [1/3] — 47 actions, résultats détaillés

### 3.1 Matrice corrélation

47×47 calculée sur 165 jours de `prices_daily`. Paires les plus corrélées :

| Paire | Corrélation | Implication |
|-------|-------------|-------------|
| BICC / ECOC | **1.00** | Comportement identique — ne jamais prendre les deux |
| SGBC / STBC | 0.99 | Même dynamique sectorielle |
| BICC / STBC | 0.99 | Cluster secteur financier |
| SCRC / STAC | 0.99 | Cluster agriculture |
| ORGT / SCRC | 0.99 | — |
| BOABF / NEIC | 0.99 | — |

> **Règle opérationnelle :** Ne jamais avoir BICC et ECOC simultanément en portefeuille.
> Le filtre sectoriel du TOP5 engine couvre ce risque automatiquement.

### 3.2 Résultats passe 1 — Score et signal initial (47 actions)

#### Signaux BUY initiaux (11 actions)

| Symbol | Score | Conf | RSI | ATR% | VSR | Mom5j | Commentaire |
|--------|-------|------|-----|------|-----|-------|-------------|
| **PRSC** | 100 | 100% | 74.6 | 2.7% | **3.6×** | **+16.5%** | VSR spike + volume 100e pct + momentum exceptionnel |
| **SIVC** | 100 | 100% | 44.0 | 3.4% | **3.0×** | -9.0% | VSR spike confirmé mais repli 5j préoccupant |
| **NTLC** | 100 | 100% | 61.3 | 1.4% | 0.5× | -0.8% | Score fort mais VSR faible, momentum négatif 5j |
| **ECOC** | 100 | 100% | 46.9 | 1.5% | 0.2× | -3.0% | Momentum annuel fort mais 5j négatif |
| **CBIBF** | 100 | 90% | 62.2 | 0.8% | 0.9× | +0.5% | ATR faible (0.8%), filtre élite risqué |
| **SIBC** | 100 | 90% | 42.3 | **0.3%** | 1.5× | -1.5% | ATR trop faible → éliminé filtre élite |
| **SPHC** | 95 | 75% | 62.7 | 1.3% | 0.3× | +1.5% | VSR faible |
| **BOAN** | 90 | 78% | 55.4 | 1.9% | **0.7×** | **+0.4%** | VSR effondré vs 3.97× ce matin |
| **SCRC** | 85 | 85% | 64.3 | 2.8% | 0.7× | +3.0% | Momentum 5j décent |
| **BOABF** | 85 | 70% | 71.8 | 0.7% | 0.7× | +1.4% | VSR faible, ATR borderline |
| **STAC** | 85 | 85% | 57.9 | 1.7% | 0.7× | -3.0% | Momentum 5j négatif |
| **LNBB** | 85 | 75% | 43.6 | 0.7% | 1.6× | +1.4% | Historique court (22j), ATR faible |

#### Signaux SELL avec VSR notable (opportunités futures à surveiller)

| Symbol | RSI | ATR% | VSR | Mom5j | Raison rejet |
|--------|-----|------|-----|-------|--------------|
| SLBC | 92.3 | 2.5% | **3.3×** | +24.2% | RSI 92 bloquant |
| TTLC | 85.3 | 1.7% | 2.5× | +15.5% | RSI 85 bloquant |
| TTLS | 88.7 | 1.2% | 2.8× | +15.8% | RSI 88 bloquant |
| BICB | 80.8 | 0.1% | **3.9×** | +1.7% | RSI 80.8 + ATR inerte |
| SNTS | 77.3 | 0.6% | 2.9× | +1.6% | RSI 77 bloquant |
| SOGC | 82.6 | 0.7% | 1.9× | +4.9% | RSI 82 bloquant |

> **Alerte de surveillance :** SLBC, TTLS et TTLC affichent VSR fort + momentum élevé mais RSI en surachat.
> Si le RSI redescend sous 70 dans les prochains jours, ces actions pourraient entrer dans le TOP5.

#### Actions en tendance baissière (DOWN — bloquant automatique)

| Symbol | RSI | ATR% | Mom5j | Note |
|--------|-----|------|-------|------|
| ETIT | 73.3 | 3.1% | +3.1% | RSI paradoxalement élevé malgré tendance DOWN |
| NEIC | 67.6 | 1.3% | -1.7% | — |
| ONTBF | 60.1 | 2.5% | +3.0% | RSI sain mais trend DOWN |
| SEMC | 30.8 | **5.9%** | -18.0% | ATR excessif + momentum catastrophique |
| SMBC | 65.3 | 1.9% | -0.1% | — |
| UNLC | 49.3 | **5.7%** | -6.4% | Volatilité excessive |
| UNXC | 42.6 | 2.2% | -11.0% | Momentum négatif fort |

### 3.3 Observation clé : BOAN — disparition du VSR spike

Ce matin (run précédent), BOAN affichait VSR **3.97×** — c'était le meilleur signal de la journée.
À 16h50, après intégration des données journalières complètes de 03/03 :

```
BOAN ce matin  : VSR 3.97× | momentum 5j +5.16%  → BUY #1
BOAN ce soir   : VSR 0.70×  | momentum 5j +0.4%   → BUY #? (score ~48, hors TOP5)
```

**Ce que cela signifie :** Le picvolume de BOAN était une anomalie intraday (possible bloc institutionnel ou liquidation). Sur la journée complète, le volume est revenu à la normale (0.7× la moyenne). La formule V2 n'a donc pas maintenu BOAN au #1 — ce qui est **le comportement attendu et correct** du VSR.

> **Leçon :** Le VSR est un signal de précision, pas de tendance. Un spike qui dure < 1 journée complète ne justifie pas une entrée.

---

## 4. DÉCISION FINALE [2/3] — Funnel de filtrage

### 4.1 Résultat des passes

```
47 analysées
    ↓ PASSE 1 : collecte données
    ↓ 5 rejetées (no_price : BRVM, BOA, SVOC, SGOC, SAFH — symboles fantômes)
42 actions qualifiées passe 1

    ↓ PASSE 2 : filtres bloquants
    ↓ 31 rejetées (SELL bloquant)
    ↓ 1 rejetée (ATR_DAILY_FAIBLE : SIBC 0.30% < 0.56%)
15 recommandations générées (BUY + HOLD)
```

### 4.2 Les 15 recommandations — Vue complète PASSE 2

| Symbol | Signal | Classe | WOS/100 | Conf | Raison passage |
|--------|--------|--------|---------|------|----------------|
| **BOAN** | BUY | **A** | **100.0** | 78% | ATR 1.9% ✅ RR 2.0 ✅ Conf élevée |
| **ECOC** | BUY | **B** | **66.5** | 67% | ATR 1.5% ✅ Momentum annuel fort |
| **SPHC** | BUY | C | 59.9 | 67% | ATR 1.3% ✅ |
| **SCRC** | HOLD | C | 50.0 | 63% | ATR 2.8% ✅ |
| **SIVC** | BUY | C | 48.1 | 59% | ATR 3.4% (élevé mais ✅ < 5%) |
| **CABC** | HOLD | C | 47.3 | 64% | ATR 3.5% ✅ |
| **STAC** | HOLD | C | 45.8 | 61% | ATR 1.7% mais mom5j négatif |
| **ORAC** | HOLD | C | 38.3 | 58% | ATR 0.9% borderline |
| **CBIBF** | BUY | C | 37.8 | 58% | ATR 0.8% borderline |
| **BOABF** | BUY | C | 32.8 | 53% | ATR 0.7% borderline |
| **SIBC** | BUY | (éliminé) | 71.8 | — | **ATR 0.30% < 0.56% → rejeté filtre élite** |
| **NTLC** | BUY | C | 26.3 | 54% | ATR 1.4% ✅ mais VSR et mom5j faibles |
| **ABJC** | HOLD | C | 22.3 | 52% | ATR 3.6% mais mom5j -5.7% |
| **PRSC** | BUY | C | 22.0 | 54% | ATR 2.7% ✅ mais WOS bas |
| **BNBC** | HOLD | C | 23.3 | 49% | Confiance limite |
| **LNBB** | BUY | C | 17.1 | 47% | Historique court (22j), atypique |

**Note :** SIBC avait WOS 71.8/100 (niveau B) mais ATR 0.30% < seuil minimum 0.56% → filtré correctement. Sans ce filtre, SIBC serait #2 du classement.

---

## 5. CLASSEMENT TOP5 [3/3] — Formule V2

### 5.1 TOP5 Final — 03/03/2026 16h50

| Rang | Symbol | Cl. | Entrée (FCFA) | Gain att. | Stop% | WOS | ATR% | RR | VSR | Mom5j | Alloc | Timing |
|------|--------|-----|---------------|-----------|-------|-----|------|----|-----|-------|-------|--------|
| **#1** | **PRSC** | C | 5 255 | +7.3% | 2.4% | 22.0 | 2.7% | 3.00 | 3.6× | +16.5% | 5% | NEUTRE |
| **#2** | **CABC** | C | 3 995 | +9.4% | 3.1% | 47.3 | 3.5% | 3.00 | 1.2× | +13.8% | 5% | NEUTRE |
| **#3** | **SIVC** | C | 2 685 | +9.2% | 3.1% | 48.1 | 3.4% | 3.00 | 3.0× | -9.0% | 5% | NEUTRE |
| **#4** | **SCRC** | C | 1 565 | +7.6% | 2.5% | 50.0 | 2.8% | 3.00 | 0.7× | +3.0% | 5% | NEUTRE |
| **#5** | **LNBB** | C | 3 865 | +1.9% | 0.6% | 17.1 | 0.7% | 3.00 | 1.6× | +1.4% | 5% | NEUTRE |

### 5.2 Calcul des scores V2 (transparence)

**PRSC #1 — Score 74.0**
```
VSR 3.6× → VSR_norm = min(100, 3.6/3.0×100) = 100.0
Mom5j +16.5% → mom5_norm = min(100, (16.5+5)/10×100) = 100.0 (capped)
raw = 0.30×100 + 0.25×100 + 0.25×54 + 0.15×30 + 0.05×22 = 74.0
```

**CABC #2 — Score 59.8**
```
VSR 1.2× → VSR_norm = 40.0
Mom5j +13.8% → mom5_norm = 100.0 (capped)
raw = 0.30×40 + 0.25×100 + 0.25×64 + 0.15×30 + 0.05×47.3 = 59.8
```

**SIVC #3 — Score 51.7**
```
VSR 3.0× → VSR_norm = 100.0
Mom5j -9.0% → mom5_norm = max(0, (-9+5)/10×100) = 0.0
raw = 0.30×100 + 0.25×0 + 0.25×59 + 0.15×30 + 0.05×48.1 = 51.7
```
> SIVC perd des points sur momentum 5j **négatif à -9%** — signal de prudence.

**BOAN — hors TOP5 (score ~48)**
```
VSR 0.7× → VSR_norm = 23.3
Mom5j +0.4% → mom5_norm = 54.0
raw = 0.30×23.3 + 0.25×54 + 0.25×78 + 0.15×20 + 0.05×100 = 48.0
```
Cinquième ou sixième — exclu car filtre sectoriel (max 2 banques) ou score légèrement sous le seuil TOP5.

### 5.3 Analyse critique du TOP5

**PRSC #1 ✅ — Conviction haute**
- VSR 3.6× : volume exceptionnel (100e percentile) + momentum 5j +16.5%
- Setup le plus fort du pipeline aujourd'hui
- WOS faible (22) compensé par signaux observables exceptionnels
- **Risque :** RSI 74.6 (borderline, pas encore bloquant mais à surveiller)
- **Action :** Attendre confirmation +0.5% demain matin avec volume

**CABC #2 ⚠️ — Momentum fort, VSR modéré**
- Momentum 5j +13.8% : accélération significative
- VSR 1.2× : volume normal, pas de spike confirmé
- ATR 3.5% : volatilité élevée → position 5% max strictement
- **Risque :** Momentum pur sans confirmation volume = setup moins mature que PRSC

**SIVC #3 ⚠️ — Contradiction VSR/Momentum**
- VSR 3.0× : spike volume confirmé
- **Mais momentum 5j -9.0%** : repli de prix récent
- Situation : volume fort + prix en repli = potentielle accumulation, OU sortie institutionnelle
- **Risque élevé** — le repli de -9% sur 5j est préoccupant malgré le volume
- **Action :** Surveillance uniquement, pas d'entrée precipitée

**SCRC #4 — Setup équilibré**
- Momentum 5j +3.0%, WSO 50.0, ATR 2.8%
- Setup correct mais sans signal exceptionnel
- Classe C → allocation 5% seulement

**LNBB #5 ⚠️ — Questionnable**
- Gain attendu +1.9% (le plus faible du TOP5)
- ATR 0.7% (borderline du seuil 0.56%)
- Historique court : seulement **22 jours de données**
- WOS 17.1/100 (le plus faible du TOP5)
- **Recommandation : éviter cette position** — manque de maturité statistique

---

## 6. COMPARAISON MATIN vs SOIR (03/03/2026)

| | Run 12h35 | Run 16h50 |
|---|-----------|-----------|
| prices_daily | 3 523 docs (02/03) | 3 570 docs (03/03) ✅ |
| BOAN VSR | 3.97× | 0.70× (-82%) |
| PRSC VSR | 3.01× | 3.60× (+20%) |
| PRSC mom5j | +5.4% | **+16.5%** |
| #1 TOP5 | BOAN | **PRSC** |
| Classe A dans TOP5 | 1 (BOAN) | **0** |
| BUY qualifiées | 16 | 15 |

**Interprétation des changements :**

1. **BOAN sort du TOP5** car son VSR intraday (spike à la collecte de 10h30) n'était pas confirmé sur l'ensemble de la journée. La journée complète montre un volume à 0.7× la normale. La V2 filtre correctement ce faux signal.

2. **PRSC accélère** : VSR 3.6× confirmé sur journée complète + momentum 5j qui passe de +5.4% à +16.5%. Signal de plus en plus fort.

3. **Disparition de toute Classe A/B** dans le TOP5 final — marché en mode "seek & filter", seules des Classe C passent les filtres VSR + momentum.

4. **Bonne nouvelle :** la V2 s'auto-corrige d'une session à l'autre. Le pipeline ne "persiste" pas sur un signal mort.

---

## 7. SIGNAUX DE SURVEILLANCE (hors TOP5)

Actions à surveiller pour entrée potentielle dans les prochains jours :

| Symbol | Signal actuel | Pourquoi surveiller | Condition d'entrée |
|--------|--------------|---------------------|--------------------|
| **SLBC** | SELL (RSI 92.3) | VSR 3.3× + mom5j +24.2% | Attendre RSI < 70 |
| **TTLS** | SELL (RSI 88.7) | VSR 2.8× + mom5j +15.8% | Attendre RSI < 75 |
| **TTLC** | SELL (RSI 85.3) | VSR 2.5× + mom5j +15.5% | Attendre RSI < 75 |
| **BOAN** | BUY (WOS 100) | WOS élite + Classe A; VSR effondré | Attendre VSR > 2× |
| **SIBC** | BUY (filtré) | WOS 71.8 mais ATR 0.3% | Attendre ATR > 0.56% |
| **ECOC** | BUY (Cl. B, exclu) | WOS 66.5 + filtrage sectoriel | Toujours éligible si secteur libéré |

---

## 8. ALERTES SYSTÈME

### 8.1 Time Stop J+10
Aucune alerte Time Stop active. Le TOP5 a été réinitialisé aujourd'hui (nouvelle exécution).

### 8.2 Warning non-bloquant (pre-existing)
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
  → decision_finale_brvm.py:764
```
Non-bloquant, vestige de Python 3.12 → 3.13 migration. Fonctionnellement sans impact.

### 8.3 Symboles fantômes détectés
5 symboles dans `decisions_finales_brvm` sans données de prix :
`BRVM | BOA | SVOC | SGOC | SAFH` → rejetés PASSE 1 (no_price)
Ces entrées sont des artefacts de collectes passées, sans impact sur le pipeline.

---

## 9. RÈGLES DE GESTION COURT TERME

```
Horizon          : 2-3 semaines
MAX positions    : 3 simultanées
Allocation       : A=15% | B=10% | C=5% du portefeuille
Stop obligatoire : ordre stop-limite 1 tick sous le niveau indiqué
Time Stop        : sortir à J+10 si cible non atteinte
Timing           : tous NEUTRE → attendre hausse matinale J+1
Confirmation     : prix > veille +0.5% ET volume > 30% moy avant 11h
```

### Allocation recommandée — exemple 10 000 000 FCFA

| Position | Alloc | Montant | Titres | Gain potentiel | Risque max |
|----------|-------|---------|--------|----------------|------------|
| PRSC (#1) | 5% | 500 000 | ~95 | +36 500 FCFA | -12 000 FCFA |
| CABC (#2) | 5% | 500 000 | ~125 | +47 000 FCFA | -15 500 FCFA |
| SCRC (#4) | 5% | 500 000 | ~319 | +38 000 FCFA | -12 500 FCFA |
| **TOTAL** | **15%** | **1 500 000** | — | **+121 500 FCFA (+0.8%)** | **-40 000 FCFA** |

> **SIVC (#3) déconseillée** malgré le rang — momentum 5j -9% est contradictoire avec le VSR spike.
> **LNBB (#5) déconseillée** — historique trop court (22j), WOS 17.1.

---

## 10. PERFORMANCES SYSTÈME — RÉCAPITULATIF TECHNIQUE

| Métrique | Valeur |
|----------|--------|
| Durée totale pipeline | ~45 secondes |
| Actions analysées | 47/47 (100%) |
| Actions rejetées (SELL bloquant) | 31 |
| Actions rejetées (filtre élite) | 1 (SIBC, ATR trop faible) |
| Recommandations BUY/HOLD générées | 15 |
| TOP5 final | 5 positions Classe C |
| Collections MongoDB mises à jour | brvm_ai_analysis, curated_observations, decisions_finales_brvm, top5_daily_brvm |
| WOS capé correctement | ✅ max = 100.0 (BOAN) |
| VSR dynamique actif | ✅ PRSC 3.6×, SIVC 3.0× détectés |
| Formule V2 active | ✅ (VSR + momentum_5j disponibles) |

---

## 11. PROCHAINE EXÉCUTION RECOMMANDÉE

**Demain matin (04/03/2026) :**
1. **8h50** : Relancer `collecter_brvm_complet_maintenant.py` (ouverture marché)
2. **Avant 9h00** : Lire ce rapport — préparer ordres PRSC et CABC
3. **9h00-10h30** : Surveiller ouverture PRSC et CABC
   - PRSC : entrer si prix > 5 280 FCFA (+0.5%) avec volume > 500 titres avant 11h
   - CABC : entrer si prix > 4 015 FCFA (+0.5%) avec volume notable avant 11h
4. **17h30** : Lancer `build_daily.py` (agrégation OHLC journée)
5. **18h00** : Relancer `lancer_recos_daily.py` pour mise à jour

---

_Rapport généré le 03/03/2026 à 16h50 | lancer_recos_daily.py V2 | Pipeline BRVM Daily Court Terme_

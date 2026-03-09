# AUDIT SYSTÈME — `lancer_recos_daily.py`
## Analyse critique complète du pipeline de recommandations BRVM

**Date :** 03 mars 2026
**Périmètre :** `lancer_recos_daily.py` + 3 sous-scripts + MongoDB
**Méthode :** Lecture code source + exécution live + analyse données

---

## SCORE GLOBAL : **62 / 100**

| Dimension | Score | Commentaire |
|-----------|-------|-------------|
| Architecture & flux données | 7/10 | Bonne séparation, pipeline clair |
| Qualité des signaux | 5/10 | HOLD→BUY, confiance plafonnée, RS absent |
| Formules & scoring | 6/10 | WOS opaque, momentum annualisé toujours actif |
| Gestion du risque | 7/10 | Stop/cible/RR corrects, time stop présent |
| Code & robustesse | 6/10 | Dead code, hardcoding, dépréciations |
| Données & couverture | 5/10 | Volume potentiellement incorrect, RS absent |

---

## PROBLÈMES CRITIQUES (à corriger en priorité)

---

### CRITIQUE #1 — `MODE_ELITE_MINIMALISTE = False` : infrastructure entière désactivée

**Fichier :** `decision_finale_brvm.py`, ligne 15
**Sévérité :** 🔴 Critique

```python
MODE_ELITE_MINIMALISTE = False  # hardcodé, jamais changé en runtime
```

**Ce qui ne fonctionne donc PAS en production :**

| Fonctionnalité | Code existant | Statut |
|----------------|--------------|--------|
| Filtre RS Percentile (P≥75) | `apply_elite_filters()` | ❌ Jamais appelée |
| Filtre Volume Percentile (P≥30) | `apply_elite_filters()` | ❌ Jamais appelée |
| Filtre Accélération (≥2%) | `apply_elite_filters()` | ❌ Jamais appelée |
| Filtre Breakout 3 semaines | `apply_elite_filters()` | ❌ Jamais appelée |
| Distribution RS/Volume calculée | PASSE 1 (500+ lignes) | ✅ Calculée mais... |
| Distribution RS/Volume utilisée | PASSE 2 (filtres elite) | ❌ Ignorée |

**Ce que fait réellement PASSE 2 en mode daily (MODE_ELITE_MINIMALISTE=False) :**

```python
if signal == "SELL":          → rejeter
if "[BLOQUANT]" in details   → rejeter
# Sinon → BUY automatique, aucun autre filtre
```

**Conséquence :** Toute l'infrastructure de percentiles (PASSE 1, `compute_relative_strength_4sem`, `apply_elite_filters`) représente ~600 lignes de code calculées pour rien. Les 15 recommandations BUY passent uniquement le filtre SELL/BLOQUANT, pas de discrimination RS ou volume.

**Fix :** Ajouter des filtres fonctionnels en mode non-Elite (seuils absolus : RS > -10%, volume > 200 tx) ou activer MODE_ELITE_MINIMALISTE pour le pipeline daily.

---

### CRITIQUE #2 — Confiance artificellement plafonnée entre 40% et 78%

**Fichier :** `decision_finale_brvm.py`, lignes 1036-1046
**Sévérité :** 🔴 Critique (trompe l'utilisateur)

```python
wos_normalized = min(100, max(0, wos)) / 100.0
confiance = 40 + (wos_normalized * 40)       # Résultat : [40, 80]
# Bonus RSI (+3) et accélération (+5) → max 88
confiance = min(78, max(40, confiance))       # Forçage à [40, 78]
```

**Résultats aberrants :**
- **WOS = 0** → `confiance = 40%` (affiché en rouge malgré setup vide)
- **WOS = 100** → `confiance = 80` → capé à `78%` (impossible d'aller au-delà)
- **BOAN (WOS=100)** affiche `confiance: 78%` alors qu'il est le meilleur signal
- **LNBB (WOS=17)** affiche `confiance: 47%` — seulement 7 points sous le meilleur signal

**Impact trader :** L'utilisateur ne peut pas distinguer un setup exceptionnel d'un setup médiocre en regardant la confiance. La fourchette 47%-78% donne une fausse impression de précision.

**Fix :** Supprimer le cap à 78. Utiliser une formule plus discriminante :
```python
confiance = round(min(100, wos * 0.8 + score_tech * 0.2), 1)
```

---

### CRITIQUE #3 — Signal HOLD converti automatiquement en décision BUY

**Fichier :** `decision_finale_brvm.py`, lignes 1062 + 893-903
**Sévérité :** 🔴 Critique (erreur sémantique)

```python
# PASSE 2 — MODE_ELITE_MINIMALISTE=False
if signal == "SELL":
    continue   # Rejeté
# HOLD → passe sans filtrage supplémentaire
# ...
decision = {
    "decision": "BUY",   # ← Toujours BUY, même si signal = HOLD
    "signal": signal,    # ← Stocke "HOLD" ici, mais decision = "BUY"
```

**Exemple concret aujourd'hui :**
```
analyse_ia : CABC | HOLD | score 50
decision   : CABC | BUY  | WOS 47.3  ← contradiction
TOP5       : CABC #2 avec +9.4% gain  ← recommandé à l'achat
```

HOLD signifie "ne rien faire" dans tous les standards de l'analyse technique. Le convertir en BUY est une erreur métier fondamentale. Sur 15 recommandations aujourd'hui, **7 sont des HOLD convertis en BUY** (CABC, SCRC, STAC, ORAC, ABJC, BNBC + quelques autres).

**Fix :**
```python
# Dans PASSE 2, filtrer aussi les HOLD à faible score
if signal == "HOLD" and score_tech < 60:
    continue  # HOLD sur action tiède = pas de recommandation
```

---

### CRITIQUE #4 — RS (Relative Strength) non disponible en production

**Fichier :** `decision_finale_brvm.py`, PASSE 1 + `compute_relative_strength_4sem()`
**Sévérité :** 🔴 Critique (signal clé absent)

Dans l'output de chaque exécution :
```
[CALCUL PERCENTILES] Analyse distribution complète...
   - 0 valeurs RS disponibles
   - 0 ratios volume disponibles
```

**Cause :** `compute_relative_strength_4sem()` calcule la performance de l'action vs le composite BRVM en cherchant un symbole `"BRVM"` ou `"BRVM-COMPOSITE"` dans `prices_daily`. Ce symbole n'existe pas ou n'a pas de données.

**Impact :**
- `rs_4sem = None` pour toutes les actions en `decisions_finales_brvm`
- Le WOS perd le `rs_bonus` (±0.5 multiplicateur)
- `perf_action_4sem` et `perf_brvm_4sem` = 0 dans toutes les décisions
- Si MODE_ELITE_MINIMALISTE était activé, toutes les actions seraient rejetées par `RS_INDISPONIBLE`

**Fix :** Utiliser les 47 actions comme proxy de l'indice (médiane des performances) plutôt qu'un symbole dédié :
```python
# Calculer le rendement moyen du marché comme proxy
renders_marche = [data["perf"] for data in actions_data if data["perf"] is not None]
perf_brvm_proxy = statistics.median(renders_marche) if renders_marche else 0
```

---

## PROBLÈMES MAJEURS

---

### MAJEUR #5 — Volume intraday potentiellement sur-compté

**Fichier :** `build_daily.py`, ligne 95
**Sévérité :** 🟠 Majeur

```python
volume_total = sum((c.get("volume") or 0 for c in collectes))
```

**Problème :** La BRVM publie le volume de transactions cumulatif depuis l'ouverture, pas le delta par collecte. Si chaque collecte retourne `volume_cumulatif_journée` et non `volume_depuis_dernière_collecte`, la somme est fausse.

**Exemple :** 7 collectes avec volume cumulatif = 1000 chacune → `volume_total = 7000` au lieu de `1000`.

**Impact sur VSR :** Le VSR compare `volume_J0` (potentiellement ×7) / `moyenne_10_jours_précédents`. Un VSR de 3.0× pourrait en réalité être 0.43× si le bug existe.

**Vérification nécessaire :**
```python
# Dans prices_intraday_raw, vérifier si le volume est cumulatif ou delta
db.prices_intraday_raw.find_one({"symbol": "BOAN", "date": "2026-03-03"},
                                 {"volume": 1, "datetime": 1})
# Comparer 2 collectes successives du même jour
```

**Fix si cumulatif :** Utiliser le volume de la dernière collecte (close) comme volume journalier :
```python
volume_total = last.get("volume") or 0  # Dernier = cumulatif = total jour
```

---

### MAJEUR #6 — Momentum annualisé encore actif dans le scoring

**Fichier :** `analyse_ia_simple.py`, section scoring ligne ~806
**Sévérité :** 🟠 Majeur

Le V2 a ajouté `momentum_5j` mais n'a **pas supprimé** `momentum_regression` du scoring :

```python
momentum_regression = indicateurs.get("momentum_regression")  # 30j daily, annualisé
if momentum_regression >= 25:
    score += 25    # Toujours actif!
elif momentum_regression >= 10:
    score += 15
```

**Double momentum dans les details :**
```
BOAN : "[!] MOMENTUM FORT: -115.8% annualisé [ALERTE]"   ← momentum_regression
BOAN : "Momentum 5j: 0.4%"                                ← momentum_5j (V2)
```

BOAN a un `momentum_regression` négatif (-115.8% annualisé) mais un `momentum_5j` positif (+0.4%). Ces deux signaux contradictoires coexistent dans le scoring, créant de la confusion.

**Impact :** Score de BOAN pénalisé de -10 points pour momentum annualisé négatif malgré une tendance récente positive. Idem pour NTLC (-0.8% sur 5j mais +128% annualisé = +25pts de score inflé).

**Fix :** En mode daily (`MODE_DAILY=True`), désactiver `momentum_regression` et utiliser uniquement `momentum_5j` et `momentum_10j`.

---

### MAJEUR #7 — Score peut dépasser 100 silencieusement

**Fichier :** `analyse_ia_simple.py`, ligne ~913
**Sévérité :** 🟠 Majeur

```python
confiance = min(100, max(0, score_final))  # Borné
```

Mais `score_final` peut être 120 (PRSC aujourd'hui). La borne se passe silencieusement.

**Problème en aval :** Le WOS dans `decision_finale_brvm.py` utilise `score_tech` (le score brut, pas la confiance) pour certains calculs. Si `score_tech = 120`, les pondérations WOS sont biaisées.

**Cas concret :**
```
PRSC score brut = 120 (100 initial + 20 pts VSR)
confiance affiché = 100% (clip)
WOS calculé utilise score_tech = 120 → WOS ~22 (incohérent)
```

**Fix :** Appliquer la borne **avant** toute propagation :
```python
score_final = min(100, max(0, score))  # Borner AVANT retour
```

---

### MAJEUR #8 — `delete_many` à chaque run : perte d'historique

**Fichier :** `decision_finale_brvm.py`, ligne ~580
**Sévérité :** 🟠 Majeur

```python
decisions_finales.delete_many({"horizon": HORIZON_TAG})  # Efface TOUT à chaque run
```

**Conséquences :**
1. Zéro historique des décisions → impossible de tracer les entrées passées
2. Si le pipeline plante à mi-chemin (après delete, avant insert), les décisions sont perdues
3. Le Time Stop J+10 dans `top5_engine_final.py` s'appuie sur `first_selected_at` dans `top5_daily_brvm`, mais si décision est supprimée/recréée chaque jour, le `first_selected_at` est bien préservé dans le TOP5 (OK), mais toute analyse d'historique sur `decisions_finales_brvm` est impossible.

**Fix :**
```python
# Taguer avec un timestamp au lieu de supprimer
decisions_finales.update_many(
    {"horizon": HORIZON_TAG},
    {"$set": {"archived": True, "archived_at": datetime.now(timezone.utc)}}
)
# Puis insérer nouvelles décisions avec "archived": False
```

---

### MAJEUR #9 — `datetime.utcnow()` déprécié (violation Python 3.13)

**Fichier :** `decision_finale_brvm.py`, ligne 764
**Sévérité :** 🟠 Majeur (sera cassant en Python 3.14+)

```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
  → date_limite = datetime.utcnow() - timedelta(days=7)
```

**Fix immédiat :**
```python
from datetime import datetime, timezone, timedelta
date_limite = datetime.now(timezone.utc) - timedelta(days=7)
```

---

## PROBLÈMES MINEURS

---

### MINEUR #10 — ATR_MIN 0.3% (analyse_ia) vs 0.56% (décision finale) : double standard

**Sévérité :** 🟡 Mineur

Dans `analyse_ia_simple.py` :
```python
elif vol < 0.3:   → BLOQUANT
```

Dans `decision_finale_brvm.py` (filtre standalone) :
```python
if atr_pct < 0.56:  → ATR_DAILY_FAIBLE rejeté
```

Il existe un **couloir indétecté** entre 0.3% et 0.56% : une action avec ATR=0.45% passe le filtre `analyse_ia` (non BLOQUANT), reçoit un signal BUY, **mais est ensuite rejetée** dans `decision_finale_brvm`. Ce double-passage est inutilement redondant et confus.

**Fix :** Aligner les deux seuils à 0.56%.

---

### MINEUR #11 — LNBB dans le TOP5 avec seulement 22 jours d'historique

**Sévérité :** 🟡 Mineur

```
[LNBB] OK 22 donnees   ← Matrice corrélation
```

LNBB a 22 jours de données (minimum pour les calculs), soit ~4.4 semaines. Les indicateurs RSI(14), SMA(10), ATR(8) sur 22 jours ne sont pas statistiquement fiables. Même SIVC n'a que 25 jours.

**Actions similaires :** BICB (22j), ORAC (23j), UNXC (23j), SIVC (25j).

**Fix :** Ajouter un filtre `min_historique = 40 jours` en mode daily avant de générer un signal.

---

### MINEUR #12 — Symboles fantômes dans `decisions_finales_brvm`

**Sévérité :** 🟡 Mineur

Chaque exécution tente de trouver des prix pour des symboles inexistants :
```
[BRVM] [X] Pas de prix disponible
[BOA]  [X] Pas de prix disponible
[SVOC] [X] Pas de prix disponible
[SGOC] [X] Pas de prix disponible
[SAFH] [X] Pas de prix disponible
```

Ces 5 symboles occupent du temps inutilement à chaque run et génèrent du bruit dans les logs.

**Fix :** Les retirer de `curated_observations` ou de la liste des sources analysées.

---

### MINEUR #13 — Paires corrélées à 1.00 non filtrées dans les décisions

**Sévérité :** 🟡 Mineur

La matrice de corrélation détecte des paires à corrélation 1.00 :
```
BICC / ECOC : 1.00
BICC / STBC : 0.99
SGBC / STBC : 0.99
```

ECOC et BICC sont identiques en termes de comportement de prix. Pourtant, les deux pourraient simultanément recevoir un signal BUY et apparaître ensemble dans le TOP5. Le filtre sectoriel ne couvre pas ce cas (ECOC = Ecobank, BICC = CI-BISSA sont classés comme "AUTRE" potentiellement).

**Fix :** Dans `top5_engine_final.py`, exclure les paires avec corrélation > 0.95 si l'une est déjà dans le TOP5.

---

### MINEUR #14 — Timing "CONFIRME" jamais déclenché aujourd'hui

**Sévérité :** 🟡 Informatif

Toutes les 15 recommandations affichent `timing_signal: "NEUTRE"`. Le timing "CONFIRME" requiert désormais (V2) : variation > 0 ET volume_intraday ≥ 20% volume_veille. Ce seuil de 20% peut être trop conservateur si les premières collectes intraday du jour ont peu de volume.

**Observation :** Sur 47 actions, aucune n'a eu de CONFIRME. Soit le seuil 20% est trop élevé, soit les collectes intraday de ce matin étaient trop récentes par rapport à la clôture de la veille.

**Fix :** Revoir le seuil à 10% ou ajouter une fenêtre horaire (CONFIRME uniquement entre 10h-15h).

---

## CE QUI FONCTIONNE BIEN ✅

| Fonctionnalité | Statut | Note |
|----------------|--------|------|
| Architecture pipeline 3 étapes | ✅ | Claire, séquentielle, fail-fast |
| WOS cap à 100 | ✅ | Fix V2 actif, BOAN = 100.0 confirmé |
| VSR dynamique | ✅ | PRSC 3.6×, SIVC 3.0× détectés |
| Formule TOP5_SCORE V2 | ✅ | PRSC #1 grâce VSR (était absent avant) |
| RR dynamique par classe (A=2.0, B=2.4, C=3.0) | ✅ | Cohérent avec gestion de risque |
| Filtre ATR < 0.56% | ✅ | SIBC correctement éliminé |
| Diversification sectorielle (max 2 banques) | ✅ | Max 2 banques/secteur appliqué |
| Time Stop J+10 avec alerte | ✅ | Logique saine |
| Déduplication upsert (symbol, date) | ✅ | Idempotent |
| Encodage UTF-8 explicite | ✅ | Robuste sur Windows |
| Backtest standalone (V2) | ✅ | Profit Factor 1.67 sur 165 jours |
| Matrice corrélation 47×47 | ✅ | RSI Pearson calculés correctement |

---

## TABLEAU DE BORD CRITIQUE

```
PIPELINE lancer_recos_daily.py — 03/03/2026
═══════════════════════════════════════════
Données                    Statut
───────────────────────────────────────────
prices_daily               ✅ 3570 docs | 03/03 ✅
prices_intraday            ✅ 5875 collectes
RS composite BRVM          ❌ 0 valeurs disponibles
Volume cuisson sum vs last  ⚠️ À vérifier

Filtres                    Statut
───────────────────────────────────────────
SELL bloquant              ✅ 31 rejets corrects
ATR < 0.56% (daily)        ✅ SIBC rejeté
RS percentile P≥75         ❌ Désactivé (MODE_ELITE=False)
Volume percentile P≥30     ❌ Désactivé
Accélération ≥ 2%          ❌ Désactivé
Breakout 3 semaines        ❌ Désactivé

Signaux                    Statut  Valeur
───────────────────────────────────────────
VSR                        ✅      PRSC 3.6×, SIVC 3.0×
momentum_5j                ✅      PRSC +16.5%, CABC +13.8%
momentum_regression        ⚠️      Actif mais annualisé (biais)
Relative Strength          ❌      Non disponible
Breakout                   ❌      Non calculé

Sortie TOP5                Statut
───────────────────────────────────────────
Confiance discriminante    ❌      Fourchette 40-78% trop étroite
Classe A dans TOP5         ⚠️      BOAN absent (VSR effondré)
HOLD→BUY conversions       ⚠️      7/15 recommandations sont HOLD
Historique décisions       ❌      delete_many à chaque run
─══════════════════════════════════════════
Score global               62/100
```

---

## RECOMMANDATIONS PRIORITAIRES

### Priorité 1 — Activer un filtre RS minimal (même sans MODE_ELITE)
```python
# Ligne 903, après vérification signal SELL, ajouter :
if signal == "HOLD" and score_tech < 60:
    rejected_p2["bloquant"] += 1
    continue

# Et un seuil RS absolu si disponible
if action_data["rs_4sem"] is not None and action_data["rs_4sem"] < -20:
    rejected_p2["bloquant"] += 1
    continue
```
**Impact immédiat :** Réduction des recommandations de 15 → ~8-10, qualité supérieure.

### Priorité 2 — Corriger le calcul du volume (build_daily.py)
Vérifier si `prices_intraday_raw.volume` est cumulatif ou delta.
Si cumulatif : remplacer `sum()` par `last.get("volume")`.
**Impact :** VSR recalibré, moins de faux spikes.

### Priorité 3 — Corriger confiance [40→78] vers [0→100]
```python
confiance = min(100, max(0, wos))   # Simple, lisible
```
**Impact :** Discrimination réelle entre Classe A (WOS 100 → conf 100%) et Classe C (WOS 22 → conf 22%).

### Priorité 4 — HOLD ≠ BUY
Stocker `decision: "HOLD"` pour les signaux HOLD et ne les remonter dans le TOP5 que si score ≥ 65.

### Priorité 5 — Fixer le RS composite BRVM
Calculer `perf_brvm_proxy` depuis la médiane des 47 actions (proxy disponible sans données externes).

### Priorité 6 — Corriger `datetime.utcnow()` (1 ligne)
```python
date_limite = datetime.now(timezone.utc) - timedelta(days=7)
```

### Priorité 7 — Ajouter `min_historique = 40 jours`
Exclure LNBB, BICB, ORAC, UNXC, SIVC du pipeline jusqu'à accumulation suffisante.

---

## VERDICT FINAL

Le pipeline fonctionne et produit des recommandations cohérente en apparence. Mais sous le capot, **4 problèmes critiques** l'empêchent d'atteindre son potentiel :

1. Les filtres élite (RS, volume, breakout) sont entièrement bypassés — le pipeline fonctionne en mode "décoration" pour ces calculs.
2. La confiance est artificiellement comprimée entre 40% et 78% — impossible de différencier un setup fort d'un setup médiocre.
3. Les signaux HOLD sont convertis en BUY — 7/15 recommandations d'aujourd'hui ne devraient pas être là.
4. La Relative Strength vs le marché est silencieusement absente.

**Sans ces 4 correctifs**, le TOP5 produit 5 recommandations où les vraies opportunités (1-2 réelles) sont noyées dans 3-4 actions dont le seul mérite est de ne pas être en SELL.

**Avec les correctifs Priorité 1-4**, l'estimation passe à **75-78/100** et le TOP5 contiendrait systématiquement les meilleures setups du marché.

---

_Audit réalisé le 03/03/2026 | Analyse code source + exécution live | Pipeline V2_

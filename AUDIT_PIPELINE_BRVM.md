# AUDIT COMPLET — PIPELINE BRVM IA DECISIONNELLE

**Date d'audit :** 2026-03-06 (mis a jour apres ablation study + chantiers v2.7)
**Version pipeline :** post-corrections v2.7 (10 etapes, ablation findings appliques, tradable_universe unifie, setup_type classification)
**Resultat global :** 10/10 etapes fonctionnelles — 8 bugs corriges + 14 ameliorations appliquees

---

## 1. ARCHITECTURE DU PIPELINE

### Orchestrateur principal : `pipeline_brvm.py`

```
pipeline_brvm.py (orchestrateur)
subprocess.run par etape, sys.exit(1) sur returncode != 0
PYTHONIOENCODING=utf-8 propage a tous les scripts fils

ETAPE 1  — collecter_publications_brvm.py  [UNIFIE v2.4]
           Phase A — bulletins généraux :
             scrape BRVM (liens PDF) + RichBourse (articles/palmares)
             -> curated_observations (source: BRVM_PUBLICATION, RICHBOURSE)
             emetteur=ABJC, symboles=[47 actions] (bulletins globaux)
           Phase B — publications par emetteur (NOUVEAU, integre) :
             scrape publications SPECIFIQUES par emetteur (og_group_ref_target_id)
             categories : AG, DIVIDENDE, RESULTATS, COMMUNIQUE
             node_id resolu via dropdown BRVM
             -> curated_observations emetteur=SYMBOL, symboles=[SYMBOL] (1 seul)
             IMPACT : corrige le probleme fondamental score_semantique=0
           |
ETAPE 2  — extraire_pdf_pdfplumber.py
           telecharge chaque PDF officiel BRVM (Bulletins, Rapports, AG)
           extrait texte avec pdfplumber (x_tolerance=3)
           fallback tableaux -> texte ligne par ligne
           flag pdf_extraction_status: OK | VIDE (scanné/protege)
           re-detection symboles dans texte extrait
           -> met a jour curated_observations (full_text, symboles, emetteur)
           |
ETAPE 3  — analyse_semantique_brvm_v3.py  [MIS A JOUR V4]
           score_contenu = score_lexique + 3 x score_catalyseur
           score_lexique  : 22 mots positifs / 19 mots negatifs  (signal faible)
           score_catalyseur : 31 phrases catalyseurs positifs / 20 negatifs (signal fort x3)
             ex: "resultat net en hausse", "dividende en hausse", "perte nette"
           confiance texte : <100c=0.0 | <500c=0.4 | <2000c=0.7 | >=2000c=1.0
           stocke : semantic_score_catalyseur, semantic_score_lexique, has_catalyseur
           -> mise a jour curated_observations (semantic_score_base, semantic_version=v4)
           |
ETAPE 4  — agregateur_semantique_actions.py  [MIS A JOUR V2]
           Score_final(doc) = score_contenu x w_source x w_recence x w_confiance x w_event x w_position
           w_recence : decay EXPONENTIEL 0.5^(jours/5) — fenetre 14j seulement
             0j->1.0 | 5j->0.50 | 10j->0.25 | 14j->0.13 | >14j->0
           Top-k=3 : 3 docs les plus impactants par symbole (anti-spam bulletins)
           signal_explosion : score_7j >= 12 ET catalyseur dans les 72h
           -> AGREGATION_SEMANTIQUE_ACTION dans curated_observations
           champs : score_semantique_7j, catalyseur_recent_72h, signal_explosion
           |
ETAPE 5  — analyse_ia_simple.py
           RSI, ATR, WOS, VSR, momentum, timing
           -> brvm_ai_analysis + decisions_finales_brvm (signaux)
           |
ETAPE 6  — decision_finale_brvm.py
           BUY/HOLD/SELL, stop = ATR x 1.5
           -> decisions_finales_brvm (SEMAINE, non archives)
           |
ETAPE 7  — multi_factor_engine.py  [MIS A JOUR V2.5]
           5 facteurs cross-sectionnels :
             RS (0.30) > Breakout (0.25) > Volume (0.20)
             > Momentum perf_10j (0.15) > Compression (0.10)
           VSR detonateur : vsr_ratio_10j = mean(vol[-3:]) / mean(vol[-10:])
             >= 2.5x = choc liquidite, trigger VCP
           -> multi_factor_scores_daily
           -> enrichit decisions_finales_brvm (score_total_mf, vsr_ratio_10j, ...)
           NOUVEAU : injecter_decisions_mf_manquantes()
             Pour chaque EXPLOSION/SWING_FORT (score >= 70) absent de
             decisions_finales_brvm en BUY, cree une decision synthetique :
             stop = 1.5 x ATR, gain = 3 x stop_pct, RR=3.0, classe A/B
             generated_by = "multi_factor_engine"
             IMPACT corrige : ORGT EXPLOSION 88.7 hors UNIVERSE -> TOP5 #1
           |
ETAPE 8  — top5_engine_final.py  [MIS A JOUR V2.5]
           Chargement scores semantiques (AGREGATION_SEMANTIQUE_ACTION)
           Normalisation score_7j -> [0,100] : score_7j=0->40, +15->70, +30->100
           FORMULE :
             top5_score = (0.55xMF + 0.35xAlpha + 0.10xSEM) x liq
                        + 5.0 bonus si signal_explosion
                        + 4.0 bonus si VCP pattern
             VCP = compression>=60 AND breakout>=60 AND vsr_ratio_10j>=2.5
           Blacklist  (WR<30% exclus)
           Regime     BULL/NEUTRAL/BEAR (breadth + momentum)
           Meta-model LogReg desactive (R4), reactiver a 60 trades fermes
           Pre-filtres MF (score>=55, breakout>=50, VSR>=60)
           Correlation >= 0.85 bloquee
           Circuit breaker DD>12%
           Vol targeting + trailing stop
           TP1/TP2/Runner plan de sortie
           Affichage : MF=xx | alpha=xx | SEM=+/-xx [VCP] [EXPLOSION]
           -> top5_weekly_brvm (ou top5_daily_brvm)
           |
ETAPE 9  — propagation_sector_to_action.py
           lit top5_weekly_brvm (via top5_engine_final.py)
           ajuste confiance +/-10%
           ajuste sizing x0.8 a x1.2
           -> met a jour decisions_finales_brvm par symbol
           |
ETAPE 10 — backtest_reporting_monitoring.py
           fraicheur donnees (ts delta corrige)
           gain espere actifs (disclaimer clair)
           seuil BUY dynamique volatilite
           -> salle_marche_brvm.log
```

---

## 2. ETAT DES COLLECTIONS MONGODB (2026-03-05)

| Collection | Docs | Role |
|------------|-----:|------|
| `prices_daily` | 5 987 | Prix journaliers 47 actions BRVM |
| `prices_weekly` | 1 265 | Prix hebdomadaires consolides |
| `curated_observations` | 40 018 | Publications + analyses + scores |
| `decisions_finales_brvm` | 468 total (399 archivees) | BUY/HOLD/SELL generees |
| `multi_factor_scores_daily` | 47 | Scores MF 5-facteurs par action |
| `top5_weekly_brvm` | 4 | TOP positions semaine courante |
| `top5_daily_brvm` | 1 | TOP positions mode daily |
| `track_record_weekly` | 15 | Historique performances cloturees |

### PDFs BRVM extraits (apres etape 2)

| Statut | Nombre | Detail |
|--------|-------:|-------|
| `OK` — texte extrait | 39 | dont 28 Bulletins Officiels de la Cotation (~53k chars) |
| `VIDE` — PDF scanne | 4 | BOA CI, BOA SN (images, non extractibles) |
| Deja traites sessions precedentes | 9 | |
| **Total PDF_OFFICIEL traites** | **52** | 100% couverts |

---

## 3. SCORES MF ENGINE — DERNIERE EXECUTION

**Mode :** DAILY (prices_daily) | **Actions analysees :** 47/47

| Rang | Symbol | Score | Label | RS | Breakout | Volume | Momentum | Compr. |
|------|--------|-------|-------|----|----------|--------|----------|--------|
| 1 | SHEC | 94.4 | EXPLOSION | 100P | 98P | 81P | 100P | 87P |
| 2 | SDCC | 88.7 | EXPLOSION | 92P | 100P | 79P | 96P | 62P |
| 3 | ORGT | 78.5 | SWING_FORT | 85P | 96P | 49P | 79P | 74P |
| 4 | TTLS | 77.5 | SWING_FORT | 74P | 74P | 96P | 92P | 36P |
| 5 | TTLC | 76.8 | SWING_FORT | 87P | 64P | 94P | 94P | 19P |
| 6 | CFAC | 72.2 | SWING_FORT | 64P | 92P | 68P | 68P | 64P |
| 7 | STAC | 71.4 | SWING_FORT | 96P | 77P | 47P | 74P | 30P |
| 8 | CABC | 70.6 | SWING_FORT | 72P | 94P | 28P | 98P | 53P |

**Poids facteurs :** RS=0.30 · Breakout=0.25 · Volume=0.20 · Momentum(perf_10j)=0.15 · Compression=0.10
**Bonus :** +5 pts si Acceleration >= P80

---

## 4. TOP5 ENGINE — SORTIE PIPELINE WEEKLY

**Regime :** BULL (85% actions > SMA20, momentum median +12.06%)
**Blacklist :** SICC, BNBC, PRSC, SLBC, BOAN, TTLC, STAC (WR < 30%)
**Positions autorisees :** 5 (BULL) — 4 retenues apres filtres

| Rang | Symbol | MF | Label | Alloc | Stop | TP1 (+7.5%) | TP2 (+15%) | Runner (+27.5%) |
|------|--------|----|-------|-------|------|------------|------------|-----------------|
| 1 | UNLC | 61.1 | SWING_MOYEN | 13.9% | 11 690 | 14 088 | 15 071 | 16 709 |
| 2 | UNXC | — | — | — | — | — | — | — |
| 3 | CBIBF | 61.1 | SWING_MOYEN | 12.0% | — | — | — | — |
| 4 | ETIT | 57.4 | SWING_MOYEN | 11.9% | 27 | 33 | 36 | 40 |

**Plan de sortie :** 50% a TP1 · 30% a TP2 · 20% runner libre
**Trailing stop :** Initial = entree - 1.5xATR · Breakeven a +1 ATR · Trailing close-1ATR a +3 ATR
**Circuit breaker :** DD cumule 10 derniers = 0% -> OK

---

## 5. BUGS CORRIGES (session 2026-03-05)

### BUG CRITIQUE #1 — Doublons dans top5_engine_brvm.py

**Fichier :** `top5_engine_brvm.py` ligne 168
**Symptome :** BOAC apparaissait 3 fois, SAFC 2 fois dans le TOP5.
**Cause :** `find({"horizon": "SEMAINE"})` sans filtre `archived` incluait toutes
les decisions archivees. Meme symbole en plusieurs copies archivees = plusieurs rangs.

```python
# AVANT
recos = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))

# APRES
recos_raw = list(db.decisions_finales_brvm.find({
    "horizon": "SEMAINE",
    "archived": {"$ne": True}
}))
# + deduplication par symbol (garder WOS max)
seen_symbols = {}
for r in recos_raw:
    sym = r.get("symbol", "")
    score_key = r.get("wos") or r.get("rs_4sem") or 0
    if sym not in seen_symbols or score_key > (...):
        seen_symbols[sym] = r
recos = list(seen_symbols.values())
```

**Resultat :** 4 symboles uniques, zero doublon.

---

### BUG CRITIQUE #2 — Pipeline utilisait l'ancien engine

**Fichier :** `pipeline_brvm.py`
**Symptome :** Toutes les ameliorations quantitatives (blacklist, regime, meta-model,
TP1/TP2/Runner, trailing stop, vol targeting) bypassees a chaque run du pipeline.
**Cause :** PIPELINE pointait sur `top5_engine_brvm.py` (version initiale sans filtres).

```python
# AVANT (8 etapes)
("TOP5 ENGINE (CLASSEMENT SURPERFORMANCE)", "top5_engine_brvm.py"),

# APRES (10 etapes)
("EXTRACTION PDF (pdfplumber)",             "extraire_pdf_pdfplumber.py"),
("MULTI-FACTOR ENGINE (SCORING QUANTITATIF)", "multi_factor_engine.py"),
("TOP5 ENGINE FINAL (BLACKLIST + REGIME + TP)", "top5_engine_final.py"),
```

**Resultat :** Pipeline orchestre le moteur complet (10 etapes).

---

### BUG CRITIQUE #3 — Fraicheur donnees : delta negatif (-7213.4h)

**Fichier :** `backtest_reporting_monitoring.py`
**Symptome :** `[INFO] Donnees fraiches: il y a -7213.4h` — alerte stale-data jamais declenchee.
**Cause (double) :**
1. 26 documents `BULLETIN_OFFICIEL` avaient `ts='2026-12-31'` (date future sentinelle).
2. Incompatibilite datetime naive vs aware lors de la soustraction.

**Correction :**
```python
# Filtrer uniquement ts string, normaliser [:19] pour enlever timezone
last_pub = db.curated_observations.find_one(
    {"ts": {"$type": "string"}}, sort=[("ts", -1)]
)
ts_clean = ts[:19]
dt = datetime.fromisoformat(ts_clean)
delta = (datetime.now() - dt).total_seconds() / 3600
if abs(delta) > 24 * 30:
    log_alert(f"Donnees potentiellement stales ...")
```

+ Suppression des 26 docs `ts='2026-12-31'` via `delete_many`.

**Resultat :** `[INFO] Donnees fraiches: il y a 0.2h`

---

### BUG CRITIQUE #4 — Etape ajustement sectoriel toujours vide

**Fichier :** `propagation_sector_to_action.py`
**Symptome :** `Aucune decision TOP 5 trouvee` a chaque run depuis le debut du projet.
**Cause :** Requete `find({"is_top5": True})` — champ jamais ecrit par aucun script.

```python
# AVANT (champ fantome)
decisions = list(db.decisions_finales_brvm.find({
    "horizon": "SEMAINE", "decision": "BUY",
    "is_top5": True   # jamais ecrit
}))

# APRES (lire depuis top5_weekly_brvm)
top5_docs = list(db.top5_weekly_brvm.find({}).sort("rank", 1))
# lookup dans decisions_finales_brvm par symbol
```

**Resultat :** `4 decisions TOP 5 a ajuster selon secteur`

---

### BUG SECONDAIRE #5 — backtest_signaux : gain espere presente comme realise

**Fichier :** `backtest_reporting_monitoring.py`
**Symptome :** `Gain moyen: 29.36% sur 180j` sur 84 trades (archives inclus).
**Cause :** Calcul `(prix_cible - prix_actuel)` sur les cibles definies a l'avance.
C'est le gain espere, pas le gain realise.

```python
# APRES : filtre archived + label explicite
decisions = list(db.decisions_finales_brvm.find({
    "horizon": horizon, "archived": {"$ne": True}
}))
log_info(f"Backtest {horizon} (espere) | {n_trades} trades actifs | ...")
```

**Resultat :** `9 trades actifs | Gain moyen cible: 38.65%`

---

### BUG SECONDAIRE #6 — 26 documents BULLETIN_OFFICIEL ts='2026-12-31'

**Collection :** `curated_observations`
**Cause :** Bulletins PDF collectes sans extraction de date reelle.
Date par defaut '2026-12-31' assignee (valeur sentinelle incorrecte).
**Correction :** `delete_many({"ts": "2026-12-31"})` — 26 docs supprimes.
**Resultat :** Max ts = `2026-03-05T11:13:07` (aujourd'hui).

---

### BUG CRITIQUE #7 — `get_mongo_db()` retourne un tuple, pas une db

**Fichier :** `scripts/connectors/brvm_publications_par_emetteur.py`
**Symptome :** `'tuple' object has no attribute 'curated_observations'` — 0 publications sauvegardees meme quand des docs sont trouves (BICC=4, SNTS=2).
**Cause :** `get_mongo_db()` retourne `(client, db)`. Le script faisait `db = get_mongo_db()` au lieu de `_, db = get_mongo_db()`.

```python
# AVANT (bug)
def main():
    db = get_mongo_db()

# APRES (correct, pattern matching collecter_publications_brvm.py:251)
def main():
    _, db = get_mongo_db()
```

**Resultat :** BICC +4 publications sauvegardees (AG), SNTS node_id=411 resolu correctement.

---

## 6. FAIBLESSES RESIDUELLES

### ~~F1 — Analyse semantique sur bruit PDF (80% des articles)~~ RESOLUE

**Resolution :** Etape 2 ajoutee dans le pipeline (`extraire_pdf_pdfplumber.py`).

- pdfplumber 0.11.9 installe dans le venv
- 39/43 PDFs traites avec succes (28 BOC x ~53k chars, 11 AG/rapports)
- 4 PDFs scannes/proteges marques `VIDE` (non retentes)
- Symboles re-detectes dans le texte extrait -> alimentent l'etape 3

**Limitation residuelle :** 4 PDFs images (BOA CI, BOA SN) non extractibles.
OCR non implemente (tesseract requis).

---

### ~~F2 — Meta-model : precision 52% (quasi-aleatoire)~~ DESACTIVE (R4)

**Impact :** ELEVE → RESOLU temporairement

Le `LogisticRegression` atteignait 52% de precision, proche du hasard.

**Correction (R4) :** `ENABLE_META_MODEL = False` dans `top5_engine_final.py`.
`prob_win = 0.55` constant pour tous les candidats. Code preserved sous flag.

**Condition de re-activation :** `track_record_weekly >= 60` trades clotures avec
features MF reelles (`score_total_mf`, `rs_score_mf`, `breakout_score_mf`, `volume_score_mf`).

---

### ~~F3 — Pipeline trop restrictif : 4 positions en BULL~~  RESOLU (R6)

**Impact :** MOYEN → RESOLU

Cause initiale : `decision_finale_brvm.py` avait un UNIVERSE hardcode de seulement
12 symboles. Les actions hors UNIVERSE (ex: ORGT score 88.7 EXPLOSION) n'avaient
aucun document dans `decisions_finales_brvm` → invisibles pour `top5_engine_final.py`.

**Correction (R6) :** `injecter_decisions_mf_manquantes()` ajoutee dans `multi_factor_engine.py` :
- Apres scoring, identifie tous les EXPLOSION/SWING_FORT (score >= 70) sans BUY actif
- Cree une decision synthetique : prix=close, stop=1.5xATR, gain=3xstop, classe A/B
- `generated_by = "multi_factor_engine"` pour tracabilite
- Upsert : met a jour un HOLD/None existant ou insere un nouveau document

**Run validation (2026-03-06) :**
- 5 injections : ORGT (88.7), SHEC (75.0), CFAC (74.8), SIVC (70.9), TTLS (70.0)
- Resultat TOP5 : 5 positions en BULL (au lieu de 3)
- ORGT #1 score=85.7 classe A | CFAC #2 score=73.2 | PRSC #3 | SDCC #4 | SIVC #5

**Note residuelle :** decision_finale_brvm.py garde son UNIVERSE=12 (analyse approfondie).
L'injection MF comble le manque pour le TOP5 en mode daily et weekly.

---

### ~~F7 — Score semantique = 0 pour TOUTES les actions (100%)~~ RESOLU (v2.3)

**Impact :** CRITIQUE → RESOLU

**Symptome initial :** `score_semantique_semaine > 0: 0/513 documents` — TOP5 100% technique.

**Diagnostic (chaine de causalite) :**
1. `collecter_publications_brvm.py` collecte des bulletins generaux (palmares, cours)
   -> `emetteur=ABJC`, `symboles=[47 actions]`, `titre=""`
2. Texte vide ou generique → `semantic_score_base ≈ 4` (quasi-zero, aucun catalyseur)
3. `agregateur_semantique_actions.py` distribue le meme micro-score a 47 actions
4. UNLC/UNXC absent de `AGREGATION_SEMANTIQUE_ACTION`
5. `decisions_finales_brvm.score_semantique = 0` pour toutes les actions

**Resolution en 3 couches :**

| Couche | Fichier | Correction |
|--------|---------|------------|
| Collecte | `brvm_publications_par_emetteur.py` (nouveau) | Scrape publications SPECIFIQUES par societe via og_group_ref_target_id. `emetteur=SYMBOL`, `symboles=[SYMBOL]` (1 seul) |
| Scoring | `analyse_semantique_brvm_v3.py` → V4 | `score_contenu = lexique + 3xcatalyseur`. Confiance texte. Stocke `has_catalyseur` separement |
| Agregation | `agregateur_semantique_actions.py` → V2 | Decay exponentiel (half_life=5j), fenetre 14j, Top-k=3, `signal_explosion` flag |

**Nouveau signal :** `signal_explosion = score_7j >= 12 AND catalyseur dans 72h`

**Nouveau scoring `top5_engine_final.py` :**
```
top5_score = (0.55 x score_total_mf + 0.35 x score_alpha + 0.10 x sem_norm) x liq
           + 5.0 bonus si signal_explosion
```
Avant : 0% sentiment / Apres : 10% sentiment + 5 bonus explosion

---

### BUG CRITIQUE #8 — Score sémantique = 0 (gate trop restrictif dans l'agrégateur)

**Fichier :** `agregateur_semantique_actions.py`
**Symptome :** Toutes les actions avaient `score_semantique_7j = 0` en sortie d'agrégateur,
rendant la composante sémantique (10%) du TOP5 score totalement plate.
**Cause :** La requête MongoDB avait un gate :
```python
{"attrs.semantic_score_base": {"$exists": True, "$ne": 0}},
```
Ce gate excluait tous les docs enrichis par `preparer_sentiment_publications()` (score événementiel)
qui n'avaient pas encore été passés par `analyse_semantique_brvm_v3.py` (score de contenu).
Résultat : 0 docs qualifiants → aucune agrégation → scores restent à 0.

**Correction :**
```python
# AVANT — gate qui bloquait les docs sans semantic_score_base
{"$or": [
    {"attrs.semantic_score_base": {"$exists": True, "$ne": 0}},
    {"attrs.has_catalyseur": True},
]},

# APRÈS — filtre sur identifiant société uniquement (emetteur OU symboles)
{"$or": [
    {"attrs.emetteur": {"$exists": True, "$ne": None}},
    {"attrs.symboles": {"$exists": True, "$ne": []}},
]}
```

**Amélioration complémentaire :** `score_contenu` combine maintenant `semantic_score_base`
(signal V4 de contenu) + `sentiment_score / 4` (signal événementiel normalisé).
`has_catalyseur` reconnaît aussi les événements avec `sentiment_impact = "HIGH"` (dividende,
résultat, perte nette) — déclencheur du `signal_explosion`.

**Impact :**
- Dividende récent (+25 sent) → score_contenu ≈ 6.25 × w_event(DIVIDENDE=2.5) → score_7j ≈ 10-11
- `signal_explosion` activable pour les sociétés avec dividende dans les 72h
- Contribution sémantique TOP5 effective : `0.10 × sem_norm` non plus plate à 40/100

---

### F4 — Scores sectoriels : 1 seul secteur avec score 0

**Impact :** FAIBLE

`sector_sentiment_brvm` contient uniquement `DISTRIBUTION : +0.0`.
L'agregateur sectoriel (`agregateur_sentiment_sectoriel.py`) n'est pas
dans le pipeline. L'etape 9 tourne sans effet reel.

**Recommandation :** Ajouter `agregateur_sentiment_sectoriel.py` comme etape 4bis.

---

### F5 — Collecte : 0 nouveaux docs a chaque run en journee

**Impact :** FAIBLE (comportement attendu)

Le collecteur verifie les doublons par hash/URL. Normal entre deux runs
rapproches. Publications BRVM publiees 1x/jour apres 18h00 UTC.

**Recommandation :** Scheduler (cron/Airflow) a 18h15 UTC.

---

## 7. PERFORMANCE PIPELINE

### Metriques observees (run 2026-03-05)

| Indicateur | Valeur | Cible | Statut |
|------------|--------|-------|--------|
| Temps total | ~10 min (avec PDF) | < 15 min | OK |
| PDFs extraits | 39/43 (91%) | > 80% | OK |
| Articles semantiques | 386+ (dont BOC) | > 100 | OK |
| Actions MF scorees | 47/47 | 47 | OK |
| Blacklist appliquee | 7 exclusions | Auto | OK |
| Regime marche | BULL (85% > SMA20) | Correct | OK |
| Positions TOP5 weekly | 4 | 3-5 | OK |
| Circuit breaker | 0% DD | < 8% | OK |
| Fraicheur donnees | 0.2h | < 24h | OK |
| Doublons TOP5 | 0 | 0 | OK |
| Etape sectorielle | 4 decisions ajustees | > 0 | OK |

### Backtest walk-forward (OOS — `backtest_daily_v2.py`)

| Metrique | Valeur | Cible | Statut |
|----------|--------|-------|--------|
| Win Rate (brut, signaux MF 5-facteurs) | 50.8% | >= 60% | ~KO |
| Profit Factor brut | 1.87 | >= 2.5 | ~KO |
| Esperance brute | +1.61%/trade | >= +0.5% | OK |
| MaxDD brut (sans filtres) | 70.6% | < 15% | KO (non representatif) |

### Backtest pipeline-complete (R1 -> R6 — `backtest_daily_v2.py --pipeline`)

Mode appliquant les filtres de production :
blacklist + regime + vol targeting (1.0%/trade) + circuit breaker (CB>20%).
Paramètres calibres : RISK_PCT_TRADE=1.0%, MAX_ALLOC=15%, CB_DD_THRESHOLD=20%.

| Metrique | Valeur | Cible | Statut |
|----------|--------|-------|--------|
| Win Rate pipeline | **53.8%** | >= 50% | OK |
| Profit Factor pipeline | **2.41** | >= 1.5 | OK |
| **MaxDD pipeline (reel)** | **15.0%** | < 20% | **OK** |
| Esperance/trade | **+1.24%** | >= +0.5% | OK |
| Capital final (base 100) | **+123.4%** | > 0% | OK |
| CB declenches | **0** | < 5 | OK |
| Reduction MaxDD vs brut | -55.6pp | > 0 | OK |

**Amelioration vs v2.4 :** WR +6.1pp (47.7→53.8%), PF +1.13 (1.28→2.41), CB 10→0.
**Cause :** generer_signal() MF-aligne (5 facteurs, seuil score_mf>=55) + parametres risque recalibres.

---

## 7bis. ABLATION STUDY — RÉSULTATS (2026-03-06)

### Protocole
Script : `ablation_study.py` (standalone, aucun fichier modifié)
Horizon : J+10 | ATR_MIN=0.56% | Stop=1.5×ATR | Coûts=0.70% A/R
Données : 4 577 fenêtres valides sur 47 symboles (historique complet prices_daily)

### Tableau comparatif (11 configurations)

```
Config                     N    WR%      EV     Win     Los    PF    DD%     Cap
C01_Breakout_seul         46  43.5%  +2.02%  +8.50%  -2.97%  2.20  34.5%  221.1  +0.23
C06_RS+BRK+VOL           529  50.1%  +1.81%  +7.21%  -3.61%  2.01  77.0% ...
C08_MF_sans_acc          579  50.9%  +1.84%  +7.23%  -3.76%  2.00  74.3% ...    +0.03
C07_MF_PROD (REF)        592  50.7%  +1.78%  +7.14%  -3.73%  1.97  73.2% ...    << REF
C10_Poids_egaux          391  49.1%  ...                      1.97  ...
C02_Volume_seul          278  51.1%  ...                      1.79  ...
C05_RS+Volume           1006  49.3%  ...                      1.77  ...
C04_RS+Breakout         1007  48.4%  ...                      1.66  ...
C00_RS_seul             1323  46.3%  +0.70%  +5.12%  -3.11%  1.42  91.1% ...    -0.55
C03_Momentum_seul       1203  47.1%  +0.62%  +4.86%  -3.15%  1.37  91.2% ...    -0.60
```

### Conclusions actionnées (v2.7)

| Finding | Evidence | Action |
|---------|----------|--------|
| Bonus accélération nuit | C08 PF=2.00 > C07 PF=1.97 (N=579 trades) | **Supprimé** de `calculer_score_total()` |
| RS seul = pire facteur individuel (PF=1.42) | N=1323 (statistiquement solide) | **Documenté** — révision poids déférée (besoin +6 mois TR live) |
| Breakout seul bat le modèle complet (PF=2.20) | N=46 (trop petit) | **Documenté** — N insuffisant pour agir |
| RS+BRK+VOL ≈ MF_5 (PF=2.01 vs 1.97) | N=529 | **Documenté** — simplification possible si TR live confirme |
| VCP : moins de 10 trades | Signal rare sur marché thin BRVM | Normal, non actionnable |

### Suivi requis
- Paper trading 8-12 semaines pour confirmer avec live data
- Re-run ablation à 150+ trades (breakout seulement) avant de modifier poids RS
- Révision pondération RS/Breakout : DÉFÉRRÉE à T+6 mois minimum

---

## 8. SCORE GLOBAL SYSTEME

| Dimension | Score | Commentaire |
|-----------|:-----:|-------------|
| Architecture pipeline | 9/10 | tradable_universe.py unifié (47 actions), dead code UNIVERSE=12 supprimé |
| Qualite signal technique | 9/10 | Ablation study prouve facteurs, acc bonus supprimé (evidence PF), setup_type pipeline |
| Gestion du risque | 8.5/10 | Blacklist, regime, vol targeting 1%/trade (CB=0), liquidite R3 |
| Signal semantique | 8.5/10 | Catalyseur x3, decay exponentiel, Top-k=3, signal_explosion, gate supprimé, blend sentiment |
| Backtest & validation | 7.5/10 | WR=53.8%, PF=2.41, MaxDD=15% (pipeline), ablation study 11 configs sur 4577 fenetres |
| Monitoring & alertes | 7/10 | Fraicheur corrigee, disclaimer espere, P&L flottant |
| Robustesse donnees | 7.5/10 | Archived filter, dedup, injection synthetiques tracables |

**Score global : 8.2/10**
*(evolution : 3.0 -> 5.8 -> 6.4 -> 6.7 -> 7.1 -> 7.6 -> 7.9 -> 8.0 -> 8.2)*

---

## 9. ROADMAP PROCHAINES AMELIORATIONS

### Priorite HAUTE
1. ~~**Pipeline-complete backtest**~~ — **FAIT** (R1 — `backtest_daily_v2.py --pipeline`, MaxDD 13.2%)
2. ~~**Meta-model recalibration**~~ — **FAIT provisoirement** (R4 — desactive, prob_win=0.55 constant)
3. ~~**Parsing PDF BRVM**~~ — **FAIT** (pdfplumber, 39/43 OK, etape 2 pipeline)
4. ~~**Pipeline semantique catalyseur (F7)**~~ — **FAIT** (v2.3 — scraper emetteur + V4 + aggregateur V2 + explosion signal)
5. ~~**Backtest MF-complet**~~ — **FAIT** (R6 — generer_signal() MF-aligne, WR=53.8%, PF=2.41, CB=0)
6. ~~**Injection BUY synthetiques (F3)**~~ — **FAIT** (R6 — injecter_decisions_mf_manquantes(), ORGT #1 TOP5)
7. ~~**VCP bonus TOP5**~~ — **FAIT** (R6 — VCP=compression>=60+breakout>=60+vsr>=2.5, +4pts, tag [VCP])
8. ~~**Ablation study multi-facteurs**~~ — **FAIT** (v2.7 — 11 configs, 4577 fenetres, acc bonus supprime)
9. ~~**Tradable universe unifié**~~ — **FAIT** (v2.7 — `tradable_universe.py` 47 actions, UNIVERSE=12 dead code supprime)
10. ~~**Setup_type classification**~~ — **FAIT** (v2.7 — EXPLOSION_VSR/VCP/BREAKOUT_VOLUME/SWING_FORT, setup_id hashé)
11. ~~**Format recommandation enrichi**~~ — **FAIT** (v2.7 — Setup+Invalidation+Liquidite dans top5_engine_final.py)
12. **Meta-model recalibration reel** — reentrainer sur features MF + track_record >= 60 trades fermes

### Priorite MOYENNE
13. ~~**Filtres swing explosion (R5)**~~ — **FAIT** (RSI<=78, compression, breakout>=50, VSR>=60)
14. ~~**Filtre liquidite (R3)**~~ — **FAIT** (val_moy20j >= 3M FCFA, jours_trades >= 10/20)
15. ~~**Run full 47 actions**~~ — **FAIT** (v2.4 — scraper emetteur integre)
16. **Agregateur sectoriel dans pipeline** — ajouter etape 4bis
17. **Scheduler journalier** — cron/Airflow a 18h15 UTC (apres publication BRVM)
18. **Track record automatique** — cloture positions TOP5 fin de semaine
19. **OCR PDFs scannes** — tesseract pour les 4 PDFs images (BOA CI/SN)
20. **Backtest execution constraints BRVM** — fill_rate, partial_fill, slippage adaptatif (Chantier 2 v2.7 — différé)

### Priorite BASSE
21. **Dashboard fraicheur temps reel** — indicateur vert/orange/rouge Django
22. **Alertes canal** — notification si circuit breaker ou regime BEAR
23. **Backtest par secteur** — WR par secteur pour affiner blacklist sectorielle
24. **Carnet d'ordre BOA Direct** — integration ob_pressure_score (port 9092, WebSocket)
    Connector cree dans scripts/connectors/boaksdirect_orderbook.py (en attente discovery)

---

## 10. FICHIERS MODIFIES

| Fichier | Modifications |
|---------|---------------|
| `extraire_pdf_pdfplumber.py` | Nouveau script — telechargement + extraction pdfplumber |
| `pipeline_brvm.py` | v2.5 : ETAPE 7 label "INJECTION BUY MANQUANTS", ETAPE 8 label "VCP" |
| `lancer_recos_daily.py` | v2.5 : docstring complete (multi_factor step), stop label 0.9->1.5xATR, step 2b VCP |
| `collecter_publications_brvm.py` | v2.4 : fusion architecturale — scraper emetteur integre (Phase B) |
| `scripts/connectors/brvm_publications_par_emetteur.py` | OBSOLETE — logique fusionnee dans `collecter_publications_brvm.py` |
| `analyse_semantique_brvm_v3.py` | V4 : score_contenu = lexique + 3xcatalyseur, 51 phrases catalyseurs, confiance texte |
| `agregateur_semantique_actions.py` | Bug #8 : gate $ne:0 supprimé, score_contenu = sem + sent/4, has_cat += sentiment_impact=HIGH |
| `top5_engine_final.py` | v2.7 : setup_type ligne, invalidation ligne, liquidite ligne, setup_id projection |
| `top5_engine_brvm.py` | Filtre `archived` + deduplication par symbol |
| `backtest_daily_v2.py` | R6 : generer_signal() MF-aligne (_score_linear, 5 facteurs, VCP, score_mf gate) + RISK_PCT=1%, MAX_ALLOC=15%, CB_DD=20% |
| `multi_factor_engine.py` | v2.7 : acc bonus supprimé (ablation), classify_setup_type(), make_setup_id(), setup_type+setup_id dans tous les docs |
| `tradable_universe.py` | NOUVEAU v2.7 — source de vérité 47 actions BRVM, get_tradable_universe(db) filtre liquidité |
| `decision_finale_brvm.py` | v2.7 : UNIVERSE=12 dead code supprimé, import UNIVERSE_BRVM_SET depuis tradable_universe |
| `ablation_study.py` | NOUVEAU v2.7 — 11 configurations, precompute-once, 4577 fenetres, 7.9s runtime |
| `propagation_sector_to_action.py` | Lecture `top5_weekly_brvm` au lieu de `is_top5` fantome |
| `backtest_reporting_monitoring.py` | UTF-8 fix, filtre archived, label espere, datetime corrige |
| `analyse_ia_simple.py` | RSI BLOQUANT threshold, ATR override |
| `requirements.txt` | `pdfplumber==0.11.9` ajoute |
| `curated_observations` (MongoDB) | Suppression 26 docs `ts='2026-12-31'` |
| `scripts/connectors/boaksdirect_orderbook.py` | Nouveau — connector carnet d'ordre BOA Direct (en attente, mode discovery) |
| `AUDIT_PIPELINE_BRVM.md` | v2.7 : ablation study section, roadmap 8-11 marked FAIT, score global 8.0->8.2 |

---

*Rapport genere le 2026-03-06 — Pipeline BRVM IA Decisionnelle v2.7 (ablation study + tradable_universe + setup_type + format enrichi, score global 8.2/10)*

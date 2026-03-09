#!/usr/bin/env python3
"""
PIPELINE COURT TERME — Recommandations 2-3 semaines
=====================================================

Utilise les données journalières (prices_daily) construites depuis
les collectes intraday (7-8x/jour) pour un signal plus frais.

Pipeline :
  [0c] preparer_sentiment_publications()  <- enrichit curated_observations
  [1/3] analyse_ia_simple.py --mode daily
  [2/3] decision_finale_brvm.py --mode daily
        Stop = 1.5 x ATR_daily | RR = 3.0 | horizon = JOUR
  [2b/3] multi_factor_engine.py --mode daily
         5 facteurs cross-sectionnels + injection BUY synthetiques
         pour EXPLOSION/SWING_FORT absents du UNIVERSE de decision_finale
  [3/3] top5_engine_final.py --mode daily
        VCP bonus +4pts, formule 0.55xMF + 0.35xAlpha + 0.10xSEM
  -> top5_daily_brvm (MongoDB, separe du weekly)

Usage :
  .venv/Scripts/python.exe lancer_recos_daily.py
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import subprocess
import re
import unicodedata
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# MAPPING : fragments de nom société → symbole BRVM (insensible à la casse)
# Priorité : clés plus longues d'abord (ordre descendant par longueur)
# ---------------------------------------------------------------------------
_COMPANY_TO_SYMBOL_RAW = {
    # ── BOA ────────────────────────────────────────────────────────────────
    "BANK OF AFRICA BURKINA":    "BOABF",
    "BANK OF AFRICA BENIN":      "BOAB",
    "BANK OF AFRICA NIGER":      "BOAN",
    "BANK OF AFRICA SENEGAL":    "BOAS",
    "BANK OF AFRICA MALI":       "BOAM",
    "BANK OF AFRICA COTE":       "BOAC",
    "BANK OF AFRICA CI":         "BOAC",
    "BANK OF AFRICA SN":         "BOAS",
    "BANK OF AFRICA BF":         "BOABF",
    "BOA BURKINA":               "BOABF",
    "BOA BENIN":                 "BOAB",
    "BOA NIGER":                 "BOAN",
    "BOA SENEGAL":               "BOAS",
    "BOA MALI":                  "BOAM",
    "BOA COTE":                  "BOAC",
    # ── Autres banques ─────────────────────────────────────────────────────
    "SOCIETE GENERALE BURKINA":  "SGBC",
    "SOCIETE GENERALE":          "SGBC",
    "SOCIETE IVOIRIENNE DE BANQUE": "SIBC",
    "SOCIETE TOGOLAISE DE BANQUE":  "STBC",
    "CORIS BANK INTERNATIONAL":  "CBIBF",
    "CORIS BANK":                "CBIBF",
    "ECOBANK TRANSNATIONAL":     "ETIT",
    "ECOBANK":                   "ECOC",
    "BICICI":                    "BICC",
    "NSIA BANQUE":               "NSBC",
    "BANQUE NATIONALE DU BURKINA": "BNBC",
    "BNB":                       "BNBC",
    # ─── Agriculture / Agroalimentaire ────────────────────────────────────
    "PALMCI":                    "PALC",
    "PALM CI":                   "PALC",
    "PALMAFRIQUE":               "PALC",
    "SOGB":                      "SOGC",
    "SAFCA":                     "SAFC",
    "SUCRIVOIRE":                "SIVC",
    # ─── Télécom ─────────────────────────────────────────────────────────
    "SONATEL":                   "SNTS",
    "ONATEL":                    "ONTBF",
    # ─── Industrie / Distribution ─────────────────────────────────────────
    "SITAB":                     "STAC",
    "SOLIBRA":                   "SLBC",
    "FILTISAC":                  "FTSC",
    "CFAO":                      "CFAC",
    "TRACTAFRIC":                "TTLS",
    "PRES FROID":                "PRSC",
    "UNILEVER":                  "UNXC",
    "SICOR":                     "SICC",
    "NEI-CEDA":                  "NEIC",
    "NEI CEDA":                  "NEIC",
    "BOLLORE":                   "ABJC",
    "SODEPALM":                  "SDCC",
    "NESTLE":                    "NTLC",
    "ORAGROUP":                  "ORAC",
    "SMBC":                      "SMBC",
    "SMB ":                      "SMBC",
    # ─── Symboles BRVM directs (4-5 lettres majuscules présents dans le titre) ──
    # (gérés séparément par regex — voir _extract_symbol_from_text)
}

# Trier par longueur décroissante pour matching greedy (priorité au plus précis)
COMPANY_TO_SYMBOL = dict(
    sorted(_COMPANY_TO_SYMBOL_RAW.items(), key=lambda x: -len(x[0]))
)

# Liste officielle des 47 symboles BRVM pour détection directe
BRVM_SYMBOLS_SET = {
    "ABJC","BICB","BICC","BNBC","BOAB","BOABF","BOAC","BOAM","BOAN","BOAS",
    "CABC","CBIBF","CFAC","CIEC","ECOC","ETIT","FTSC","LNBB","NEIC","NSBC",
    "NTLC","ONTBF","ORAC","ORGT","PALC","PRSC","SAFC","SCRC","SDCC","SDSC",
    "SEMC","SGBC","SHEC","SIBC","SICC","SIVC","SLBC","SMBC","SNTS","SOGC",
    "SPHC","STAC","STBC","TTLC","TTLS","UNLC","UNXC",
}

# Règles de scoring par type d'événement (motifs → score)
# Score : de -80 à +35. Seuils dans get_sentiment_for_symbol : ±20 = pos/neg
EVENT_RULES = [
    # Négatif fort
    (["suspension de cotation", "suspension cotation", "cotation suspendue"], -80, "HIGH"),
    (["defaut de paiement", "incapacite de paiement"], -60, "HIGH"),
    (["perte nette", "resultat negatif", "deficitaire", "redressement judiciai"], -30, "HIGH"),
    (["difficulte financier", "tension financier"], -25, "MEDIUM"),
    (["assemblee generale extraordinaire", "ag extraordinaire"], -8, "MEDIUM"),
    (["report de l assemblee", "report assemblee"], -5, "LOW"),
    # Neutre
    (["avis de convocation", "pouvoir", "assemblee generale ordinaire", "ag ordinaire",
      "rapport annuel", "bilan annuel", "communique"], 0, "LOW"),
    # Positif
    (["augmentation de capital"], +12, "MEDIUM"),
    (["dividende", "coupon", "mise en paiement dividend"], +25, "MEDIUM"),
    (["resultat en hausse", "benefice en hausse", "croissance des resultats",
      "performance record", "record de benefice", "resultat positif"], +35, "HIGH"),
    (["resultat satisfaisant", "hausse du chiffre d affaires",
      "croissance chiffre d affaires"], +20, "MEDIUM"),
]


def _normalize(text: str) -> str:
    """Supprime accents, ponctuation non-alphanumérique, met en majuscule."""
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Remplacer toute ponctuation/tiret/apostrophe par un espace
    cleaned = re.sub(r"[^\w\s]", " ", without_accents)
    return " ".join(cleaned.upper().split())


def _extract_symbol_from_text(text_norm: str):
    """
    Tente d'extraire un symbole BRVM depuis un texte normalisé.
    1. Recherche directe des codes BRVM (ex. SNTS, BOABF)
    2. Recherche par fragements de nom société
    Retourne le symbole ou None.
    """
    # 1. Codes BRVM directs (mot entier, priorité aux plus longs d'abord)
    for sym in sorted(BRVM_SYMBOLS_SET, key=len, reverse=True):
        if re.search(r'\b' + sym + r'\b', text_norm):
            return sym

    # 2. Fragments de noms
    for fragment, sym in COMPANY_TO_SYMBOL.items():
        if _normalize(fragment) in text_norm:
            return sym

    return None


def _score_event(text_norm: str):
    """
    Détermine le score sentiment et l'impact à partir du texte normalisé.
    Retourne (score: float, impact: str) ou (0.0, "LOW") si aucun match.
    """
    for patterns, score, impact in EVENT_RULES:
        for pat in patterns:
            if _normalize(pat) in text_norm:
                return float(score), impact
    return 0.0, "LOW"


def preparer_sentiment_publications() -> dict:
    """
    Étape 0c du pipeline — Enrichit les curated_observations BRVM_PUBLICATION
    avec attrs.emetteur et attrs.sentiment_score exploitables par
    get_sentiment_for_symbol() dans analyse_ia_simple.py.

    Stratégie :
    - Lis les docs source='BRVM_PUBLICATION' depuis curated_observations
    - Extrais le symbole BRVM + le type d'événement depuis le champ 'key'
    - Calcule un score de sentiment par événement (règles expertes BRVM)
    - Met à jour attrs.emetteur + attrs.sentiment_score + attrs.sentiment_impact
      uniquement pour les docs avec un symbole identifié et un événement reconnu
    - Les BOC PDFs (URL) et les données numériques sont ignorés silencieusement.

    Retourne: dict avec stats {total, enriched, skipped}
    """
    try:
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = c["centralisation_db"]
    except Exception as e:
        print(f"  [SENTIMENT] MongoDB inaccessible : {e}")
        return {"total": 0, "enriched": 0, "skipped": 0}

    docs = list(db.curated_observations.find({"source": "BRVM_PUBLICATION"}))
    total = len(docs)
    enriched = 0
    skipped = 0
    symbol_events: dict[str, list] = {}  # symbol → [(score, impact)]

    for doc in docs:
        raw_key = str(doc.get("key") or "")

        # Ignorer : URLs de PDF / données numériques pures
        if raw_key.startswith("http") or re.match(r'^[\d\s,.\-FCFA]+$', raw_key.strip()):
            skipped += 1
            continue

        text_norm = _normalize(raw_key)

        # Extraire le symbole BRVM
        symbol = _extract_symbol_from_text(text_norm)
        if not symbol:
            # Essayer aussi depuis attrs.title
            title_attr = str(doc.get("attrs", {}).get("title") or "")
            if title_attr:
                symbol = _extract_symbol_from_text(_normalize(title_attr))

        if not symbol:
            skipped += 1
            continue

        # Scorer l'événement
        score, impact = _score_event(text_norm)

        # Mettre à jour le doc MongoDB
        db.curated_observations.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "attrs.emetteur": symbol,
                "attrs.sentiment_score": score,
                "attrs.sentiment_impact": impact,
                "attrs.sentiment_enriched_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        enriched += 1
        symbol_events.setdefault(symbol, []).append((score, impact))

    # Affichage résumé
    print(f"  [SENTIMENT] {total} publications | {enriched} enrichies | {skipped} ignorées")
    if symbol_events:
        print(f"  [SENTIMENT] Symboles avec signal :")
        for sym in sorted(symbol_events):
            scores = [s for s, _ in symbol_events[sym]]
            avg = sum(scores) / len(scores)
            label = "POSITIF" if avg >= 20 else ("NEGATIF" if avg <= -20 else "NEUTRE")
            print(f"    {sym:6s} : {len(scores)} pub(s) | score moy {avg:+.0f} → {label}")
    else:
        print("  [SENTIMENT] Aucun symbole identifie dans les publications (donnees insuffisantes)")

    return {"total": total, "enriched": enriched, "skipped": skipped}


# ---------------------------------------------------------------------------
# AMÉLIORATION 2 — Backtest : affichage du dernier résultat CSV
# ---------------------------------------------------------------------------
def afficher_backtest_summary():
    """
    Lit le dernier fichier backtest_daily_v2_*.csv et affiche un résumé compact.
    Calcule Win Rate, Profit Factor, Gain moyen, Max Drawdown.
    Appel : après le classement TOP5, avant l'affichage final.
    """
    import csv
    import glob
    import os

    pattern = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_daily_v2_*.csv")
    fichiers = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

    if not fichiers:
        print("\n  [VALIDATION BACKTEST] Aucun backtest disponible — relancer backtest_daily_v2.py")
        return

    csv_path = fichiers[0]
    csv_nom  = os.path.basename(csv_path)

    trades = []
    try:
        with open(csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    trades.append({
                        "rendement_reel": float(row["rendement_reel"]),
                        "gagnant":        row["gagnant"].strip().lower() in ("true", "1", "yes"),
                        "date_entree":    row.get("date_entree", ""),
                    })
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"\n  [VALIDATION BACKTEST] Erreur lecture {csv_nom} : {e}")
        return

    if not trades:
        print(f"\n  [VALIDATION BACKTEST] Fichier vide : {csv_nom}")
        return

    n         = len(trades)
    gagnants  = [t for t in trades if t["gagnant"]]
    perdants  = [t for t in trades if not t["gagnant"]]
    win_rate  = round(len(gagnants) / n * 100, 1)
    gains_tot = sum(t["rendement_reel"] for t in gagnants)
    pertes_tot = abs(sum(t["rendement_reel"] for t in perdants))
    pf        = round(gains_tot / pertes_tot, 2) if pertes_tot > 0 else float("inf")
    gain_moy  = round(sum(t["rendement_reel"] for t in trades) / n, 2)

    # Max Drawdown cumulatif sur capital simulé
    capital   = 100.0
    peak      = capital
    max_dd    = 0.0
    for t in trades:
        capital   += capital * t["rendement_reel"] / 100
        if capital > peak:
            peak = capital
        dd = (peak - capital) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Période couverte
    dates = sorted(set(t["date_entree"] for t in trades if t["date_entree"]))
    periode = f"{dates[0]} → {dates[-1]}" if len(dates) >= 2 else "N/A"

    print(f"\n{'─'*66}")
    print(f"  VALIDATION BACKTEST ({csv_nom})")
    print(f"{'─'*66}")
    print(f"  Trades : {n} | Période : {periode}")
    print(f"  Win Rate   : {win_rate:.1f}%  ({len(gagnants)}W / {len(perdants)}L)")
    print(f"  Profit Factor : {pf:.2f}   |  Gain moyen : {gain_moy:+.2f}%")
    print(f"  Max Drawdown  : -{max_dd:.1f}%")
    if win_rate >= 55 and pf >= 1.5:
        print("  VERDICT : Signal robuste — systeme valide")
    elif win_rate >= 45 and pf >= 1.0:
        print("  VERDICT : Signal correct — ameliorable")
    else:
        print("  VERDICT : signal faible — revoir les parametres")
    print(f"{'─'*66}")


# ---------------------------------------------------------------------------
# AMÉLIORATION 3 — Suivi des positions ouvertes (alertes visuelles)
# ---------------------------------------------------------------------------
def verifier_positions_ouvertes():
    """
    Lit top5_daily_brvm et compare les prix d'entrée aux dernières clôtures.
    Affiche le P&L flottant et des alertes si cible/stop/time stop atteints.
    Appel : après afficher_backtest_summary().
    """
    try:
        from pymongo import MongoClient
        c  = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = c["centralisation_db"]
    except Exception as e:
        print(f"\n  [POSITIONS] MongoDB inaccessible : {e}")
        return

    positions = list(db.top5_daily_brvm.find(
        {},
        {"symbol": 1, "prix_entree": 1, "prix_sortie": 1, "prix_cible": 1, "stop": 1,
         "first_selected_at": 1, "rank": 1, "gain_attendu": 1}
    ).sort("rank", 1))

    if not positions:
        print("\n  [POSITIONS] Aucune position ouverte (top5_daily_brvm vide)")
        return

    now = datetime.now(timezone.utc)
    pal_liste = []

    print(f"\n{'='*66}")
    print("  PORTEFEUILLE OUVERT — P&L FLOTTANT")
    print(f"{'='*66}")

    for p in positions:
        symbol      = p.get("symbol", "???")
        prix_entree = p.get("prix_entree") or p.get("entry")
        prix_cible  = p.get("prix_sortie") or p.get("prix_cible")
        stop        = p.get("stop")
        rank        = p.get("rank", "?")
        first_sel   = p.get("first_selected_at")

        # Clôture la plus récente depuis prices_daily
        last_daily = db.prices_daily.find_one(
            {"symbol": symbol},
            {"close": 1, "date": 1},
            sort=[("date", -1)]
        )
        if not last_daily:
            print(f"  #{rank} {symbol:<6} | Entrée {_fmt(prix_entree)} | Pas de cours disponible")
            continue

        prix_actuel = last_daily.get("close")
        date_cours  = last_daily.get("date", "?")

        if not prix_actuel or not prix_entree or prix_entree <= 0:
            print(f"  #{rank} {symbol:<6} | Prix manquant")
            continue

        pal_pct = (prix_actuel - prix_entree) / prix_entree * 100
        pal_liste.append(pal_pct)

        # Calcul durée en position
        jours_en_pos = 0
        if first_sel:
            if hasattr(first_sel, "tzinfo") and first_sel.tzinfo is None:
                first_sel = first_sel.replace(tzinfo=timezone.utc)
            jours_en_pos = (now - first_sel).days

        # Statut
        alerte = ""
        if prix_cible and prix_actuel >= prix_cible:
            alerte = "  >>> CIBLE ATTEINTE — PRENDRE PROFIT"
        elif stop and prix_actuel <= stop:
            alerte = "  >>> STOP ATTEINT — SORTIR IMMEDIATEMENT"
        elif jours_en_pos >= 10:
            alerte = f"  >>> TIME STOP J+{jours_en_pos} — CLOTURER SI CIBLE NON ATTEINTE"
        elif stop and pal_pct < 0 and prix_actuel <= stop * 1.03:
            # Seulement si on a déjà perdu ET qu'on est proche du stop
            alerte = f"  >>> PROCHE STOP ({_fmt(stop)})"

        # Indicateur directionnel
        if alerte.startswith("  >>> CIBLE"):
            etat = "PROFIT"
        elif alerte.startswith("  >>> STOP"):
            etat = "STOP"
        elif alerte.startswith("  >>> TIME"):
            etat = "TIME"
        elif pal_pct >= 0:
            etat = f"TENIR (cible {_fmt(prix_cible)})"
        else:
            etat = f"SURVEILLER (cible {_fmt(prix_cible)})"

        signe = "+" if pal_pct >= 0 else ""
        print(f"  #{rank} {symbol:<6} | Entree {_fmt(prix_entree)} | Actuel {_fmt(prix_actuel)} "
              f"({date_cours}) | P&L {signe}{pal_pct:.1f}% | {etat}")
        if alerte:
            print(alerte)

    if pal_liste:
        pal_moy = sum(pal_liste) / len(pal_liste)
        signe   = "+" if pal_moy >= 0 else ""
        print(f"{'─'*66}")
        print(f"  P&L moyen portefeuille : {signe}{pal_moy:.1f}%")
    print(f"{'='*66}\n")


def _fmt(v):
    """Formate un prix FCFA avec séparateur milliers."""
    if v is None:
        return "N/A"
    try:
        return f"{float(v):,.0f}".replace(",", " ")
    except Exception:
        return str(v)


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))


def titre(label):
    safe_print(f"\n{'='*62}")
    safe_print(f"  {label}")
    safe_print(f"{'='*62}")


def run(script, label):
    titre(label)
    result = subprocess.run(
        [sys.executable, script, "--mode", "daily"],
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        safe_print(f"[ERREUR] Script {script} a échoué (code {result.returncode})")
        return False
    return True


def verifier_donnees():
    """Vérifie que les données prices_daily sont disponibles (source principale)."""
    try:
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = c["centralisation_db"]

        n_daily = db.prices_daily.count_documents({})
        symbols_daily = db.prices_daily.distinct("symbol")
        last_day = db.prices_daily.find_one(sort=[("date", -1)])
        derniere_date = last_day["date"] if last_day else "N/A"

        print(f"  prices_daily    : {n_daily:,} docs | {len(symbols_daily)} symboles | dernier : {derniere_date}")

        if n_daily < 50:
            print("  [BLOQUANT] Pas assez de données prices_daily.")
            print("  → Lancez d'abord : .venv/Scripts/python.exe build_daily.py")
            return False

        n_intraday = db.prices_intraday_raw.count_documents({})
        print(f"  prices_intraday : {n_intraday:,} collectes brutes")

        n_weekly = db.prices_weekly.count_documents({})
        print(f"  prices_weekly   : {n_weekly:,} docs (référence croisée)")

        return True

    except Exception as e:
        print(f"  [ERREUR] MongoDB inaccessible : {e}")
        print("  → Vérifiez que MongoDB est démarré.")
        return False


def evaluer_contexte_marche():
    """
    Seuil d'Activation Marché — vérifie si le marché est en état de générer des signaux.
    Bloque les recommandations si le marché est en repli généralisé (>70% actions baissières
    ou perf médiane 10j < -3%).
    Retourne: (True=OK, message, score_marche)
    """
    try:
        from pymongo import MongoClient
        from statistics import median
        c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = c["centralisation_db"]

        # Récupérer la dernière date disponible
        last = db.prices_daily.find_one(sort=[("date", -1)])
        if not last:
            return True, "Données insuffisantes pour évaluer le marché", 50

        symbols = db.prices_daily.distinct("symbol")
        perfs_10j = []

        for sym in symbols:
            docs = list(db.prices_daily.find(
                {"symbol": sym},
                {"date": 1, "close": 1}
            ).sort("date", -1).limit(11))

            if len(docs) < 6:
                continue
            docs = docs[::-1]  # chronologique
            prix_debut = docs[0].get("close") or 0
            prix_fin = docs[-1].get("close") or 0
            if prix_debut > 0:
                perf = (prix_fin - prix_debut) / prix_debut * 100
                perfs_10j.append((sym, perf))

        if len(perfs_10j) < 20:
            return True, "Pas assez de données pour évaluer le contexte marché", 50

        perfs = [p for _, p in perfs_10j]
        med_perf = round(median(perfs), 2)
        pct_baissier = sum(1 for p in perfs if p < 0) / len(perfs) * 100
        # Score marché [0-100] : 50 = neutre, >50 = haussier, <50 = baissier
        score_marche = round(50 + med_perf * 3, 1)
        score_marche = max(0, min(100, score_marche))

        # Seuil d'alerte
        if med_perf < -3.0 or pct_baissier > 70:
            msg = (f"[ALERTE MARCHE] Perf médiane 10j={med_perf:+.1f}% | "
                   f"{pct_baissier:.0f}% actions baissières — "
                   "marché en repli, signaux non fiables")
            return False, msg, score_marche

        msg = (f"Contexte marché OK | Perf médiane 10j={med_perf:+.1f}% | "
               f"{pct_baissier:.0f}% actions baissières | Score={score_marche:.0f}/100")
        return True, msg, score_marche


    except Exception as e:
        return True, f"Erreur évaluation marché (ignorée): {e}", 50


def afficher_top5():
    """Affiche le TOP5 court terme (top5_daily_brvm)."""
    try:
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/")
        db = c["centralisation_db"]

        top5 = list(db.top5_daily_brvm.find({}, {"_id": 0}).sort("rank", 1))

        if not top5:
            print("\n  Aucune recommandation court terme générée.")
            return

        print(f"\n{'='*70}")
        print("  TOP 5 RECOMMANDATIONS BRVM — COURT TERME | Horizon : 2-3 semaines")
        print(f"{'='*70}")
        print(f"  {'#':<3} {'Symbol':<6} {'Cl.':<4} {'Entrée':>9} {'Gain':>7} {'Stop':>7} {'WOS':>5} {'ATR%':>5} {'RR':>5}  {'Alloc':>6}  {'Timing'}")
        print(f"  {'-'*68}")

        for r in top5:
            rank     = r.get("rank", "?")
            symbol   = r.get("symbol", "?")
            classe   = r.get("classe", "?")
            prix     = r.get("prix_entree", r.get("prix", 0))
            gain     = r.get("gain_attendu", 0)
            stop_abs = r.get("stop", 0)
            stop_pct = ((prix - stop_abs) / prix * 100) if prix and stop_abs else r.get("stop_pct", 0)
            wos      = r.get("wos", r.get("wos_score", 0))
            atr      = r.get("atr_pct", 0)
            rr       = r.get("rr", 0)
            alloc    = r.get("allocation_max", 5.0)
            timing   = r.get("timing_signal", "N/A")
            liq      = r.get("position_size_factor", 1.0) or 1.0

            liq_tag = "" if liq >= 1.0 else " [LIQ-]"

            if timing == "CONFIRME":
                timing_tag = "OK-ENTRER"
            elif timing == "ATTENDRE":
                timing_tag = "ATTENDRE!"
            elif timing == "NEUTRE":
                timing_tag = "NEUTRE"
            else:
                timing_tag = "N/A"

            print(f"  #{rank:<2} {symbol:<6} {classe:<4} {prix:>9,.0f} {gain:>+6.1f}% {stop_pct:>-6.1f}% {wos:>5.1f} {atr:>4.1f}% {rr:>5.2f}  {alloc:>4.0f}%{'':<2}  {timing_tag}{liq_tag}")

        # A4 — Time Stop J+10 : alerte si action dans TOP5 depuis >= 10 jours
        alertes_timestop = []
        for r in top5:
            first_sel = r.get("first_selected_at")
            if first_sel and isinstance(first_sel, datetime):
                # Normaliser timezone si nécessaire
                if first_sel.tzinfo is None:
                    first_sel = first_sel.replace(tzinfo=timezone.utc)
                jours = (datetime.now(timezone.utc) - first_sel).days
                if jours >= 10:
                    alertes_timestop.append((r.get("symbol", "?"), jours))

        if alertes_timestop:
            print(f"\n  {'!'*66}")
            print(f"  TIME STOP J+10 — EVALUER SORTIE AUJOURD'HUI")
            print(f"  {'!'*66}")
            for sym, nb_j in alertes_timestop:
                print(f"  >>> {sym:<6} dans TOP5 depuis {nb_j}j (max 10j) — sortir si cible non atteinte")
            print(f"  {'!'*66}")

        print(f"\n  Générées le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"\n  {'─'*66}")
        print(f"  REGLES DE GESTION COURT TERME")
        print(f"  {'─'*66}")
        print(f"  > Horizon de détention : 2-3 semaines")
        print(f"  > MAX 3 positions simultanées")
        print(f"  > Alloc A=15% | B=10% | C=5% du portefeuille par position")
        print(f"  > Timing ATTENDRE! → différer l'entrée au lendemain")
        print(f"  > Stop obligatoire : ordre limite 1 tick sous le niveau indiqué")
        print(f"  > Confirmer l'entrée sur hausse intraday du matin")
        print(f"  {'─'*66}\n")

    except Exception as e:
        print(f"  [ERREUR affichage] {e}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*62)
    print("  PIPELINE COURT TERME — 2 à 3 semaines")
    print("  Source : prices_daily (données journalières)")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*62)

    # 0. Vérification données
    print("\n[0/3] Vérification données journalières...")
    if not verifier_donnees():
        sys.exit(1)

    # 0b. Contexte marché — Seuil d'Activation
    print("\n[CONTEXTE] Évaluation conditions de marché...")
    marche_ok, marche_msg, score_marche = evaluer_contexte_marche()
    safe_print(f"  {marche_msg}")
    if not marche_ok:
        safe_print(f"  [!] Score marché : {score_marche:.0f}/100 (seuil minimal : 35/100)")
        safe_print("  [!] Les signaux générés ont une fiabilité réduite en marché baissier.")
        safe_print("  [!] Nombre de positions recommandé : 0 à 1 maximum (capital préservé)")
    else:
        safe_print(f"  Score marché : {score_marche:.0f}/100")

    # 0c. Enrichissement sentiment publications officielles BRVM
    print("\n[SENTIMENT] Préparation signal sentiment depuis publications BRVM...")
    preparer_sentiment_publications()

    # 1. Analyse IA (mode daily)
    ok = run("analyse_ia_simple.py", "[1/3] Analyse IA — Mode DAILY (prices_daily)")
    if not ok:
        print("[STOP] Erreur étape 1")
        sys.exit(1)

    # 2. Décisions BUY (mode daily — stop=1.5×ATR_daily, RR=3.0)
    ok = run("decision_finale_brvm.py", "[2/3] Decisions BUY — Stop=1.5xATR_daily | RR=3.0 | horizon=JOUR")
    if not ok:
        print("[STOP] Erreur étape 2")
        sys.exit(1)

    # 2b. Multi-Factor Score cross-sectionnel + injection BUY manquants
    ok = run("multi_factor_engine.py", "[2b/3] Multi-Factor Score + Injection BUY synthetiques (EXPLOSION/SWING_FORT)")
    if not ok:
        print("[STOP] Erreur étape 2b")
        sys.exit(1)

    # 3. Classement TOP5 → top5_daily_brvm (VCP +4pts, 0.55xMF+0.35xAlpha+0.10xSEM)
    ok = run("top5_engine_final.py", "[3/3] Classement TOP5 — VCP bonus, Regime, TP1/TP2/Runner -> top5_daily_brvm")
    if not ok:
        print("[STOP] Erreur étape 3")
        sys.exit(1)

    afficher_top5()

    # POST-A. Validation — résumé backtest
    afficher_backtest_summary()

    # POST-B. Suivi portefeuille — P&L flottant et alertes cible/stop/time stop
    verifier_positions_ouvertes()

    print("\n" + "="*62)
    print("  PIPELINE COURT TERME TERMINÉ")
    print("  Collection MongoDB : top5_daily_brvm")
    print("="*62 + "\n")

#!/usr/bin/env python3
"""
AGRÉGATEUR SÉMANTIQUE PAR ACTION — V2 (QUANT DESK / EXPLOSION DETECTOR)
==========================================================================

Modèle :
    Score_final(doc) = score_contenu × w_source × w_recence × w_confiance × w_position
    Score(symbole)   = SUM des top-3 docs (par |score_final|)

Paramètres BRVM swing 1-2 semaines :
    Fenêtre analyse : 14 jours
    Half-life       : 5 jours (decay exponentiel)
    Top-k docs      : 3 (anti-spam)
    Seuil explosion : +12 (score_7j)
    Catalyseur requis dans les 72h pour activer le signal

Signal explosion :
    score_semantique_7j >= SEUIL_EXPLOSION
    + catalyseur dans les 72h
    + (confirmation technique : VSR spike + breakout — vérifiée dans top5_engine_final.py)
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# ─── Paramètres globaux ─────────────────────────────────────────────────────
HALF_LIFE_DAYS   = 5.0   # demi-vie du signal (jours)
FENETRE_JOURS    = 14    # on ignore les docs > 14j
TOP_K_DOCS       = 3     # max docs pris en compte par symbole
SEUIL_EXPLOSION  = 12.0  # score_7j >= seuil → signal explosion potentiel
DELAI_CATALYSEUR = 3     # catalyseur doit être dans les 3 derniers jours

# ─── Pondération SOURCE ──────────────────────────────────────────────────────
SOURCE_WEIGHTS = {
    "BRVM_PUBLICATION": 1.0,   # communiqué officiel BRVM / emetteur
    "RICHBOURSE":       0.5,   # agence financière / presse
    "AUTRE":            0.5,
}

# ─── Pondération POSITION dans doc multi-symboles ───────────────────────────
POSITION_WEIGHTS = [1.0, 0.7, 0.5, 0.3]   # index 0,1,2,3+

# ─── Pondération ÉVÉNEMENT (classification) ─────────────────────────────────
EVENT_WEIGHTS = {
    "RESULTATS":    3.0,
    "DIVIDENDE":    2.5,
    "NOTATION":     2.2,
    "PARTENARIAT":  1.8,
    "COMMUNIQUE":   1.0,
    "CITATION":     0.4,
    "AG":           1.2,
    "AUTRE":        0.8,
}


def time_weight_exp(days_old: int) -> float:
    """
    Decay exponentiel : 0.5^(days / half_life)
    Exemples (half_life=5j) :
        0j → 1.00  |  5j → 0.50  |  10j → 0.25  |  14j → 0.13  |  >14j → 0
    """
    if days_old > FENETRE_JOURS:
        return 0.0
    return 0.5 ** (days_old / HALF_LIFE_DAYS)


def classify_event(text: str, title: str = "") -> str:
    combined = (text + " " + title).lower()
    if any(k in combined for k in ["résultat", "chiffre d'affaires", "bénéfice", "perte"]):
        return "RESULTATS"
    if any(k in combined for k in ["dividende", "distribution", "détachement", "coupon"]):
        return "DIVIDENDE"
    if any(k in combined for k in ["notation", "rating", "dégradation", "amélioration note"]):
        return "NOTATION"
    if any(k in combined for k in ["partenariat", "accord", "contrat", "alliance"]):
        return "PARTENARIAT"
    if any(k in combined for k in ["assemblée", "convocation", "ag "]):
        return "AG"
    if any(k in combined for k in ["communiqué", "annonce"]):
        return "COMMUNIQUE"
    return "AUTRE"


def main():
    _, db = get_mongo_db()

    print("\n" + "=" * 70)
    print(" AGRÉGATEUR SÉMANTIQUE V2 — EXPLOSION DETECTOR ".center(70))
    print(f" Fenetre={FENETRE_JOURS}j  |  Half-life={HALF_LIFE_DAYS}j  |  Top-k={TOP_K_DOCS}  |  Seuil={SEUIL_EXPLOSION} ".center(70))
    print("=" * 70 + "\n")

    today = datetime.now()
    date_limite = today - timedelta(days=FENETRE_JOURS)

    # Charger tous les docs publications avec un identifiant société (emetteur OU symboles)
    # NOTE : gate semantic_score_base!=0 supprimé — bloquait les docs enrichis par
    # preparer_sentiment_publications() mais pas encore passés par analyse_semantique_brvm_v3
    docs = list(db.curated_observations.find({
        "$and": [
            {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}},
            {"$or": [
                {"attrs.emetteur": {"$exists": True, "$ne": None}},
                {"attrs.symboles": {"$exists": True, "$ne": []}},
            ]}
        ]
    }))

    print(f"  {len(docs)} publications avec identifiant societe charges (fenetre agregateur)\n")

    # ─── Collecte des scores par symbole ─────────────────────────────────────
    # sym_docs[symbol] = [(score_final, days_old, has_catalyseur, event_type)]
    sym_docs = defaultdict(list)

    n_docs_fenetre = 0
    n_docs_hors    = 0

    for doc in docs:
        attrs  = doc.get("attrs", {})
        source = doc.get("source", "AUTRE")

        # ── Date et récence
        ts = doc.get("ts")
        try:
            if isinstance(ts, str):
                pub_date = datetime.fromisoformat(ts.split("T")[0])
            elif isinstance(ts, datetime):
                pub_date = ts
            else:
                pub_date = today
        except Exception:
            pub_date = today

        days_old = (today - pub_date).days
        w_recence = time_weight_exp(days_old)

        if w_recence == 0.0:
            n_docs_hors += 1
            continue
        n_docs_fenetre += 1

        # ── Scores de base (V4 sémantique + sentiment événementiel)
        score_sem     = attrs.get("semantic_score_base") or 0
        score_sent    = attrs.get("sentiment_score") or 0
        # sentiment_score (-80 à +35) pondéré /4 pour aligner sur l'échelle sémantique
        score_contenu = score_sem + score_sent / 4.0
        w_confiance   = attrs.get("semantic_confiance", 0.7)   # défaut 0.7 pour docs V3
        # has_catalyseur : signal V4 OU impact HIGH (dividende, résultats, perte nette)
        has_cat       = (
            attrs.get("has_catalyseur", False)
            or attrs.get("sentiment_impact", "LOW") == "HIGH"
        )

        # ── Classification événement
        text  = attrs.get("full_text", attrs.get("description", attrs.get("contenu", "")))
        title = attrs.get("titre", attrs.get("title", ""))
        event_type = classify_event(text, title)
        w_event = EVENT_WEIGHTS.get(event_type, 1.0)

        # ── Source
        w_source = SOURCE_WEIGHTS.get(source, 0.5)

        # ── Symboles à traiter
        symbols_to_process = []
        emetteur = attrs.get("emetteur")
        if emetteur:
            symbols_to_process.append((emetteur, 0))
        for idx, sym in enumerate(attrs.get("symboles", [])):
            if not (idx == 0 and emetteur and sym == emetteur):
                symbols_to_process.append((sym, idx if emetteur else idx))

        if not symbols_to_process:
            continue

        # ── Score final par symbole
        for symbol, position in symbols_to_process:
            w_pos = POSITION_WEIGHTS[min(position, len(POSITION_WEIGHTS) - 1)]

            # Score_final(doc) = score_contenu × w_source × w_recence × w_confiance × w_event × w_position
            score_final = (score_contenu
                           * w_source
                           * w_recence
                           * w_confiance
                           * w_event
                           * w_pos)

            sym_docs[symbol].append({
                "score_final":  score_final,
                "score_contenu": score_contenu,
                "days_old":     days_old,
                "has_catalyseur": has_cat,
                "event_type":   event_type,
                "w_recence":    round(w_recence, 3),
                "w_source":     w_source,
                "titre":        title[:60] if title else "",
            })

    print(f"  Docs dans fenetre {FENETRE_JOURS}j : {n_docs_fenetre}")
    print(f"  Docs hors fenetre          : {n_docs_hors}\n")

    # ─── Agrégation Top-k=3 par symbole ──────────────────────────────────────
    print("=" * 70)
    print("  SCORES PAR ACTION (Top-3 docs par action)")
    print("=" * 70)

    results = {}

    for symbol, doc_list in sym_docs.items():
        # Trier par |score_final| décroissant → prendre les 3 plus impactants
        top_docs = sorted(doc_list, key=lambda d: abs(d["score_final"]), reverse=True)[:TOP_K_DOCS]

        score_7j = sum(d["score_final"] for d in top_docs)

        # Catalyseur récent (dans les DELAI_CATALYSEUR jours)
        cat_recent = any(
            d["has_catalyseur"] and d["days_old"] <= DELAI_CATALYSEUR
            for d in doc_list  # on cherche dans TOUS les docs (pas juste top-3)
        )

        # Signal explosion : score élevé + catalyseur récent
        signal_explosion = (score_7j >= SEUIL_EXPLOSION and cat_recent)

        # Sentiment global
        if score_7j > 2:
            sentiment = "POSITIF"
        elif score_7j < -2:
            sentiment = "NEGATIF"
        else:
            sentiment = "NEUTRE"

        # Types événements des top docs
        event_types = list({d["event_type"] for d in top_docs})

        results[symbol] = {
            "score_semantique_7j":    round(score_7j, 2),
            "score_semantique_semaine": round(score_7j, 2),   # alias backward compat
            "catalyseur_recent_72h":  cat_recent,
            "signal_explosion":       signal_explosion,
            "nb_docs_total":          len(doc_list),
            "nb_docs_top_k":          len(top_docs),
            "sentiment_global":       sentiment,
            "event_types":            event_types,
            "top_docs":               top_docs,
        }

    # Trier par score_7j décroissant
    sorted_results = sorted(results.items(), key=lambda x: x[1]["score_semantique_7j"], reverse=True)

    count_saved = 0
    count_explosion = 0

    for symbol, data in sorted_results:
        score_7j = data["score_semantique_7j"]
        explosion = data["signal_explosion"]
        cat_recent = data["catalyseur_recent_72h"]

        # ── Sauvegarder dans AGREGATION_SEMANTIQUE_ACTION
        existing = db.curated_observations.find_one({
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key":     symbol,
        })

        fields_to_set = {
            "symbol":                   symbol,
            "score_semantique_7j":      score_7j,
            "score_semantique_semaine": score_7j,
            "catalyseur_recent_72h":    cat_recent,
            "signal_explosion":         explosion,
            "nb_publications":          data["nb_docs_total"],
            "nb_docs_top_k":            data["nb_docs_top_k"],
            "sentiment_global":         data["sentiment_global"],
            "types_events":             data["event_types"],
            "last_semantic_update":     datetime.utcnow(),
            "aggregateur_version":      "v2_topk_explosion",
        }

        if existing:
            attrs_merged = existing.get("attrs", {})
            attrs_merged.update(fields_to_set)
            db.curated_observations.update_one(
                {"dataset": "AGREGATION_SEMANTIQUE_ACTION", "key": symbol},
                {"$set": {"attrs": attrs_merged, "value": score_7j}}
            )
        else:
            db.curated_observations.insert_one({
                "source":  "AGREGATION_SEMANTIQUE",
                "dataset": "AGREGATION_SEMANTIQUE_ACTION",
                "key":     symbol,
                "ts":      today.strftime("%Y-%m-%d"),
                "value":   score_7j,
                "attrs":   fields_to_set,
            })

        count_saved += 1
        if explosion:
            count_explosion += 1

        # Affichage
        flag_exp  = "  *** EXPLOSION ***" if explosion else ""
        flag_cat  = "  [CAT RECENT]"      if cat_recent else ""
        print(f"  {symbol:6s}  score_7j={score_7j:7.2f}  "
              f"{data['sentiment_global']:8s}  "
              f"top_docs={data['nb_docs_top_k']}/{data['nb_docs_total']}"
              f"{flag_cat}{flag_exp}")
        if explosion:
            for d in data["top_docs"][:2]:
                print(f"          [{d['event_type']:10s}] {d['titre'][:50]}  "
                      f"(w_rec={d['w_recence']}, score={d['score_final']:.1f})")

    print(f"\n{'='*70}")
    print(f"  Actions sauvegardees  : {count_saved}")
    print(f"  Signaux EXPLOSION     : {count_explosion}  (score>={SEUIL_EXPLOSION} + catalyseur 72h)")
    print(f"  Parametres            : half_life={HALF_LIFE_DAYS}j / fenetre={FENETRE_JOURS}j / top_k={TOP_K_DOCS}")
    print(f"{'='*70}")
    print("  Prochaine etape : top5_engine_final.py  (integration score_semantique_7j)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

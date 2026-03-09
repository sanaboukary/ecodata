#!/usr/bin/env python3
"""
TEST RAPIDE - Agrégation Sémantique (Sans Momentum)
"""
import os
import sys
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Classification événement rapide
def classify_event(text: str, title: str = "") -> str:
    combined = (text + " " + title).lower()
    if any(kw in combined for kw in ["resultat", "chiffre d'affaires", "benefice"]):
        return "RESULTATS"
    if "dividende" in combined:
        return "DIVIDENDE"
    if "notation" in combined:
        return "NOTATION"
    if "partenariat" in combined or "accord" in combined:
        return "PARTENARIAT"
    if "communique" in combined:
        return "COMMUNIQUE"
    return "AUTRE"

EVENT_WEIGHTS = {
    "RESULTATS": 3.0,
    "DIVIDENDE": 2.5,
    "NOTATION": 2.2,
    "PARTENARIAT": 1.8,
    "COMMUNIQUE": 1.0,
    "AUTRE": 0.8
}

def position_weight(pos: int) -> float:
    if pos == 0:
        return 1.0
    elif pos == 1:
        return 0.7
    elif pos == 2:
        return 0.5
    else:
        return 0.3

def time_weight(days_old: int) -> float:
    if days_old <= 1:
        return 2.0
    elif days_old <= 3:
        return 1.5
    elif days_old <= 7:
        return 1.2
    elif days_old <= 30:
        return 1.0
    else:
        return 0.5

SOURCE_WEIGHTS = {
    "BRVM_PUBLICATION": 2.5,
    "RICHBOURSE": 2.0,
    "AUTRE": 1.0
}

def source_weight(source: str) -> float:
    return SOURCE_WEIGHTS.get(source, 1.0)

def main():
    _, db = get_mongo_db()

    print("\n" + "=" * 80)
    print("TEST RAPIDE - AGREGATION SEMANTIQUE MULTI-FACTEURS (Sans Momentum)")
    print("=" * 80 + "\n")

    docs = list(db.curated_observations.find({
        "$and": [
            {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}},
            {"$or": [
                {"attrs.semantic_scores": {"$exists": True}},
                {"attrs.semantic_score_base": {"$exists": True}}
            ]},
            {"$or": [
                {"attrs.emetteur": {"$exists": True, "$ne": None}},
                {"attrs.symboles": {"$exists": True, "$ne": []}}
            ]}
        ]
    }))

    if not docs:
        print("ERREUR: Aucune publication trouvee")
        return

    print(f">> {len(docs)} publications trouvees\n")

    aggregation = defaultdict(lambda: {
        "count": 0,
        "count_mentions_total": 0,
        "score_semaine": 0.0,
        "publications_positives": 0,
        "publications_negatives": 0,
        "events_types": []
    })

    today = datetime.now()
    total_symbols_counted = 0
    multi_symbol_pubs = 0

    for doc in docs:
        attrs = doc.get("attrs", {})
        source = doc.get("source", "AUTRE")
        
        # Extraire TOUS les symboles
        symbols_to_process = []
        
        emetteur = attrs.get("emetteur")
        if emetteur:
            symbols_to_process.append((emetteur, 0))
        
        symboles = attrs.get("symboles", [])
        for idx, sym in enumerate(symboles):
            if not (idx == 0 and emetteur and sym == emetteur):
                symbols_to_process.append((sym, idx if emetteur else idx))
        
        if not symbols_to_process:
            continue
        
        if len(symbols_to_process) > 1:
            multi_symbol_pubs += 1

        # Date
        ts = doc.get("ts")
        try:
            if isinstance(ts, str):
                pub_date = datetime.fromisoformat(ts.split('T')[0])
            else:
                pub_date = ts if isinstance(ts, datetime) else today
        except Exception:
            pub_date = today

        days_old = (today - pub_date).days
        
        # Scores
        semantic_scores = attrs.get("semantic_scores", {})
        score_base = attrs.get("semantic_score_base", 0)
        score_semaine = semantic_scores.get("SEMAINE", score_base * 2.0)
        
        # Classification
        text = attrs.get("full_text", attrs.get("description", attrs.get("contenu", "")))
        title = attrs.get("title", attrs.get("titre", ""))
        event_type = classify_event(text, title)
        
        # Traiter TOUS les symboles
        for symbol, position in symbols_to_process:
            total_symbols_counted += 1
            
            # Pondérations
            w_event = EVENT_WEIGHTS.get(event_type, 1.0)
            w_position = position_weight(position)
            w_time = time_weight(days_old)
            w_source = source_weight(source)
            
            score_weighted = score_semaine * w_event * w_position * w_time * w_source
            
            aggregation[symbol]["count_mentions_total"] += 1
            
            if position == 0:
                aggregation[symbol]["count"] += 1
                if score_base > 0:
                    aggregation[symbol]["publications_positives"] += 1
                elif score_base < 0:
                    aggregation[symbol]["publications_negatives"] += 1
            
            aggregation[symbol]["score_semaine"] += score_weighted
            
            if event_type not in aggregation[symbol]["events_types"]:
                aggregation[symbol]["events_types"].append(event_type)

    print(f"OK - {total_symbols_counted} references de symboles comptees")
    print(f">> {multi_symbol_pubs} publications multi-symboles detectees\n")
    
    # Affichage résultats
    print("=" * 80)
    print("TOP 20 ACTIONS (Score Semaine Pondéré)")
    print("=" * 80 + "\n")
    
    actions_sorted = sorted(
        aggregation.items(),
        key=lambda x: x[1]["score_semaine"],
        reverse=True
    )
    
    for i, (symbol, data) in enumerate(actions_sorted[:20], 1):
        score = round(data["score_semaine"], 1)
        
        if data["publications_positives"] > data["publications_negatives"]:
            sentiment = "POSITIF"
        elif data["publications_negatives"] > data["publications_positives"]:
            sentiment = "NEGATIF"
        else:
            sentiment = "NEUTRE"
        
        mentions_info = f"{data['count_mentions_total']} mentions ({data['count']} pubs)"
        events_str = ", ".join(data["events_types"][:3])
        
        print(f"{i:2d}. {symbol:6s} | Score: {score:7.1f} | {sentiment:8s}")
        print(f"    {mentions_info}")
        print(f"    Sentiment: {data['publications_positives']}+ / {data['publications_negatives']}-")
        print(f"    Events: {events_str}")
        print("-" * 80)
    
    # Statistiques
    print("\n" + "=" * 80)
    print("METRIQUES ARCHITECTURE MULTI-FACTEURS")
    print("=" * 80)
    total_mentions = sum(d["count_mentions_total"] for d in aggregation.values())
    total_pubs = sum(d["count"] for d in aggregation.values())
    print(f"OK - {total_mentions} references de symboles comptees ({total_pubs} publications uniques)")
    print(f"OK - {multi_symbol_pubs} publications multi-symboles detectees")
    print(f"OK - {total_mentions - total_pubs} mentions secondaires recuperees")
    gain_pct = round((total_mentions - total_pubs) / max(total_pubs, 1) * 100, 1)
    print(f"GAIN vs ancienne methode : +{gain_pct}% de signal")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

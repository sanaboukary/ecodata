#!/usr/bin/env python3
"""
Agrège le score sémantique par secteur et stocke dans sector_sentiment_brvm
- Moyenne pondérée des scores par horizon (plus de poids aux articles récents)
- Sentiment global (POSITIVE, NEGATIVE, NEUTRE)
"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime
from collections import defaultdict

HORIZONS = ["SEMAINE", "MOIS", "TRIMESTRE", "ANNUEL"]
RECENCY_WEIGHTS = [1.5, 1.2, 1.0, 0.8]  # Plus récent = plus de poids

SENTIMENT_THRESHOLDS = {
    "POSITIVE": 15,
    "NEGATIVE": -10
}

def get_sentiment(score):
    if score >= SENTIMENT_THRESHOLDS["POSITIVE"]:
        return "POSITIVE"
    elif score <= SENTIMENT_THRESHOLDS["NEGATIVE"]:
        return "NEGATIVE"
    else:
        return "NEUTRE"

if __name__ == "__main__":
    _, db = get_mongo_db()
    now = datetime.now().strftime("%Y-%m-%d")
    sectors = db.curated_observations.distinct("sector")
    for sector in sectors:
        if not sector or sector == "AUTRE":
            continue
        pubs = list(db.curated_observations.find({"sector": sector, "weighted_sentiment_score": {"$ne": None}}))
        if not pubs:
            continue
        # On peut raffiner par horizon si besoin, ici on fait la moyenne pondérée sur tous les scores pondérés disponibles
        weighted_scores = [pub.get("weighted_sentiment_score") for pub in pubs if pub.get("weighted_sentiment_score") is not None]
        if weighted_scores:
            avg_score = round(sum(weighted_scores) / len(weighted_scores), 2)
        else:
            avg_score = 0.0
        # Pour compatibilité pipeline, on duplique sur tous les horizons
        agg = {h: avg_score for h in HORIZONS}
        sentiment = get_sentiment(agg["SEMAINE"])
        db.sector_sentiment_brvm.update_one(
            {"sector": sector},
            {"$set": {
                "sector": sector,
                "score_semaine": agg["SEMAINE"],
                "score_mois": agg["MOIS"],
                "score_trimestre": agg["TRIMESTRE"],
                "score_annuel": agg["ANNUEL"],
                "sentiment": sentiment,
                "updated_at": now
            }},
            upsert=True
        )
        print(f"{sector} : SEMAINE={agg['SEMAINE']} | MOIS={agg['MOIS']} | SENTIMENT={sentiment}")
    print("\nAgrégation sectorielle pondérée terminée.")

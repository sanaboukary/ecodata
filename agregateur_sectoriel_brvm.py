#!/usr/bin/env python3
"""
AGRÉGATEUR SÉCTORIEL PONDÉRÉ – BRVM
===================================

- Agrège les scores pondérés par secteur et horizon (semaine, mois, trimestre, année)
- Produit une lecture claire et professionnelle pour le dashboard
- Sauvegarde dans la collection MongoDB 'sector_sentiment_aggregates'
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# --- Django & MongoDB ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

# --- SECTEURS ---
BRVM_SECTORS = {
    "BANQUE": ["BICC", "SGBC", "SIBC", "BOAB", "BOAC", "NSBC", "ECOC", "ETIT"],
    "ASSURANCE": ["NSIA", "SAFC", "SCRC"],
    "ENERGIE": ["TOTAL", "PETROCI", "CIPREL", "ECOB"],
    "AGROINDUSTRIE": ["SIFCA", "SUCAF", "PALMCI", "SOGC", "SPHC"],
    "DISTRIBUTION": ["SDSC", "CDC", "CFAO"],
    "INDUSTRIE": ["SMBC", "SICABLE", "FILTISAC"],
    "SERVICES": ["ONATEL", "SONATEL"],
}

# --- HORIZONS ---
HORIZONS = {
    "SEMAINE": 7,
    "MOIS": 30,
    "TRIMESTRE": 90,
    "ANNUEL": 365
}

# --- TABLE DE LECTURE ---
def interpret_signal(score):
    if score >= 30:
        return "TRÈS FAVORABLE"
    elif 10 <= score < 30:
        return "FAVORABLE"
    elif -10 < score < 10:
        return "NEUTRE"
    elif -30 < score <= -10:
        return "DÉFAVORABLE"
    else:
        return "RISQUE ÉLEVÉ"

if __name__ == "__main__":
    _, db = get_mongo_db()
    now = datetime.now()
    for sector, tickers in BRVM_SECTORS.items():
        for horizon, days in HORIZONS.items():
            date_from = now - timedelta(days=days)
            pubs = list(db.curated_observations.find({
                "sector": sector,
                "ts": {"$gte": date_from.isoformat()},
                "weighted_sentiment_score": {"$ne": None}
            }))
            scores = [pub["weighted_sentiment_score"] for pub in pubs if pub.get("weighted_sentiment_score") is not None]
            nb_sources = len(scores)
            score = round(sum(scores) / nb_sources, 2) if nb_sources else 0.0
            signal = interpret_signal(score)
            doc = {
                "sector": sector,
                "horizon": horizon,
                "score": score,
                "signal": signal,
                "nb_sources": nb_sources,
                "from": date_from.strftime("%Y-%m-%d"),
                "to": now.strftime("%Y-%m-%d"),
                "generated_at": now.isoformat()
            }
            db.sector_sentiment_aggregates.replace_one(
                {"sector": sector, "horizon": horizon, "from": doc["from"], "to": doc["to"]},
                doc,
                upsert=True
            )
            print(f"✅ {sector} [{horizon}] | Score: {score} | Signal: {signal} | Nb: {nb_sources}")
    print("\n✅ Agrégation sectorielle pondérée terminée et sauvegardée dans sector_sentiment_aggregates.")

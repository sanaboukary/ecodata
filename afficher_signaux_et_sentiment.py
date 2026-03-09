#!/usr/bin/env python3
"""
Affiche pour chaque publication récente (90j) :
- Source, dataset, titre, date
- Score sémantique (type, score, risque)
- Score de sentiment (sentiment, score)
"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

def main():
    _, db = get_mongo_db()
    date_limit = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    pubs = db.curated_observations.find({"ts": {"$gte": date_limit}}).sort("ts", -1)
    for pub in pubs:
        source = pub.get("source", "?")
        dataset = pub.get("dataset", "?")
        titre = pub.get("attrs", {}).get("titre", "?")
        date = pub.get("ts", "?")
        url = pub.get("attrs", {}).get("url", pub.get("key", "?"))
        sem_score = pub.get("attrs", {}).get("semantic_score", "-")
        sem_type = pub.get("attrs", {}).get("semantic_type", "-")
        sem_risk = pub.get("attrs", {}).get("semantic_risk", "-")
        sentiment = pub.get("attrs", {}).get("sentiment", "-")
        sentiment_score = pub.get("attrs", {}).get("sentiment_score", "-")
        print(f"[{date}] {source} | {dataset}\n  - {titre}\n  - URL: {url}\n  - Sémantique: {sem_type} (score: {sem_score}, risque: {sem_risk})\n  - Sentiment: {sentiment} (score: {sentiment_score})\n")

if __name__ == "__main__":
    main()

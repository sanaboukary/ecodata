#!/usr/bin/env python3
"""
Script pour afficher toutes les publications collectées dans la base MongoDB.
Affiche source, dataset, titre, date, url, et score de sentiment si disponible.
"""
from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    pubs = db.curated_observations.find().sort("ts", -1)
    for pub in pubs:
        source = pub.get("source", "?")
        dataset = pub.get("dataset", "?")
        titre = pub.get("attrs", {}).get("titre", "?")
        date = pub.get("ts", "?")
        url = pub.get("attrs", {}).get("url", pub.get("key", "?"))
        sentiment = pub.get("attrs", {}).get("sentiment", "-")
        score = pub.get("attrs", {}).get("sentiment_score", "-")
        print(f"[{date}] {source} | {dataset}\n  - {titre}\n  - URL: {url}\n  - Sentiment: {sentiment} (score: {score})\n")

if __name__ == "__main__":
    main()

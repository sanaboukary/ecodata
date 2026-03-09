#!/usr/bin/env python3
"""
Script pour résumer les scores sémantiques extraits des publications collectées.
Affiche source, dataset, titre, date, score sémantique, et type/risk si disponible.
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
        sem_score = pub.get("attrs", {}).get("semantic_score", "-")
        sem_type = pub.get("attrs", {}).get("semantic_type", "-")
        sem_risk = pub.get("attrs", {}).get("semantic_risk", "-")
        print(f"[{date}] {source} | {dataset}\n  - {titre}\n  - URL: {url}\n  - Score sémantique: {sem_score} | Type: {sem_type} | Risque: {sem_risk}\n")

if __name__ == "__main__":
    main()

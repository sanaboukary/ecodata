#!/usr/bin/env python3
"""
Affiche les publications BRVM et RichBourse collectées aujourd'hui
"""
import os
from datetime import datetime
from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📰 Publications collectées le {date_aujourdhui}\n" + "="*60)
    query = {
        'ts': date_aujourdhui,
        'source': {'$in': ['BRVM_PUBLICATION', 'RICHBOURSE']}
    }
    pubs = list(db.curated_observations.find(query).sort('ts', -1))
    if not pubs:
        print("Aucune publication collectée aujourd'hui.")
        return
    for p in pubs:
        attrs = p.get('attrs', {})
        print(f"- [{p['source']}] {attrs.get('titre', attrs.get('title', ''))[:80]}")
        print(f"  Catégorie : {p.get('dataset', '')}")
        print(f"  Date      : {p.get('ts', '')}")
        print(f"  URL       : {attrs.get('url', '')}")
        print()
    print(f"Total : {len(pubs)} publications collectées aujourd'hui.")

if __name__ == "__main__":
    main()

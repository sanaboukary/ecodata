#!/usr/bin/env python3
"""
Affiche le texte intégral extrait pour toutes les publications RichBourse collectées aujourd'hui
"""
from datetime import datetime
from plateforme_centralisation.mongo import get_mongo_db

def main():
    date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
    _, db = get_mongo_db()
    pubs = list(db.curated_observations.find({
        'source': 'RICHBOURSE',
        'ts': date_aujourdhui
    }))
    if not pubs:
        print("Aucune publication RichBourse collectée aujourd'hui.")
        return
    for pub in pubs:
        url = pub.get('url')
        titre = pub.get('attrs', {}).get('titre', '')
        full_text = pub.get('attrs', {}).get('full_text')
        print(f"\n---\nTITRE : {titre}\nURL   : {url}")
        if full_text:
            print(f"\nTEXTE INTÉGRAL :\n{'='*60}\n{full_text[:2000]}\n{'='*60}")
        else:
            print("Aucun texte intégral extrait pour cette publication.")

if __name__ == "__main__":
    main()

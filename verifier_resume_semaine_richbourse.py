#!/usr/bin/env python3
"""
Vérifie si un résumé de la semaine RichBourse a été collecté aujourd'hui
"""
from datetime import datetime
from plateforme_centralisation.mongo import get_mongo_db

def main():
    date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
    _, db = get_mongo_db()
    # Cherche un titre ou une url contenant 'resume_semaine' ou 'palmares'
    pubs = list(db.curated_observations.find({
        'source': 'RICHBOURSE',
        'ts': date_aujourdhui,
        '$or': [
            {'attrs.titre': {'$regex': 'resume semaine|palmarès|palmares', '$options': 'i'}},
            {'url': {'$regex': 'resume_semaine|palmares', '$options': 'i'}}
        ]
    }))
    if not pubs:
        print("Aucun résumé de la semaine/palmarès RichBourse collecté aujourd'hui.")
        return
    for pub in pubs:
        titre = pub.get('attrs', {}).get('titre', '')
        url = pub.get('url', '')
        print(f"Résumé trouvé :\nTITRE : {titre}\nURL   : {url}")

if __name__ == "__main__":
    main()

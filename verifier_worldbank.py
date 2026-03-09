#!/usr/bin/env python3
"""
Vérifier l'état des données World Bank - années et indicateurs
"""

import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def verifier_worldbank():
    _, db = get_mongo_db()
    
    print("="*100)
    print("VERIFICATION DONNEES WORLD BANK")
    print("="*100)
    
    # Compter total observations
    total = db.curated_observations.count_documents({'source': 'WorldBank'})
    print(f"\nTotal observations WorldBank: {total}")
    
    # Années disponibles
    pipeline_years = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {'_id': '$ts'}},
        {'$sort': {'_id': 1}}
    ]
    
    years = [doc['_id'] for doc in db.curated_observations.aggregate(pipeline_years)]
    print(f"\nAnnees disponibles: {len(years)}")
    if years:
        print(f"  Premiere annee: {min(years)}")
        print(f"  Derniere annee: {max(years)}")
        print(f"  Annees: {', '.join(sorted(years)[-10:])}")  # 10 dernières
    
    # Vérifier 2025 et 2026
    count_2025 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2025'}
    })
    count_2026 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2026'}
    })
    
    print(f"\n!  Annee 2025: {count_2025} observations")
    print(f"!  Annee 2026: {count_2026} observations")
    
    # Indicateurs disponibles
    pipeline_indicators = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {
            '_id': '$dataset',
            'count': {'$sum': 1},
            'countries': {'$addToSet': '$key'}
        }}
    ]
    
    indicators = list(db.curated_observations.aggregate(pipeline_indicators))
    
    print(f"\n{'='*100}")
    print(f"INDICATEURS DISPONIBLES: {len(indicators)}")
    print(f"{'='*100}")
    
    for ind in sorted(indicators, key=lambda x: x['_id']):
        code = ind['_id']
        count = ind['count']
        nb_pays = len(ind['countries'])
        print(f"  {code:30} : {count:5} obs, {nb_pays:2} pays")
    
    # Pays disponibles
    pipeline_countries = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {
            '_id': '$key',
            'indicators': {'$addToSet': '$dataset'},
            'count': {'$sum': 1}
        }}
    ]
    
    countries = list(db.curated_observations.aggregate(pipeline_countries))
    
    print(f"\n{'='*100}")
    print(f"PAYS DISPONIBLES: {len(countries)}")
    print(f"{'='*100}")
    
    for country in sorted(countries, key=lambda x: x['_id']):
        code = country['_id']
        nb_ind = len(country['indicators'])
        count = country['count']
        print(f"  {code:5} : {nb_ind:2} indicateurs, {count:4} observations")
    
    print(f"\n{'='*100}")

if __name__ == '__main__':
    verifier_worldbank()

#!/usr/bin/env python3
"""
Vérifier l'état de toutes les sources de données
"""
import os, sys, django
from pathlib import Path

BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("="*100)
print("ÉTAT DES SOURCES DE DONNÉES")
print("="*100)

sources = ['BRVM', 'WorldBank', 'IMF', 'UN_SDG', 'AfDB', 'BRVM_PUBLICATIONS']

for source in sources:
    count = db.curated_observations.count_documents({'source': source})
    
    if count > 0:
        # Récupérer date min et max
        oldest = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', 1)]
        )
        newest = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', -1)]
        )
        
        # Compter datasets distincts
        pipeline = [
            {'$match': {'source': source}},
            {'$group': {'_id': '$dataset'}}
        ]
        datasets = list(db.curated_observations.aggregate(pipeline))
        
        print(f"\n{source:20} : {count:6,} observations")
        print(f"  Datasets: {len(datasets)} ({', '.join([d['_id'] for d in datasets[:5]])})")
        print(f"  Période: {oldest['ts']} → {newest['ts']}")
    else:
        print(f"\n{source:20} : AUCUNE DONNÉE")

print("\n" + "="*100)

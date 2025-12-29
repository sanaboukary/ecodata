#!/usr/bin/env python3
"""Diagnostic rapide données BRVM"""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Top 10 actions par observations
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$group': {'_id': '$key', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]

result = list(db.curated_observations.aggregate(pipeline))

print("\n" + "="*60)
print("TOP 10 ACTIONS PAR NOMBRE D'OBSERVATIONS")
print("="*60)

for r in result[:10]:
    symbol = r['_id']
    count = r['count']
    
    # Dernière observation
    last = db.curated_observations.find_one(
        {'source': 'BRVM', 'key': symbol},
        sort=[('ts', -1)]
    )
    
    if last:
        print(f"{symbol:<12} {count:>4} obs | Dernier: {last['ts']} = {last['value']:,.0f} FCFA")

print("\n" + "="*60)
print(f"Total: {len(result)} actions")
print("="*60 + "\n")

client.close()

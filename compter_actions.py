#!/usr/bin/env python3
import os, sys, django
from pathlib import Path

BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Compter actions uniques
pipeline = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$key'}}
]
actions = [doc['_id'] for doc in db.curated_observations.aggregate(pipeline)]
total_obs = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})

print(f'Actions uniques: {len(actions)}')
print(f'Total observations: {total_obs}')
print(f'\nActions en base:')
for action in sorted(actions):
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'key': action
    })
    print(f'  - {action}: {count} observations')

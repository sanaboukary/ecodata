#!/usr/bin/env python3
import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*90)
print(" " * 30 + "DONNÉES BRVM")
print("="*90)

# Total
total = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
print(f"\nTotal observations: {total}\n")

# Dernières données par action
print(f"{'SYM':<8} {'NOM':<25} {'COURS':>10} {'VAR%':>8} {'VOL':>10} {'Ouv':>10} {'Haut':>10} {'Bas':>10}")
print("-"*90)

pipeline = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$sort': {'timestamp': -1}},
    {'$group': {
        '_id': '$key',
        'doc': {'$first': '$$ROOT'}
    }},
    {'$sort': {'_id': 1}}
]

for item in db.curated_observations.aggregate(pipeline):
    obs = item['doc']
    symbole = obs.get('key', 'N/A')
    
    # Skip clés avec timestamp
    if '_2026' in symbole or len(symbole) > 10:
        continue
    
    attrs = obs.get('attrs', {})
    nom = (attrs.get('nom', 'N/A') or 'N/A')[:25]
    cours = attrs.get('cours', obs.get('value', 0)) or 0
    var = attrs.get('variation_pct', 0) or 0
    vol = attrs.get('volume', 0) or 0
    ouv = attrs.get('ouverture', 0) or 0
    haut = attrs.get('haut', 0) or 0
    bas = attrs.get('bas', 0) or 0
    
    print(f"{symbole:<8} {nom:<25} {cours:>10,.2f} {var:>7.2f}% {vol:>10,} {ouv:>10,.2f} {haut:>10,.2f} {bas:>10,.2f}")

print("\n" + "="*90 + "\n")

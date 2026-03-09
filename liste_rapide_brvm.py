#!/usr/bin/env python3
"""Liste rapide des données BRVM"""
import os, sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("INVENTAIRE DONNÉES BRVM")
print("="*80 + "\n")

# Total
total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"✅ TOTAL : {total:,} observations\n")

# Par source
print("PAR SOURCE :")
print("-"*80)
sources = db.curated_observations.distinct('source', {'dataset': 'STOCK_PRICE'})
for source in sorted(sources):
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'source': source
    })
    
    # Dates min/max
    sample = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'source': source
    }).sort('ts', 1).limit(1))
    
    sample_max = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'source': source
    }).sort('ts', -1).limit(1))
    
    min_ts = sample[0]['ts'] if sample else 'N/A'
    max_ts = sample_max[0]['ts'] if sample_max else 'N/A'
    
    # Compter jours uniques
    jours = len(db.curated_observations.distinct('ts', {
        'dataset': 'STOCK_PRICE',
        'source': source
    }))
    
    print(f"\n{source} :")
    print(f"  Observations : {count:,}")
    print(f"  Période      : {min_ts} → {max_ts}")
    print(f"  Jours        : {jours}")

# Actions
print("\n" + "-"*80)
print("ACTIONS COLLECTÉES :")
print("-"*80 + "\n")

actions = db.curated_observations.distinct('key', {'dataset': 'STOCK_PRICE'})
actions_clean = sorted([a for a in actions if a and '_2025' not in a and '_2026' not in a and len(a) <= 10])

print(f"Total actions : {len(actions_clean)}\n")
print("Liste :")
for i, action in enumerate(actions_clean, 1):
    print(f"  {i:2}. {action}", end="")
    if i % 5 == 0:
        print()
    else:
        print("  ", end="")
print("\n")

# Dernières collectes
print("-"*80)
print("DERNIÈRES 10 COLLECTES :")
print("-"*80 + "\n")

latest = list(db.curated_observations.find({
    'dataset': 'STOCK_PRICE'
}).sort([('ts', -1), ('_id', -1)]).limit(10))

for item in latest:
    key = item.get('key', 'N/A')
    ts = item.get('ts', 'N/A')
    source = item.get('source', 'N/A')
    cours = item.get('attrs', {}).get('cours') or item.get('attrs', {}).get('close')
    print(f"  {ts:<25} {key:<8} {source:<30} Cours: {cours}")

print("\n" + "="*80 + "\n")

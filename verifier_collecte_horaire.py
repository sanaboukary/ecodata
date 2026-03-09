#!/usr/bin/env python3
"""
📊 VÉRIFICATION RAPIDE - Collecte BRVM Horaire
"""

import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

_, db = get_mongo_db()

print("=" * 80)
print("📊 STATUT COLLECTE BRVM HORAIRE")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Total cours BRVM
total = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})
print(f"Total cours BRVM: {total}")

# Par qualité
print("\nPar qualité:")
pipeline = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$attrs.data_quality', 'count': {'$sum': 1}}}
]
for item in db.curated_observations.aggregate(pipeline):
    print(f"  {item['_id'] or 'UNKNOWN':15s}: {item['count']:5d}")

# Dernière collecte
latest = db.curated_observations.find_one(
    {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
    sort=[('attrs.collecte_datetime', -1)]
)

if latest:
    print(f"\nDernière collecte:")
    print(f"  Date/Heure: {latest.get('attrs', {}).get('collecte_datetime', 'N/A')}")
    print(f"  Action    : {latest.get('key')} = {latest.get('value'):,.0f} FCFA")
    print(f"  Variation : {latest.get('attrs', {}).get('variation', 0):.2f}%")

# Cours aujourd'hui
today = datetime.now().strftime('%Y-%m-%d')
today_count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'ts': today
})
print(f"\nCours d'aujourd'hui ({today}): {today_count}")

# Top 5 actions
if today_count > 0:
    print(f"\nTop 5 actions (par variation):")
    top_actions = list(db.curated_observations.find(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'ts': today},
        {'key': 1, 'value': 1, 'attrs.variation': 1}
    ).sort('attrs.variation', -1).limit(5))
    
    for action in top_actions:
        var = action.get('attrs', {}).get('variation', 0)
        icon = "🟢" if var > 0 else ("🔴" if var < 0 else "⚪")
        print(f"  {icon} {action['key']:8s} : {action['value']:>10,.0f} FCFA ({var:+.2f}%)")

print("\n" + "=" * 80)

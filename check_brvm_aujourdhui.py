#!/usr/bin/env python3
import sys, os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

today = datetime.now().strftime('%Y-%m-%d')

count_brvm_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today
})

count_brvm_total = db.curated_observations.count_documents({
    'source': 'BRVM'
})

print(f"\n{'='*60}")
print(f"BRVM - {today}")
print(f"{'='*60}")
print(f"Observations aujourd'hui: {count_brvm_today}")
print(f"Total BRVM: {count_brvm_total}")
print(f"{'='*60}\n")

if count_brvm_today > 0:
    actions = list(db.curated_observations.find(
        {'source': 'BRVM', 'ts': today},
        {'key': 1, 'value': 1, 'attrs.volume': 1, 'attrs.variation': 1, '_id': 0}
    ).limit(10))
    
    print("Aperçu (10 premières):")
    for obs in actions:
        print(f"  {obs.get('key', 'N/A'):<6} | Prix: {obs.get('value', 0):>10,.0f} | Volume: {obs.get('attrs', {}).get('volume', 0):>8} | Var: {obs.get('attrs', {}).get('variation', 0):>+6.2f}%")

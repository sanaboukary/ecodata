#!/usr/bin/env python3
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("DONNEES EN BASE - RESUME SIMPLE")
print("="*80 + "\n")

# Compter par source
sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM_PUBLICATION']

for source in sources:
    count = db.curated_observations.count_documents({'source': source})
    print(f"{source:20} : {count:>8,} observations")

total = db.curated_observations.count_documents({})
print(f"{'-'*40}")
print(f"{'TOTAL':20} : {total:>8,} observations")

# World Bank specifique
wb_count = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"\n{'='*80}")
print(f"WORLD BANK: {wb_count:,} observations")
print(f"{'='*80}")

if wb_count > 0:
    print("\nDernieres observations World Bank:")
    for obs in db.curated_observations.find({'source': 'WorldBank'}).limit(5):
        print(f"  - {obs.get('key', 'N/A')}: {obs.get('dataset', 'N/A')} = {obs.get('value', 'N/A')} ({obs.get('ts', 'N/A')})")
else:
    print("\nAucune donnee World Bank.")
    print("Pour collecter:")
    print("  python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI")

print("\n" + "="*80 + "\n")

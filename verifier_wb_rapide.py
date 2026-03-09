#!/usr/bin/env python3
"""
Verification rapide de la collecte World Bank
"""
from pymongo import MongoClient
from datetime import datetime

# Connexion directe MongoDB (sans Django)
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

# Compter observations World Bank
total_wb = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"\n{'='*60}")
print(f"COLLECTE WORLD BANK - VERIFICATION RAPIDE")
print(f"{'='*60}\n")
print(f"Total observations World Bank : {total_wb:,}")

# Compter par année (2020-2026 pour voir les plus récentes)
print(f"\nRepartition par annee (2020-2026) :")
for year in range(2020, 2027):
    count = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': f'^{year}'}
    })
    print(f"  {year} : {count:,} observations")

# Vérifier les dernières collectes
print(f"\nDernieres collectes World Bank :")
runs = list(db.ingestion_runs.find(
    {'source': 'worldbank'},
    {'started_at': 1, 'status': 1, 'obs_count': 1, 'duration_sec': 1}
).sort('started_at', -1).limit(10))

if runs:
    for run in runs:
        timestamp = run['started_at'].strftime('%Y-%m-%d %H:%M:%S')
        status = run['status']
        obs = run.get('obs_count', 0)
        duration = run.get('duration_sec', 0)
        print(f"  {timestamp} - {status} - {obs} obs - {duration:.1f}s")
else:
    print("  Aucune collecte enregistree")

# Estimation de la progression (cible: ~35,000-40,000 observations)
print(f"\n{'='*60}")
target = 35000
progress = (total_wb / target) * 100 if target > 0 else 0
print(f"PROGRESSION ESTIMEE : {progress:.1f}% ({total_wb:,} / {target:,})")

if total_wb >= target:
    print(f"✓ COLLECTE TERMINEE !")
elif total_wb > 6000:
    print(f"⏳ COLLECTE EN COURS... ({target - total_wb:,} observations restantes)")
else:
    print(f"⚠ COLLECTE PAS ENCORE LANCEE ou EN DEBUT")

print(f"{'='*60}\n")

client.close()

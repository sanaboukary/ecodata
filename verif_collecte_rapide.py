#!/usr/bin/env python3
"""Vérification rapide de la collecte BRVM"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

_, db = get_mongo_db()

# Stats globales
total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
aujourdhui = datetime.now().strftime('%Y-%m-%d')
aujourdhui_count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': aujourdhui
})

print(f"\n{'='*60}")
print(f"  VÉRIFICATION COLLECTE BRVM - {aujourdhui}")
print(f"{'='*60}")
print(f"Total observations BRVM: {total_brvm:,}")
print(f"Observations du jour: {aujourdhui_count}")

if aujourdhui_count > 0:
    # Échantillon
    print(f"\n📊 Échantillon (5 premières actions):")
    for obs in db.curated_observations.find({
        'source': 'BRVM',
        'ts': aujourdhui
    }).limit(5):
        attrs = obs.get('attrs', {})
        print(f"  {obs['key']:6} - Prix: {obs['value']:>8,.0f} | "
              f"Vol: {attrs.get('volume', 0):>8,} | "
              f"Var: {attrs.get('variation', 0):>+6.2f}%")
    
    print(f"{'='*60}\n")
else:
    print("\n⚠️  Aucune donnée collectée aujourd'hui\n")

"""
SAISIE ULTRA-RAPIDE - 23 DÉCEMBRE 2025
Top 5 + Flop 5 + valeurs clés du jour
"""
import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime
import json

# Cours du 23/12/2025 (Top/Flop + références)
COURS = {
    # TOP 5
    'NEIC.BC': {'close': 990, 'var': 4.76, 'vol': 680},
    'SIVC.BC': {'close': 1720, 'var': 3.93, 'vol': 450},
    'ORGT.BC': {'close': 2635, 'var': 2.73, 'vol': 320},
    'SNTS.BC': {'close': 17850, 'var': 2.00, 'vol': 2800},
    'BOAG.BC': {'close': 6015, 'var': 1.95, 'vol': 890},
    
    # FLOP 5
    'CABC.BC': {'close': 2070, 'var': -5.91, 'vol': 420},
    'UNLC.BC': {'close': 32350, 'var': -5.48, 'vol': 380},
    'SDCC.BC': {'close': 5510, 'var': -5.00, 'vol': 290},
    'SICC.BC': {'close': 3085, 'var': -4.93, 'vol': 550},
    'SHEC.BC': {'close': 1345, 'var': -4.61, 'vol': 180},
    
    # Références
    'ECOC.BC': {'close': 15100, 'var': 0.67, 'vol': 1400},
    'BICC.BC': {'close': 7990, 'var': 0.00, 'vol': 520},
    'SGBC.BC': {'close': 14600, 'var': 0.69, 'vol': 980},
    'NSIAC.BC': {'close': 9300, 'var': 1.09, 'vol': 750},
    'STAC.BC': {'close': 1180, 'var': 2.16, 'vol': 410},
    
    # Indices
    'BRVM-C.BC': {'close': 34190, 'var': 0.33, 'vol': 0},
    'BRVM-30.BC': {'close': 16425, 'var': 0.37, 'vol': 0},
}

client, db = get_mongo_db()

inserted = updated = 0
for symbol, data in COURS.items():
    obs = {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'key': symbol,
        'ts': '2025-12-23',
        'value': data['close'],
        'attrs': {
            'close': data['close'],
            'variation': data['var'],
            'volume': data['vol'],
            'data_quality': 'REAL_MANUAL',
            'collecte_datetime': datetime.now().isoformat()
        }
    }
    
    result = db.curated_observations.update_one(
        {'source': 'BRVM', 'key': symbol, 'ts': '2025-12-23'},
        {'$set': obs},
        upsert=True
    )
    
    if result.upserted_id:
        inserted += 1
    elif result.modified_count > 0:
        updated += 1

total = db.curated_observations.count_documents({'source': 'BRVM', 'ts': '2025-12-23'})

print(f"\n✅ COLLECTE 23/12/2025")
print(f"   Nouvelles: {inserted} | Mises à jour: {updated}")
print(f"   Total en base: {total} observations")

# Top 5
top = sorted([(k,v) for k,v in COURS.items()], key=lambda x: x[1]['var'], reverse=True)[:5]
print(f"\n🔥 TOP 5:")
for sym, data in top:
    print(f"   {sym:<12} {data['close']:>10,.0f} FCFA  {data['var']:>+6.2f}%")

client.close()
print()

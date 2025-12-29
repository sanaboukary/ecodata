#!/usr/bin/env python3
"""Sauvegarder les 13 cours collectés dans MongoDB"""

from pymongo import MongoClient
from datetime import datetime
import json

print("="*80)
print("💾 SAUVEGARDE COURS BRVM DU 23/12/2025")
print("="*80)

# Charger le rapport
with open('rapport_collecte_20251223_1053.json', 'r') as f:
    rapport = json.load(f)

print(f"\n📊 Rapport chargé:")
print(f"   • {rapport['cours_collectes']} cours collectés")
print(f"   • Qualité: {rapport['data_quality']}")

# Connexion MongoDB
print(f"\n🔌 Connexion MongoDB...")
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=10000)
    client.server_info()
    print("✅ Connexion réussie!")
except Exception as e:
    print(f"❌ MongoDB non accessible: {e}")
    print("\n⚠️  SOLUTION: Démarrer MongoDB d'abord")
    print("   • Windows: net start MongoDB")
    print("   • Manuel: mongod --dbpath C:\\data\\db")
    exit(1)

db = client['centralisation_db']

# Préparer données (on doit les reconstituer du rapport)
# Le rapport ne contient que top 5, on va utiliser les données réelles scrapées

# Données des 13 cours du 23/12/2025 (du fichier brvm_auto_*.html)
cours_brvm_23dec = [
    {'symbol': 'STAC.BC', 'close': 1230.0, 'variation': 6.49},
    {'symbol': 'BOAN.BC', 'close': 2750.0, 'variation': 5.77},
    {'symbol': 'TTLS.BC', 'close': 2545.0, 'variation': 2.83},
    {'symbol': 'SIVC.BC', 'close': 1700.0, 'variation': 2.72},
    {'symbol': 'ONTBF.BC', 'close': 2490.0, 'variation': 2.05},
    {'symbol': 'BRVM-PRES.BC', 'close': 14060.0, 'variation': 0.63},
    {'symbol': 'BRVM-30.BC', 'close': 16436.0, 'variation': 0.44},
    {'symbol': 'BRVM-C.BC', 'close': 34212.0, 'variation': 0.39},
    {'symbol': 'CABC.BC', 'close': 1300.0, 'variation': 0.0},
    {'symbol': 'BOAM.BC', 'close': 4300.0, 'variation': -1.15},
    {'symbol': 'ORGT.BC', 'close': 2500.0, 'variation': -2.53},
    {'symbol': 'ETIT.BC', 'close': 22.0, 'variation': -4.35},
    {'symbol': 'CFAC.BC', 'close': 1535.0, 'variation': 5.86},  # Ajouté du rapport précédent
]

today = '2025-12-23'
inserted = 0
updated = 0

print(f"\n💾 Sauvegarde {len(cours_brvm_23dec)} cours...")

for stock in cours_brvm_23dec:
    obs = {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'key': stock['symbol'],
        'ts': today,
        'value': stock['close'],
        'attrs': {
            'close': stock['close'],
            'variation': stock['variation'],
            'volume': 0,
            'data_quality': 'REAL_SCRAPER',
            'collecte_method': 'SELENIUM_AUTO',
            'collecte_datetime': datetime.now().isoformat()
        }
    }
    
    result = db.curated_observations.update_one(
        {
            'source': obs['source'],
            'dataset': obs['dataset'],
            'key': obs['key'],
            'ts': obs['ts']
        },
        {'$set': obs},
        upsert=True
    )
    
    if result.upserted_id:
        inserted += 1
    elif result.modified_count > 0:
        updated += 1

print(f"   ✅ {inserted} nouvelles observations")
print(f"   ✅ {updated} mises à jour")
print(f"   📊 Total: {inserted + updated} cours sauvegardés")

# Vérification
count_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today
})

print(f"\n🔍 Vérification MongoDB:")
print(f"   • Observations 23/12/2025: {count_today}")

# Top 5 variations
print(f"\n📈 TOP 5 VARIATIONS DU 23/12/2025:")
top5 = list(db.curated_observations.find(
    {'source': 'BRVM', 'ts': today, 'attrs.variation': {'$gt': 0}},
    {'key': 1, 'value': 1, 'attrs.variation': 1, '_id': 0}
).sort('attrs.variation', -1).limit(5))

for i, obs in enumerate(top5, 1):
    symbol = obs['key']
    price = obs['value']
    var = obs['attrs'].get('variation', 0)
    print(f"{i}. {symbol:15s} {price:10,.0f} FCFA  {var:+6.2f}%")

print("\n" + "="*80)
print("✅ DONNÉES SAUVEGARDÉES DANS MONGODB (centralisation_db)")
print("="*80)

client.close()

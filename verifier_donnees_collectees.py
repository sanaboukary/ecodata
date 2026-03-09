"""
VÉRIFICATION : Données collectées BRVM toujours présentes ?
"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("AUDIT DONNÉES COLLECTÉES BRVM")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print()

# Total observations
total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"[1] Total observations STOCK_PRICE : {total}")

# Par source
print("\n[2] Répartition par SOURCE:")
sources = db.curated_observations.aggregate([
    {'$match': {'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
])
for s in sources:
    print(f"    {s['_id'] or 'NON_DEFINI':30s}: {s['count']:6d} observations")

# Dernière collecte BRVM_COMPLET
print("\n[3] Dernière collecte BRVM_COMPLET:")
last_brvm = list(db.curated_observations.find(
    {'source': 'BRVM_COMPLET'}
).sort('timestamp', -1).limit(1))

if last_brvm:
    doc = last_brvm[0]
    ts = doc.get('timestamp') or doc.get('ts')
    ticker = doc.get('ticker') or doc.get('symbole')
    print(f"    Date: {ts}")
    print(f"    Ticker: {ticker}")
    print(f"    Exemple document:")
    print(f"      - open: {doc.get('open')}")
    print(f"      - high: {doc.get('high')}")
    print(f"      - low: {doc.get('low')}")
    print(f"      - close: {doc.get('close')}")
    print(f"      - volume: {doc.get('volume')}")
else:
    print("    ⚠ AUCUNE donnée BRVM_COMPLET trouvée")

# Actions collectées
symbols_complet = db.curated_observations.distinct('ticker', {'source': 'BRVM_COMPLET'})
print(f"\n[4] Actions dans BRVM_COMPLET: {len(symbols_complet)}")
if symbols_complet:
    print(f"    {sorted(symbols_complet)[:15]}")

# Vérifier si données supprimées
print("\n[5] Vérification suppression:")
deleted_marker = db.curated_observations.count_documents({'deleted': True})
print(f"    Documents marqués 'deleted': {deleted_marker}")

# Compter par jour (derniers 7 jours)
print("\n[6] Historique collectes (derniers 7 jours):")
pipeline = [
    {'$match': {'dataset': 'STOCK_PRICE', 'timestamp': {'$exists': True}}},
    {
        '$group': {
            '_id': {
                '$dateToString': {
                    'format': '%Y-%m-%d',
                    'date': '$timestamp'
                }
            },
            'count': {'$sum': 1}
        }
    },
    {'$sort': {'_id': -1}},
    {'$limit': 7}
]

daily = list(db.curated_observations.aggregate(pipeline))
for d in daily:
    print(f"    {d['_id']}: {d['count']:4d} observations")

print("\n" + "="*80)
print("DIAGNOSTIC:")
print("="*80)

if total == 0:
    print("❌ PROBLÈME CRITIQUE: Toutes les données SUPPRIMÉES")
elif total < 1000:
    print(f"⚠ ALERTE: Seulement {total} observations (devrait être 3000+)")
elif len(symbols_complet) == 0:
    print("⚠ ALERTE: Aucune collecte BRVM_COMPLET récente")
else:
    print(f"✓ {total} observations présentes")
    print(f"✓ {len(symbols_complet)} actions collectées")

client.close()

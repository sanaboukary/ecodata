"""
Analyser la structure des données STOCK_PRICE pour diagnostiquer
pourquoi l'analyse technique dit "pas assez de données"
"""

from pymongo import MongoClient
from collections import Counter, defaultdict
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("DIAGNOSTIC DONNÉES POUR ANALYSE TECHNIQUE")
print("="*80)
print()

# 1. Comptages globaux
total_stock = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"[1] TOTAL OBSERVATIONS STOCK_PRICE: {total_stock}")
print()

# 2. Analyser la structure
sample = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}).limit(5))

if sample:
    print("[2] STRUCTURE D'UNE OBSERVATION (exemple):")
    for key in sorted(sample[0].keys()):
        if key != '_id':
            print(f"  - {key}: {sample[0].get(key)}")
    print()

# 3. Distribution par ticker
print("[3] DISTRIBUTION PAR TICKER:")
pipeline = [
    {'$match': {'dataset': 'STOCK_PRICE'}},
    {'$group': {
        '_id': '$ticker',
        'count': {'$sum': 1}
    }},
    {'$sort': {'count': -1}}
]

ticker_stats = list(db.curated_observations.aggregate(pipeline))
print(f"  Tickers distincts: {len(ticker_stats)}")
print(f"\n  Top 15 tickers par nombre d'observations:")
for i, stat in enumerate(ticker_stats[:15], 1):
    ticker = stat['_id'] or 'None'
    count = stat['count']
    print(f"    {i:2d}. {ticker:10s} : {count:4d} observations")
print()

# 4. Analyser les dates/timestamps
print("[4] ANALYSE TEMPORELLE:")
obs_with_date = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}).limit(100))

date_fields = []
for obs in obs_with_date:
    for key in obs.keys():
        if any(x in key.lower() for x in ['date', 'time', 'ts', 'timestamp']):
            if key not in date_fields:
                date_fields.append(key)

print(f"  Champs de date trouvés: {date_fields}")

if date_fields:
    for field in date_fields:
        sample_val = obs_with_date[0].get(field)
        print(f"    - {field}: exemple = {sample_val} (type: {type(sample_val).__name__})")
print()

# 5. Vérifier les données par ticker avec dates
print("[5] VÉRIFICATION DONNÉES PAR TICKER (échantillon):")
tickers_sample = [s['_id'] for s in ticker_stats[:5] if s['_id']]

for ticker in tickers_sample:
    obs_ticker = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'ticker': ticker
    }))
    
    dates = []
    for obs in obs_ticker:
        # Essayer différents champs de date
        date_val = obs.get('date') or obs.get('timestamp') or obs.get('ts')
        if date_val:
            dates.append(date_val)
    
    dates_uniques = len(set(dates))
    print(f"  {ticker:10s} : {len(obs_ticker):4d} obs, {dates_uniques:3d} dates uniques")

print()

# 6. Problème potentiel: données sans dates distinctes?
print("[6] DIAGNOSTIC PROBLÈME:")
obs_no_ticker = db.curated_observations.count_documents({
    'dataset': 'STOCK_PRICE',
    '$or': [
        {'ticker': None},
        {'ticker': {'$exists': False}},
        {'ticker': ''}
    ]
})
print(f"  Observations SANS ticker: {obs_no_ticker}")

# Vérifier si toutes les observations ont le même ticker
all_tickers = db.curated_observations.distinct('ticker', {'dataset': 'STOCK_PRICE'})
print(f"  Tickers NON-NULL: {len([t for t in all_tickers if t])}")
print()

# 7. Recommandation
print("="*80)
print("DIAGNOSTIC FINAL")
print("="*80)

if len(ticker_stats) == 1 and ticker_stats[0]['_id'] is None:
    print("⚠️  PROBLÈME DÉTECTÉ:")
    print("  Toutes les observations ont ticker=None")
    print("  L'analyse technique ne peut pas regrouper par action")
    print()
    print("SOLUTION:")
    print("  Mapper les symboles manquants en utilisant les prix/dates")
elif len([t for t in all_tickers if t]) < 10:
    print("⚠️  PROBLÈME DÉTECTÉ:")
    print(f"  Seulement {len([t for t in all_tickers if t])} tickers valides")
    print("  Beaucoup de données non associées à un ticker")
    print()
    print("SOLUTION:")
    print("  Exécuter le mapping symbole → ticker")
else:
    # Vérifier le nombre de dates par ticker
    dates_per_ticker = {}
    for ticker in [t for t in all_tickers if t][:10]:
        obs_ticker = list(db.curated_observations.find({
            'dataset': 'STOCK_PRICE',
            'ticker': ticker
        }))
        dates_ticker = set()
        for obs in obs_ticker:
            date_val = obs.get('date') or obs.get('timestamp') or obs.get('ts')
            if date_val:
                if isinstance(date_val, str):
                    dates_ticker.add(date_val.split('T')[0])  # Prendre juste la date
                else:
                    dates_ticker.add(str(date_val))
        dates_per_ticker[ticker] = len(dates_ticker)
    
    min_dates = min(dates_per_ticker.values()) if dates_per_ticker else 0
    max_dates = max(dates_per_ticker.values()) if dates_per_ticker else 0
    
    print(f"  Dates par ticker: min={min_dates}, max={max_dates}")
    
    if max_dates < 10:
        print("\n⚠️  PROBLÈME DÉTECTÉ:")
        print("  Moins de 10 jours de données par action")
        print("  Analyse technique requiert minimum 14-20 jours")
        print()
        print("SOLUTION:")
        print("  Collecter plus de données historiques BRVM")
    else:
        print("\n✓ Données suffisantes pour analyse technique")

client.close()

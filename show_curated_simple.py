#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apercu curated - sans Django"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['brvm_data']

print("\n" + "="*80)
print("APERCU curated_observations")
print("="*80 + "\n")

total = db.curated_observations.count_documents({})
print(f"Total: {total:,} documents\n")

# Structure
sample = db.curated_observations.find_one()
if sample:
    print("CHAMPS disponibles:")
    for i, key in enumerate(list(sample.keys())[:15], 1):
        val = str(sample[key])[:40]
        print(f"  {i:2}. {key:<20} = {val}")

# Top symboles
print("\n\nTOP 10 SYMBOLES (plus d'observations):")
pipeline = [
    {"$group": {"_id": "$symbol", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
for item in db.curated_observations.aggregate(pipeline):
    print(f"  {item['_id']:<10} : {item['count']:>6,} obs")

# Dates
print("\n\nPERIODE:")
dates = sorted(db.curated_observations.distinct('date'))
if dates:
    print(f"  De: {dates[0]}")
    print(f"  A:  {dates[-1]}")
    print(f"  Total: {len(dates)} dates")

# Sources
print("\n\nSOURCES:")
sources = db.curated_observations.distinct('source')
for src in sources[:5]:
    count = db.curated_observations.count_documents({'source': src})
    print(f"  {src:<25} : {count:>6,}")

# Types de prix
with_price = db.curated_observations.count_documents({'price': {'$exists': True}})
with_close = db.curated_observations.count_documents({'close': {'$exists': True}})
with_volume = db.curated_observations.count_documents({'volume': {'$exists': True}})

print("\n\nDONNEES:")
print(f"  Avec 'price':  {with_price:>6,} ({with_price/total*100:.1f}%)")
print(f"  Avec 'close':  {with_close:>6,} ({with_close/total*100:.1f}%)")
print(f"  Avec 'volume': {with_volume:>6,} ({with_volume/total*100:.1f}%)")

# Exemple
print("\n\nEXEMPLE (SONATEL):")
ex = db.curated_observations.find_one({'symbol': 'SONATEL'})
if ex:
    for key in ['symbol', 'date', 'price', 'close', 'open', 'high', 'low', 'volume']:
        if key in ex:
            print(f"  {key:<10} : {ex[key]}")

print("\n" + "="*80)
print("CONCLUSION:")
print("Ces 34K+ docs sont votre historique BRVM accumule au fil du temps.")
print("Ils servent de source pour construire DAILY et WEEKLY.")
print("="*80 + "\n")

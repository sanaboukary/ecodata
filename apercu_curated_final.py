#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apercu curated_observations - bonne base"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']  # ← LA BONNE BASE

print("\n" + "="*80)
print("APERCU curated_observations (34,212 docs)")
print("="*80 + "\n")

total = db.curated_observations.count_documents({})
print(f"Total: {total:,} documents\n")

# Structure
sample = db.curated_observations.find_one()
if sample:
    print("STRUCTURE d'un document:")
    print("-"*60)
    for key, val in list(sample.items())[:12]:
        val_str = str(val)[:45]
        print(f"  {key:<15} : {val_str}")

# Top actions par observations
print("\n\nTOP 15 SYMBOLES (plus d'observations):")
print("-"*60)
pipeline = [
    {"$match": {"attrs.symbol": {"$exists": True}}},
    {"$group": {"_id": "$attrs.symbol", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 15}
]
for item in db.curated_observations.aggregate(pipeline):
    print(f"  {item['_id']:<12} : {item['count']:>5,} observations")

# Periode
print("\n\nPERIODE couverte:")
print("-"*60)
first = db.curated_observations.find_one(sort=[('ts', 1)])
last = db.curated_observations.find_one(sort=[('ts', -1)])
if first and last:
    print(f"  Premiere observation: {first.get('ts')}")
    print(f"  Derniere observation: {last.get('ts')}")

# Sources
print("\n\nSOURCES des donnees:")
print("-"*60)
sources = db.curated_observations.distinct('source')
for src in sources:
    count = db.curated_observations.count_documents({'source': src})
    pct = count / total * 100
    print(f"  {src:<30} : {count:>6,} ({pct:>5.1f}%)")

# Types de donnees dans attrs
print("\n\nCHAMPS dans attrs (echantillon):")
print("-"*60)
sample_attrs = db.curated_observations.find_one({'attrs': {'$exists': True}})
if sample_attrs and 'attrs' in sample_attrs:
    attrs = sample_attrs['attrs']
    for key, val in list(attrs.items())[:15]:
        print(f"  {key:<20} : {val}")

# Exemple concret SONATEL
print("\n\nEXEMPLE: SONATEL (si disponible):")
print("-"*60)
sonatel = db.curated_observations.find_one({'attrs.symbol': 'SONATEL'})
if sonatel:
    if 'attrs' in sonatel:
        attrs = sonatel['attrs']
        fields = ['symbol', 'date', 'price', 'close', 'open', 'high', 'low', 'volume',
                 'variation_pct', 'timestamp']
        for f in fields:
            if f in attrs:
                print(f"  {f:<15} : {attrs[f]}")
    print(f"  Source: {sonatel.get('source')}")
    print(f"  Timestamp: {sonatel.get('ts')}")

print("\n" + "="*80)
print("CONCLUSION:")
print("-"*80)
print("Ces 34,212 observations = votre HISTORIQUE BRVM collecte.")
print("")
print("STRUCTURE:")
print("  - Collection MongoDB : centralisation_db.curated_observations")
print("  - Format : { key, source, ts, attrs:{ symbol, date, price, ... } }")
print("  - Usage : Source pour reconstruire prices_daily et prices_weekly")
print("")
print("DONNEES DISPONIBLES:")
print(f"  - {total:,} observations historiques")
print("  - Collecte automatique depuis plusieurs mois")
print("  - Toutes actions BRVM avec prix, volumes, variations")
print("="*80 + "\n")

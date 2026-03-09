#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

total = db.prices_weekly.count_documents({})
with_atr = db.prices_weekly.count_documents({'atr_pct': {'$exists': True, '$ne': None}})
with_tradable = db.prices_weekly.count_documents({'tradable': {'$exists': True}})

print("ETAT WEEKLY:")
print(f"  Total: {total}")
print(f"  Avec ATR: {with_atr}")
print(f"  Avec tradable flag: {with_tradable}")

if with_atr > 0:
    # ATR stats
    pipeline = [
        {'$match': {'atr_pct': {'$exists': True, '$ne': None}}},
        {'$group': {
            '_id': None,
            'avg': {'$avg': '$atr_pct'},
            'max': {'$max': '$atr_pct'},
            'min': {'$min': '$atr_pct'}
        }}
    ]
    
    stats = list(db.prices_weekly.aggregate(pipeline))
    if stats:
        s = stats[0]
        print(f"\nSTATS ATR:")
        print(f"  Moyen: {s['avg']:.2f}%")
        print(f"  Min: {s['min']:.2f}%")
        print(f"  Max: {s['max']:.2f}%")
    
    # Tradables
    tradable_count = db.prices_weekly.count_documents({'tradable': True})
    print(f"\nTRADABLES (6-25%): {tradable_count}/{total} ({tradable_count/total*100:.1f}%)")
    
    # Outliers
    outliers = db.prices_weekly.count_documents({'atr_pct': {'$gt': 40}})
    if outliers > 0:
        print(f"\nATTENTION: {outliers} outliers >40% (calcul casse)")
    else:
        print(f"\nOK: Aucun outlier >40%")

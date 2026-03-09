#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test rapide collectes multiples"""
from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime

db = MongoClient()['centralisation_db']

# Check collectes multiples
docs = list(db.prices_daily.find({}, {'symbol': 1, 'date': 1, 'created_at': 1}).limit(1000))

grouped = defaultdict(list)
for d in docs:
    date_str = d['date']
    if isinstance(date_str, datetime):
        date_only = date_str.strftime('%Y-%m-%d')
    else:
        date_only = date_str.split('T')[0] if 'T' in date_str else date_str
    
    key = (d['symbol'], date_only)
    grouped[key].append(d)

multi = {k: v for k, v in grouped.items() if len(v) > 1}

print(f"Total docs (sample): {len(docs)}")
print(f"Jours uniques: {len(grouped)}")
print(f"Avec collectes multiples: {len(multi)}")

if len(multi) > 0:
    print("\nExemples:")
    for (sym, date), obs in list(multi.items())[:5]:
        print(f"  {sym} {date}: {len(obs)} collectes")
else:
    print("\n⚠️  Aucune collecte multiple trouvée")
    print("Soit vous n'avez pas encore de collectes 9h-16h,")
    print("soit elles ont déjà été agrégées.")
    
    # Check si déjà agrégé
    agg_count = db.prices_daily.count_documents({'intraday_aggregated': True})
    print(f"\nDocuments déjà agrégés: {agg_count}")

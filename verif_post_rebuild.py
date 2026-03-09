#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICATION POST-REBUILD
"""
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

print("="*80)
print("VERIFICATION POST-REBUILD WEEKLY")
print("="*80 + "\n")

# Semaines disponibles
weeks = sorted(db.prices_weekly.distinct('week'))
print(f"Semaines weekly: {len(weeks)}")
print(f"  De {weeks[0]} a {weeks[-1]}\n")

# Par semaine
for week in weeks:
    total = db.prices_weekly.count_documents({'week': week})
    with_ind = db.prices_weekly.count_documents({'week': week, 'indicators_computed': True})
    with_atr = db.prices_weekly.count_documents({'week': week, 'atr_pct': {'$exists': True, '$ne': None}})
    tradable = db.prices_weekly.count_documents({'week': week, 'tradable': True})
    
    print(f"{week}: {total:>3} obs | Ind:{with_ind:>3} | ATR:{with_atr:>3} | Tradable:{tradable:>3}")

# Stats ATR
print("\n" + "="*80)
print("STATS ATR")
print("="*80 + "\n")

atr_docs = list(db.prices_weekly.find({
    'atr_pct': {'$exists': True, '$ne': None}
}).limit(10))

if atr_docs:
    print("Echantillon ATR:")
    for doc in atr_docs:
        print(f"  {doc['symbol']:>6} {doc['week']:>10}: ATR={doc.get('atr_pct'):>6.2f}% tradable={doc.get('tradable')}")
else:
    print("AUCUN ATR calcule!")

# Stats globales
all_atr = list(db.prices_weekly.find({
    'atr_pct': {'$exists': True, '$ne': None}
}, {'atr_pct': 1}))

if all_atr:
    atrs = [d['atr_pct'] for d in all_atr if d.get('atr_pct') is not None]
    avg_atr = sum(atrs) / len(atrs)
    max_atr = max(atrs)
    min_atr = min(atrs)
    
    print(f"\nGlobal ATR:")
    print(f"  Total: {len(atrs)}")
    print(f"  Moyen: {avg_atr:.2f}%")
    print(f"  Min: {min_atr:.2f}%")
    print(f"  Max: {max_atr:.2f}%")
    
    # Outliers
    outliers = len([a for a in atrs if a > 40])
    if outliers > 0:
        print(f"\n  ATTENTION: {outliers} outliers >40%")
    else:
        print(f"\n  OK: Aucun outlier >40%")

print("\n" + "="*80 + "\n")

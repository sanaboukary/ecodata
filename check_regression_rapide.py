#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check rapide structure données
"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("DAILY COUNT:", db.prices_daily.count_documents({}))
print("WEEKLY COUNT:", db.prices_weekly.count_documents({}))

# Premier et dernier
first = db.prices_daily.find_one(sort=[('date', 1)])
last = db.prices_daily.find_one(sort=[('date', -1)])

if first:
    print(f"\nPREMIER: {first.get('date')} - {first.get('symbol')}")
    print(f"  High: {first.get('high')}, Low: {first.get('low')}, Close: {first.get('close')}")

if last:
    print(f"\nDERNIER: {last.get('date')} - {last.get('symbol')}")
    print(f"  High: {last.get('high')}, Low: {last.get('low')}, Close: {last.get('close')}")

# Stats OHLC sur derniers 100
recent = list(db.prices_daily.find().sort('date', -1).limit(100))
ohlc_ok = sum(1 for r in recent if r.get('high', 0) > 0 and r.get('low', 0) > 0)
print(f"\n100 DERNIERS: {ohlc_ok}/100 avec OHLC complet ({ohlc_ok}%)")

# Stats sur anciens (skip 1000, prendre 100)
old = list(db.prices_daily.find().sort('date', -1).skip(1000).limit(100))
ohlc_old = sum(1 for r in old if r.get('high', 0) > 0 and r.get('low', 0) > 0)
print(f"100 ANCIENS (skip 1000): {ohlc_old}/100 avec OHLC complet ({ohlc_old}%)")

print("\n" + "="*60)
if ohlc_ok < 50 and ohlc_old > 80:
    print("❌ RÉGRESSION CONFIRMÉE - collector a changé récemment")
elif ohlc_ok > 80:
    print("✅ Données daily OK - problème ailleurs (pipeline weekly)")
else:
    print("⚠️  Données partielles depuis longtemps")

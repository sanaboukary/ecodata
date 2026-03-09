#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

# Check prices_daily
total_daily = db.prices_daily.count_documents({})
with_volume = db.prices_daily.count_documents({'volume': {'$gt': 0}})
complete_ohlc = db.prices_daily.count_documents({'is_complete': True})

print("PRICES_DAILY:")
print(f"  Total: {total_daily:,}")
print(f"  Avec volume >0: {with_volume:,} ({with_volume/total_daily*100:.1f}%)")
print(f"  OHLC complet: {complete_ohlc:,} ({complete_ohlc/total_daily*100:.1f}%)")

# Echantillon
print("\nEchantillon (10 obs recentes):")
recent = list(db.prices_daily.find().sort('date', -1).limit(10))

for doc in recent:
    date = doc.get('date', 'N/A')
    symbol = doc.get('symbol', 'N/A')
    open_p = doc.get('open') or 0
    high = doc.get('high') or 0
    low = doc.get('low') or 0
    close = doc.get('close') or 0
    volume = doc.get('volume') or 0
    
    print(f"  {date} {symbol:6s}  "
          f"O:{open_p:7.0f} H:{high:7.0f} "
          f"L:{low:7.0f} C:{close:7.0f} "
          f"V:{volume:,}")

print("\nPROBLEME VOLUME:")
if with_volume < total_daily * 0.5:
    print(f"  CRITIQUE: Moins de 50% des donnees daily ont du volume")
    print(f"  => Les donnees BRVM ont rarement du volume (marche peu liquide)")
    print(f"  => NORMAL pour la BRVM - utiliser OHLC uniquement")
    print(f"\n  SOLUTION:")
    print(f"    - ATR base sur OHLC (high-low, high-prev_close, low-prev_close)")
    print(f"    - Volume ratio facultatif")
    print(f"    - Rebuild weekly fonctionnera malgre volume=0")

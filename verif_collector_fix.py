#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vérifier que le collector corrigé génère bien high/low"""

from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Prendre les 47 dernières observations (aujourd'hui normalement)
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
recent = list(db.prices_daily.find({'date': {'$gte': today}}).sort('date', -1).limit(50))

if len(recent) == 0:
    print("❌ Aucune donnée collectée aujourd'hui")
    # Prendre les plus récentes
    recent = list(db.prices_daily.find().sort('date', -1).limit(50))

print(f"📊 Vérification {len(recent)} observations les plus récentes\n")

ohlc_ok = 0
ohlc_zero = 0
samples_good = []
samples_bad = []

for obs in recent:
    symbol = obs.get('symbol', 'N/A')
    high = obs.get('high', 0)
    low = obs.get('low', 0)
    close = obs.get('close', 0)
    open_p = obs.get('open', 0)
    date = obs.get('date', 'N/A')
    
    if high > 0 and low > 0 and close > 0 and open_p > 0:
        ohlc_ok += 1
        if len(samples_good) < 3:
            samples_good.append((symbol, open_p, high, low, close))
    else:
        ohlc_zero += 1
        if len(samples_bad) < 3:
            samples_bad.append((symbol, open_p, high, low, close))

print(f"✅ OHLC complet : {ohlc_ok}/{len(recent)} ({ohlc_ok/len(recent)*100:.1f}%)")
print(f"❌ OHLC incomplet: {ohlc_zero}/{len(recent)} ({ohlc_zero/len(recent)*100:.1f}%)")

if samples_good:
    print(f"\n📌 Exemples avec OHLC OK:")
    for sym, o, h, l, c in samples_good:
        print(f"  {sym:6} | Open:{o:8.0f} | High:{h:8.0f} | Low:{l:8.0f} | Close:{c:8.0f}")

if samples_bad:
    print(f"\n📌 Exemples avec OHLC manquant:")
    for sym, o, h, l, c in samples_bad:
        print(f"  {sym:6} | Open:{o:8.0f} | High:{h:8.0f} | Low:{l:8.0f} | Close:{c:8.0f}")

print("\n" + "="*70)
if ohlc_ok / len(recent) > 0.95:
    print("✅ COLLECTOR CORRIGÉ FONCTIONNE - OHLC calculés correctement")
elif ohlc_ok / len(recent) > 0.50:
    print("⚠️  Amélioration partielle - vérifier cas d'erreur")
else:
    print("❌ Collector toujours cassé - high/low toujours à 0")
print("="*70)

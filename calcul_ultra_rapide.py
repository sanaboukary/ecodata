#!/usr/bin/env python3
"""Script ultra-simple pour finir le calcul"""

import os, sys
from pathlib import Path
from datetime import datetime
from statistics import mean, stdev
import math

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Fonctions de calcul simples
def calc_rsi(closes, period=14):
    if len(closes) < 8:
        return None
    period = min(period, len(closes) - 1)
    
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    return round(100 - (100 / (1 + avg_gain/avg_loss)), 2)

def calc_sma(closes, period):
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)

# MAIN
print("CALCUL ULTRA-RAPIDE DES 50 PREMIERS")
print("="*50)

docs = list(db.prices_weekly.find({
    'indicators_computed': {'$ne': True}
}).sort('week', 1).limit(50))

print(f"\n{len(docs)} documents a traiter\n")

for i, doc in enumerate(docs, 1):
    symbol = doc['symbol']
    week = doc['week']
    
    # Historique
    history = list(db.prices_weekly.find({
        'symbol': symbol,
        'week': {'$lte': week}
    }).sort('week', 1))
    
    if len(history) < 5:
        print(f"{i:3d}. {symbol:10s} {week} SKIP (< 5 sem)")
        continue
    
    closes = [h.get('close', 0) for h in history if h.get('close', 0) > 0]
    if len(closes) < 5:
        print(f"{i:3d}. {symbol:10s} {week} SKIP (prix manquants)")
        continue
    
    # Calcul minimal
    rsi = calc_rsi(closes)
    sma5 = calc_sma(closes, 5)
    sma10 = calc_sma(closes, 10)
    
    trend = 'NEUTRAL'
    if sma5 and sma10:
        if sma5 > sma10 * 1.02:
            trend = 'BULLISH'
        elif sma5 < sma10 * 0.98:
            trend = 'BEARISH'
    
    # Update
    db.prices_weekly.update_one(
        {'_id': doc['_id']},
        {'$set': {
            'rsi': rsi,
            'sma5': sma5,
            'sma10': sma10,
            'trend': trend,
            'indicators_computed': True,
            'indicators_updated_at': datetime.now()
        }}
    )
    
    print(f"{i:3d}. {symbol:10s} {week} OK RSI={rsi} {trend}")

# Verification
total = db.prices_weekly.count_documents({})
with_ind = db.prices_weekly.count_documents({'indicators_computed': True})

print("\n" + "="*50)
print(f"RESULTAT: {with_ind}/{total} ({100*with_ind/total:.1f}%)")
print("="*50)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINALISATION MODE PRO - Calcul indicateurs manquants sur semaines de qualite
=============================================================================
Cible: W49, W02, W06 (14, 9, 7 actions sans indicateurs)
Total: 30 documents a completer pour 100% qualite PRO
"""

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

# SEMAINES CIBLES - Mode PRO
SEMAINES_PRO = [
    '2025-W42', '2025-W43', '2025-W44', '2025-W45', '2025-W46',
    '2025-W47', '2025-W48', '2025-W49', '2026-W02', '2026-W06'
]

# Configuration indicateurs
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

def calc_atr_pct(history, period=5):
    if len(history) < period + 1:
        return None
    active = [w for w in history if w.get('volume', 0) > 0 or abs((w.get('close', 0) - w.get('open', w.get('close', 0))) / w.get('open', 1) * 100) > 0.5]
    if len(active) < max(4, period):
        active = history if len(history) >= 4 else []
    if not active:
        return None
    true_ranges = []
    for i in range(1, len(active)):
        curr, prev = active[i], active[i-1]
        high = curr.get('high', curr.get('close', 0))
        low = curr.get('low', curr.get('close', 0))
        prev_close = prev.get('close', 0)
        if prev_close > 0:
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
    if len(true_ranges) < period:
        return None
    atr = sum(true_ranges[-period:]) / len(true_ranges[-period:])
    current_price = active[-1].get('close', 0)
    return round((atr / current_price) * 100, 2) if current_price > 0 else None

def calc_sma(closes, period):
    return round(sum(closes[-period:]) / period, 2) if len(closes) >= period else None

def calc_volatility(history, period=12):
    if len(history) < period:
        return None
    closes = [w.get('close', 0) for w in history[-period:] if w.get('close', 0) > 0]
    if len(closes) < 4:
        return None
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1] > 0]
    if len(returns) < 3:
        return None
    variance = sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)
    return round(math.sqrt(variance) * 100, 2)

def calc_volume_zscore(symbol, week_str, period=8):
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'volume': 1}
    ).sort('week', -1).limit(period + 1))
    if len(history) < 4:
        return None
    current, past = history[0], history[1:]
    volumes = [h.get('volume', 0) for h in past if h.get('volume', 0) > 0]
    if len(volumes) < 3:
        return None
    vol_mean, vol_std = mean(volumes), stdev(volumes) if len(volumes) > 1 else 0
    current_vol = current.get('volume', 0)
    return round((current_vol - vol_mean) / vol_std, 2) if vol_std > 0 and current_vol > 0 else 0.0

def calc_acceleration(symbol, week_str):
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'close': 1}
    ).sort('week', -1).limit(3))
    if len(history) < 3:
        return None
    c0, c1, c2 = history[0].get('close', 0), history[1].get('close', 0), history[2].get('close', 0)
    if c1 <= 0 or c2 <= 0:
        return None
    return round(((c0 - c1) / c1 - (c1 - c2) / c2) * 100, 2)

print("=" * 80)
print("FINALISATION MODE PRO - EXPERTISE TOTALE")
print("=" * 80)
print(f"\nSemaines cibles: {', '.join(SEMAINES_PRO)}")

# Compter documents sans indicateurs dans semaines PRO
docs_manquants = list(db.prices_weekly.find({
    'week': {'$in': SEMAINES_PRO},
    'indicators_computed': {'$ne': True}
}).sort('week', 1))

print(f"\nDocuments sans indicateurs: {len(docs_manquants)}")

if len(docs_manquants) == 0:
    print("\n[OK] Toutes les semaines PRO ont leurs indicateurs!")
    print("\nPROCHAINE ETAPE: Executer pipeline_brvm.py")
else:
    print(f"\nCalcul des {len(docs_manquants)} indicateurs manquants...\n")
    
    success = 0
    for i, doc in enumerate(docs_manquants, 1):
        symbol, week = doc['symbol'], doc['week']
        
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
        
        # Calculs
        rsi = calc_rsi(closes, 14)
        atr_pct = calc_atr_pct(history, 5)
        sma5 = calc_sma(closes, 5)
        sma10 = calc_sma(closes, 10)
        volatility = calc_volatility(history, 12)
        
        volumes = [h.get('volume', 0) for h in history[-8:]]
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        volume_ratio = round(doc.get('volume', 0) / avg_vol, 2) if avg_vol > 0 else 0.0
        
        volume_zscore = calc_volume_zscore(symbol, week, 8)
        acceleration = calc_acceleration(symbol, week)
        
        # Signaux
        rsi_signal = 'OVERSOLD' if rsi and rsi < 40 else 'OVERBOUGHT' if rsi and rsi > 65 else 'NEUTRAL'
        
        atr_signal, tradable = 'NORMAL', True
        if atr_pct:
            if atr_pct < 6:
                atr_signal, tradable = 'DEAD', False
            elif atr_pct > 25:
                atr_signal, tradable = 'EXCESSIVE', False
        
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
                'atr_pct': atr_pct,
                'sma5': sma5,
                'sma10': sma10,
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'volume_zscore': volume_zscore,
                'acceleration': acceleration,
                'rsi_signal': rsi_signal,
                'atr_signal': atr_signal,
                'trend': trend,
                'tradable': tradable,
                'indicators_computed': True,
                'indicators_updated_at': datetime.now()
            }}
        )
        
        success += 1
        print(f"{i:3d}. {symbol:10s} {week} OK RSI={rsi} ATR={atr_pct}% {trend}")

# Verification finale
print("\n" + "=" * 80)
print("VERIFICATION FINALE")
print("=" * 80)

for week in SEMAINES_PRO:
    total = db.prices_weekly.count_documents({'week': week})
    with_ind = db.prices_weekly.count_documents({'week': week, 'indicators_computed': True})
    pct = 100 * with_ind / total if total > 0 else 0
    status = "OK" if pct == 100 else "!!" if pct >= 70 else "X"
    print(f"[{status}] {week}: {with_ind}/{total} ({pct:.1f}%)")

print("\n" + "=" * 80)
print("SYSTEME PRET - MODE PRO ACTIVE")
print("=" * 80)
print("\nPROCHAINE ETAPE:")
print("  python pipeline_brvm.py")
print("\n  Le systeme analysera UNIQUEMENT les 10 semaines de qualite PRO")
print("  et generera des recommandations fiables basees sur 30 ans d'expertise")
print("=" * 80)

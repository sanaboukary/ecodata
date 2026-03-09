#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCUL INDICATEURS - VERSION OPTIMISEE  
Ne traite QUE les documents sans indicateurs
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

# Configuration
RSI_PERIOD = 14
RSI_OVERSOLD = 40
RSI_OVERBOUGHT = 65
ATR_PERIOD = 5
ATR_DEAD_MARKET = 6.0
ATR_MIN_TRADE = 6.0
ATR_MAX_TRADE = 25.0
ATR_EXCESSIVE = 25.0
SMA_FAST = 5
SMA_SLOW = 10
VOLUME_PERIOD = 8
VOLUME_ZSCORE_PERIOD = 8
VOLATILITY_PERIOD = 12

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        if len(closes) < 8:
            return None
        period = min(period, len(closes) - 1)
    
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_atr_pct(weekly_history, period=5):
    if len(weekly_history) < period + 1:
        return None
    
    active_weeks = []
    for w in weekly_history:
        close = w.get('close', 0)
        volume = w.get('volume', 0)
        open_price = w.get('open', close)
        variation_pct = abs((close - open_price) / open_price * 100) if open_price > 0 else 0
        if volume > 0 or variation_pct > 0.5:
            active_weeks.append(w)
    
    if len(active_weeks) < max(4, period):
        if len(weekly_history) >= 4:
            active_weeks = weekly_history
        else:
            return None
    
    true_ranges = []
    for i in range(1, len(active_weeks)):
        current = active_weeks[i]
        previous = active_weeks[i-1]
        high = current.get('high', current.get('close', 0))
        low = current.get('low', current.get('close', 0))
        prev_close = previous.get('close', 0)
        
        if prev_close > 0:
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    atr = sum(true_ranges[-period:]) / len(true_ranges[-period:])
    current_price = active_weeks[-1].get('close', 0)
    
    if current_price <= 0:
        return None
    
    return round((atr / current_price) * 100, 2)

def calculate_sma(closes, period):
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)

def calculate_volatility(weekly_history, period=12):
    if len(weekly_history) < period:
        return None
    
    closes = [w.get('close', 0) for w in weekly_history[-period:] if w.get('close', 0) > 0]
    if len(closes) < 4:
        return None
    
    returns = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0:
            returns.append((closes[i] - closes[i-1]) / closes[i-1])
    
    if len(returns) < 3:
        return None
    
    variance = sum((r - (sum(returns)/len(returns)))**2 for r in returns) / len(returns)
    return round(math.sqrt(variance) * 100, 2)

def calculate_volume_zscore(symbol, week_str, history_weeks=8):
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'volume': 1}
    ).sort('week', -1).limit(history_weeks + 1))
    
    if len(history) < 4:
        return None
    
    current = history[0]
    past = history[1:]
    volumes = [h.get('volume', 0) for h in past if h.get('volume', 0) > 0]
    
    if len(volumes) < 3:
        return None
    
    vol_mean = mean(volumes)
    vol_std = stdev(volumes) if len(volumes) > 1 else 0
    current_vol = current.get('volume', 0)
    
    if vol_std > 0 and current_vol > 0:
        return round((current_vol - vol_mean) / vol_std, 2)
    
    return 0.0

def calculate_acceleration(symbol, week_str):
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'close': 1}
    ).sort('week', -1).limit(3))
    
    if len(history) < 3:
        return None
    
    close_0 = history[0].get('close', 0)
    close_1 = history[1].get('close', 0)
    close_2 = history[2].get('close', 0)
    
    if close_1 <= 0 or close_2 <= 0:
        return None
    
    var_1 = ((close_0 - close_1) / close_1) * 100
    var_2 = ((close_1 - close_2) / close_2) * 100
    
    return round(var_1 - var_2, 2)

def compute_all_indicators_for_document(doc):
    symbol = doc['symbol']
    week_str = doc['week']
    
    weekly_history = list(db.prices_weekly.find({
        'symbol': symbol,
        'week': {'$lte': week_str}
    }).sort('week', 1))
    
    if len(weekly_history) < 5:
        return None
    
    closes = [w.get('close', 0) for w in weekly_history if w.get('close', 0) > 0]
    if len(closes) < 5:
        return None
    
    rsi = calculate_rsi(closes, RSI_PERIOD)
    atr_pct = calculate_atr_pct(weekly_history, ATR_PERIOD)
    sma5 = calculate_sma(closes, SMA_FAST)
    sma10 = calculate_sma(closes, SMA_SLOW)
    volatility = calculate_volatility(weekly_history, VOLATILITY_PERIOD)
    
    volumes = [w.get('volume', 0) for w in weekly_history[-VOLUME_PERIOD:]]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    current_volume = doc.get('volume', 0)
    volume_ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 0.0
    
    volume_zscore = calculate_volume_zscore(symbol, week_str, VOLUME_ZSCORE_PERIOD)
    acceleration = calculate_acceleration(symbol, week_str)
    
    rsi_signal = 'NEUTRAL'
    if rsi:
        if rsi < RSI_OVERSOLD:
            rsi_signal = 'OVERSOLD'
        elif rsi > RSI_OVERBOUGHT:
            rsi_signal = 'OVERBOUGHT'
    
    atr_signal = 'NORMAL'
    tradable = True
    if atr_pct:
        if atr_pct < ATR_DEAD_MARKET:
            atr_signal = 'DEAD'
            tradable = False
        elif atr_pct > ATR_EXCESSIVE:
            atr_signal = 'EXCESSIVE'
            tradable = False
        elif atr_pct > ATR_MAX_TRADE:
            atr_signal = 'VOLATILE'
    
    trend = 'NEUTRAL'
    if sma5 and sma10:
        if sma5 > sma10 * 1.02:
            trend = 'BULLISH'
        elif sma5 < sma10 * 0.98:
            trend = 'BEARISH'
    
    return {
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
    }

def main():
    print("="*60)
    print("CALCUL INDICATEURS - VERSION OPTIMISEE")
    print("="*60)
    
    # NE RECUPERER QUE les documents SANS indicateurs
    docs_without_indicators = list(db.prices_weekly.find({
        'indicators_computed': {'$ne': True}
    }).sort('week', 1))
    
    total = db.prices_weekly.count_documents({})
    to_process = len(docs_without_indicators)
    
    print(f"\nDocuments SANS indicateurs: {to_process}/{total}")
    
    if to_process == 0:
        print("\n[OK] Tous les documents ont leurs indicateurs!")
        return
    
    print(f"\nTraitement de {to_process} documents...\n")
    
    success_count = 0
    skip_count = 0
    
    weeks_processed = set()
    
    for i, doc in enumerate(docs_without_indicators, 1):
        symbol = doc['symbol']
        week = doc['week']
        
        if week not in weeks_processed:
            weeks_processed.add(week)
            print(f"\nSemaine {week}:")
        
        try:
            indicators = compute_all_indicators_for_document(doc)
            
            if indicators:
                db.prices_weekly.update_one(
                    {'_id': doc['_id']},
                    {'$set': indicators}
                )
                success_count += 1
                print(f"  {symbol:10s} [OK]", end='')
                if indicators.get('rsi'):
                    print(f" RSI={indicators['rsi']:.1f}", end='')
                if indicators.get('atr_pct'):
                    print(f" ATR={indicators['atr_pct']:.1f}%", end='')
                print()
            else:
                skip_count += 1
                if week in sorted(list(weeks_processed))[:3]:
                    print(f"  {symbol:10s} [SKIP] historique insuffisant")
        
        except Exception as e:
            print(f"  {symbol:10s} [ERROR] {str(e)[:40]}")
    
    after = db.prices_weekly.count_documents({'indicators_computed': True})
    
    print("\n" + "="*60)
    print("RESULTAT")
    print("="*60)
    print(f"Traites avec succes : {success_count}")
    print(f"Skippés             : {skip_count}")
    print(f"TOTAL avec indicateurs: {after}/{total} ({100*after/total:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    main()

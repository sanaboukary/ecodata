#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECALCUL INDICATEURS EXPERTS - VERSION SIMPLIFIÉE
"""

from pymongo import MongoClient
from statistics import mean, stdev
from datetime import datetime

# MongoDB direct
client = MongoClient('localhost', 27017)
db = client['centralisation_db']

def calculate_variation_pct(current_close, previous_close):
    """Calcule variation %"""
    if previous_close and previous_close > 0:
        var_pct = ((current_close - previous_close) / previous_close) * 100
        return round(var_pct, 2)
    return 0

def calculate_volume_zscore(symbol, week_str, history_weeks=8):
    """Calcule Z-score volume"""
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
        z_score = (current_vol - vol_mean) / vol_std
        return round(z_score, 2)
    
    return 0

def calculate_acceleration(symbol, week_str):
    """Calcule accélération momentum"""
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'close': 1}
    ).sort('week', -1).limit(3))
    
    if len(history) < 3:
        return None
    
    # Calculer variations à la volée
    close_0 = history[0].get('close', 0)
    close_1 = history[1].get('close', 0)
    close_2 = history[2].get('close', 0)
    
    if not (close_0 and close_1 and close_2):
        return None
    
    var_0 = calculate_variation_pct(close_0, close_1)
    var_1 = calculate_variation_pct(close_1, close_2)
    
    accel = var_0 - var_1
    
    return round(accel, 2)

def main():
    print("\n" + "="*80)
    print("RECALCUL INDICATEURS EXPERTS BRVM 30 ANS")
    print("="*80)
    
    # Récupérer tous les symboles
    symbols = db.prices_weekly.distinct('symbol')
    symbols = [s for s in symbols if s and s not in ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']]
    
    print(f"\n{len(symbols)} actions à traiter")
    
    # Récupérer toutes les semaines
    weeks = db.prices_weekly.distinct('week')
    weeks.sort()
    
    print(f"{len(weeks)} semaines à traiter\n")
    
    total_updated = 0
    total_processed = 0
    
    for symbol in symbols:
        print(f"\n[{symbol}]", end=" ", flush=True)
        
        # Récupérer historique complet pour ce symbole
        history = list(db.prices_weekly.find(
            {'symbol': symbol},
            {'week': 1, 'close': 1, 'volume': 1, 'variation_pct': 1}
        ).sort('week', 1))
        
        if len(history) < 2:
            print("SKIP (historique insuffisant)")
            continue
        
        updated_count = 0
        
        for i, doc in enumerate(history):
            week_str = doc['week']
            current_close = doc.get('close', 0)
            
            # 1. VARIATION_PCT
            variation_pct = doc.get('variation_pct')
            if variation_pct is None and i > 0:
                previous_close = history[i-1].get('close', 0)
                variation_pct = calculate_variation_pct(current_close, previous_close)
                
                db.prices_weekly.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'variation_pct': variation_pct}}
                )
                updated_count += 1
            
            # 2. VOLUME_ZSCORE
            volume_zscore = calculate_volume_zscore(symbol, week_str)
            
            if volume_zscore is not None:
                db.prices_weekly.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'volume_zscore': volume_zscore}}
                )
                updated_count += 1
            
            # 3. ACCELERATION
            if i >= 1:
                acceleration = calculate_acceleration(symbol, week_str)
                
                if acceleration is not None:
                    db.prices_weekly.update_one(
                        {'_id': doc['_id']},
                        {'$set': {'acceleration': acceleration}}
                    )
                    updated_count += 1
            
            total_processed += 1
        
        print(f"[OK] {updated_count} mises a jour")
        total_updated += updated_count
    
    print("\n" + "="*80)
    print(f"[TERMINE]")
    print(f"   Documents traites: {total_processed}")
    print(f"   Mises a jour: {total_updated}")
    print("="*80 + "\n")
    
    # Vérification échantillon
    print("VERIFICATION ECHANTILLON:")
    print("-"*80)
    
    sample = list(db.prices_weekly.find(
        {'volume_zscore': {'$exists': True}},
        {'symbol': 1, 'week': 1, 'volume_zscore': 1, 'acceleration': 1, 'variation_pct': 1}
    ).limit(10))
    
    for s in sample:
        print(f"{s['symbol']:6s} | {s['week']} | "
              f"VolZ: {s.get('volume_zscore', 'N/A'):+6} | "
              f"Accel: {s.get('acceleration', 'N/A'):+6}% | "
              f"Var: {s.get('variation_pct', 'N/A'):+6}%")
    
    print("\n")

if __name__ == "__main__":
    main()

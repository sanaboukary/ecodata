#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST DEBUG calculate_atr_pct
"""
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

# Fonction is_dead_week (copy from pipeline)
def is_dead_week(week_data):
    if week_data.get('volume', 0) == 0:
        return True
    
    high = week_data.get('high', 0)
    low = week_data.get('low', 0)
    close = week_data.get('close', 0)
    
    if high == low == close:
        return True
    
    open_price = week_data.get('open', close)
    if open_price > 0:
        variation_pct = abs((close - open_price) / open_price * 100)
        if variation_pct < 0.1:
            return True
    
    return False

# Test sur 1 action
symbol = 'SNTS'
weekly_docs = list(db.prices_weekly.find({'symbol': symbol}).sort('week', 1))

print(f"Action: {symbol}")
print(f"Total semaines: {len(weekly_docs)}\n")

if not weekly_docs:
    print(" ERREUR: Aucune semaine")
    exit(1)

# Analyser chaque semaine
for w in weekly_docs:
    week = w.get('week')
    is_dead = is_dead_week(w)
    
    print(f"{week}: Dead={is_dead} | Vol={w.get('volume',0):>8} | H={w.get('high',0):>6.0f} | L={w.get('low',0):>6.0f} | C={w.get('close',0):>6.0f}")

# Active weeks
active = [w for w in weekly_docs if not is_dead_week(w)]
print(f"\nActive weeks: {len(active)} / {len(weekly_docs)}")

if len(active) >= 6:
    print("\nHistorique suffisant pour ATR (>= 6 semaines actives)")
    
    # Calc ATR manuel
    true_ranges = []
    for i in range(1, len(active)):
        high = active[i].get('high', 0)
        low = active[i].get('low', 0)
        prev_close = active[i-1].get('close', 0)
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
        print(f"  TR[{i}]: {tr:.2f}")
    
    if len(true_ranges) >= 5:
        atr_5w = sum(true_ranges[-5:]) / 5
        current_price = active[-1].get('close', 0)
        
        if current_price > 0:
            atr_pct = (atr_5w / current_price) * 100
            print(f"\nATR 5W: {atr_5w:.2f}")
            print(f"Prix actuel: {current_price:.0f}")
            print(f"ATR%: {atr_pct:.2f}%")
            
            if atr_pct > 40:
                print("  OUTLIER (>40%)")
        else:
            print("\n  ERREUR: Prix = 0")
    else:
        print(f"\n  Pas assez de TR: {len(true_ranges)}")
else:
    print(f"\n  Historique insuffisant: {len(active)} semaines actives")

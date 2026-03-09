#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST MANUEL ATR SUR UNE ACTION
"""
from pymongo import MongoClient
import sys, os
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

# Fonction is_dead_week
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

# Fonction ATR BRVM PRO
def calculate_atr_pct_brvm(weekly_data, period=5):
    if len(weekly_data) < period + 1:
        return None, "Pas assez de semaines"
    
    # Filtrer semaines mortes
    active_weeks = [w for w in weekly_data if not is_dead_week(w)]
    dead_count = len(weekly_data) - len(active_weeks)
    
    if len(active_weeks) < period + 1:
        return None, f"Pas assez de semaines actives ({len(active_weeks)}, {dead_count} mortes)"
    
    # Calculer TR
    true_ranges = []
    for i in range(1, len(active_weeks)):
        high = active_weeks[i].get('high', 0)
        low = active_weeks[i].get('low', 0)
        prev_close = active_weeks[i-1].get('close', 0)
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None, f"Pas assez de TR ({len(true_ranges)})"
    
    # ATR 5W
    atr_5w = sum(true_ranges[-period:]) / period
    current_price = active_weeks[-1].get('close', 0)
    
    if current_price <= 0:
        return None, "Prix invalide"
    
    atr_pct = (atr_5w / current_price) * 100
    
    if atr_pct > 40:
        return None, f"Outlier {atr_pct:.2f}% >40%"
    
    return round(atr_pct, 2), f"OK (semaines actives: {len(active_weeks)}, TR moyen: {atr_5w:.2f})"

# Test sur actions
print("="*80)
print("TEST MANUEL ATR BRVM PRO")
print("="*80 + "\n")

symbols_test = ['SNTS', 'SGBC', 'BOAC', 'ETIT', 'ORGT']

for symbol in symbols_test:
    print(f"\n{'='*80}")
    print(f"ACTION: {symbol}")
    print(f"{'='*80}")
    
    # Récupérer historique weekly
    weekly_docs = list(db.prices_weekly.find(
        {'symbol': symbol}
    ).sort('week', 1))
    
    print(f"Semaines en DB: {len(weekly_docs)}")
    
    if len(weekly_docs) == 0:
        print("  ERREUR: Aucune donnee weekly")
        continue
    
    # ATR actuel en DB
    last_week_db = weekly_docs[-1] if weekly_docs else {}
    atr_db = last_week_db.get('atr_pct')
    tradable_db = last_week_db.get('tradable')
    
    print(f"  ATR en DB: {atr_db}%")
    print(f"  Tradable en DB: {tradable_db}")
    
    # Calculer ATR BRVM PRO
    atr_new, msg = calculate_atr_pct_brvm(weekly_docs, period=5)
    
    print(f"\n  ATR BRVM PRO calcule: {atr_new}%")
    print(f"  Detail: {msg}")
    
    if atr_new and atr_db:
        diff = atr_new - atr_db
        print(f"  Difference: {diff:+.2f}% ({'AMELIORATION' if abs(diff) > 5 else 'Proche'})")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nSi ATR BRVM PRO < ATR DB massivement:")
print("  => Calibration BRVM PRO fonctionne (filtre semaines mortes)")
print("\nSi ATR BRVM PRO = None souvent:")
print("  => Donnees weekly de base ont problemes (outliers dans prices_daily)")
print("\nSi ATR BRVM PRO ≈ ATR DB:")
print("  => Recalcul n'a pas ete execute ou code non charge")

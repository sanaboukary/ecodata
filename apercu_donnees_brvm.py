#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apercu des VRAIES donnees de cours BRVM"""
from pymongo import MongoClient
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("\n" + "="*80)
print("DONNEES DE COURS BRVM - VUE COMPLETE")
print("="*80 + "\n")

# ============================================================================
# 1. PRICES_INTRADAY_RAW (collectes brutes)
# ============================================================================
print("1. PRICES_INTRADAY_RAW (nouvelles collectes)")
print("-"*80)

raw_total = db.prices_intraday_raw.count_documents({})
print(f"Total: {raw_total:,} observations\n")

if raw_total > 0:
    # Dates
    dates = sorted(db.prices_intraday_raw.distinct('date'))
    print(f"Dates: {dates[0]} -> {dates[-1]} ({len(dates)} dates)")
    
    # Symboles
    symbols = db.prices_intraday_raw.distinct('symbol')
    print(f"Symboles: {len(symbols)} actions")
    print(f"Exemples: {', '.join(sorted(symbols)[:10])}")
    
    # Echantillon
    sample = db.prices_intraday_raw.find_one()
    print(f"\nEchantillon (1 observation RAW):")
    for key in ['symbol', 'datetime', 'date', 'price', 'volume', 'variation_pct', 'source']:
        if key in sample:
            print(f"  {key:<15} : {sample[key]}")

# ============================================================================
# 2. PRICES_DAILY (source de verite)
# ============================================================================
print("\n\n2. PRICES_DAILY (agregation journaliere - SOURCE DE VERITE)")
print("-"*80)

daily_total = db.prices_daily.count_documents({})
print(f"Total: {daily_total:,} jours x symboles\n")

if daily_total > 0:
    # Dates
    dates = sorted(db.prices_daily.distinct('date'))
    print(f"Periode: {dates[0]} -> {dates[-1]}")
    print(f"Dates uniques: {len(dates)} jours\n")
    
    # Symboles
    symbols = db.prices_daily.distinct('symbol')
    print(f"Symboles: {len(symbols)} actions")
    
    # Top 10 symboles par nombre de jours
    print(f"\nTOP 10 actions (plus de jours de cotation):")
    pipeline = [
        {"$group": {"_id": "$symbol", "jours": {"$sum": 1}}},
        {"$sort": {"jours": -1}},
        {"$limit": 10}
    ]
    for item in db.prices_daily.aggregate(pipeline):
        print(f"  {item['_id']:<12} : {item['jours']:>3} jours")
    
    # Echantillon avec OHLC complet
    sample = db.prices_daily.find_one({'is_complete': True})
    if sample:
        print(f"\nEchantillon (OHLC complet):")
        for key in ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 
                   'variation_pct', 'is_complete']:
            if key in sample:
                print(f"  {key:<15} : {sample[key]}")

# ============================================================================
# 3. PRICES_WEEKLY (decisions hebdomadaires)
# ============================================================================
print("\n\n3. PRICES_WEEKLY (agregation hebdomadaire + INDICATEURS)")
print("-"*80)

weekly_total = db.prices_weekly.count_documents({})
print(f"Total: {weekly_total:,} semaines x symboles\n")

if weekly_total > 0:
    # Semaines
    weeks = sorted(db.prices_weekly.distinct('week'))
    print(f"Periode: {weeks[0]} -> {weeks[-1]}")
    print(f"Semaines: {len(weeks)}")
    print(f"Liste: {', '.join(weeks)}\n")
    
    # Symboles
    symbols = db.prices_weekly.distinct('symbol')
    print(f"Symboles: {len(symbols)} actions")
    
    # Indicateurs calcules
    with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    print(f"\nIndicateurs calcules: {with_indicators} / {weekly_total} ({with_indicators/weekly_total*100:.1f}%)")
    
    # Echantillon avec indicateurs
    sample = db.prices_weekly.find_one({'indicators_computed': True})
    if sample:
        print(f"\nEchantillon (avec indicateurs) - {sample.get('symbol')} semaine {sample.get('week')}:")
        print(f"  OHLC:")
        for key in ['open', 'high', 'low', 'close', 'volume']:
            if key in sample:
                print(f"    {key:<10} : {sample[key]}")
        print(f"  Indicateurs:")
        for key in ['rsi', 'rsi_signal', 'atr_pct', 'sma5', 'sma10', 'trend', 
                   'volatility', 'volume_ratio']:
            if key in sample:
                val = sample[key]
                if isinstance(val, float):
                    print(f"    {key:<15} : {val:.2f}")
                else:
                    print(f"    {key:<15} : {val}")

# ============================================================================
# 4. EXEMPLE CONCRET - Une action complete
# ============================================================================
print("\n\n4. EXEMPLE CONCRET - SONATEL (si disponible)")
print("-"*80)

# Chercher SONATEL dans DAILY
sonatel_daily = list(db.prices_daily.find({'symbol': 'SONATEL'}).sort('date', -1).limit(5))
if sonatel_daily:
    print(f"\nSONATEL - Derniers jours (DAILY):")
    print(f"{'Date':<12} {'Close':>8} {'Volume':>10} {'Var%':>8}")
    for doc in sonatel_daily:
        print(f"{doc.get('date'):<12} {doc.get('close', 0):>8.0f} {doc.get('volume', 0):>10,.0f} {doc.get('variation_pct', 0):>+7.2f}%")

# Chercher SONATEL dans WEEKLY
sonatel_weekly = list(db.prices_weekly.find({'symbol': 'SONATEL'}).sort('week', -1).limit(3))
if sonatel_weekly:
    print(f"\nSONATEL - Dernieres semaines (WEEKLY):")
    for doc in sonatel_weekly:
        week = doc.get('week')
        close = doc.get('close', 0)
        rsi = doc.get('rsi', 0)
        trend = doc.get('trend', 'N/A')
        has_ind = doc.get('indicators_computed', False)
        ind_mark = "✓" if has_ind else "✗"
        print(f"  {week} : Close={close:>8.0f}  RSI={rsi:>5.1f}  Trend={trend:<10} [{ind_mark} indicateurs]")

# ============================================================================
# RESUME
# ============================================================================
print("\n\n" + "="*80)
print("RESUME DES DONNEES BRVM")
print("="*80)

print(f"""
ARCHITECTURE 3 NIVEAUX (RAW -> DAILY -> WEEKLY):

1. RAW (prices_intraday_raw)       : {raw_total:>6,} obs - Collectes brutes immutables
2. DAILY (prices_daily)             : {daily_total:>6,} obs - Source de verite (OHLC/jour)
3. WEEKLY (prices_weekly)           : {weekly_total:>6,} obs - Base decision (indicateurs techniques)

PERIODE COUVERTE:
""")

if daily_total > 0:
    dates = sorted(db.prices_daily.distinct('date'))
    print(f"  DAILY  : {dates[0]} -> {dates[-1]} ({len(dates)} jours)")

if weekly_total > 0:
    weeks = sorted(db.prices_weekly.distinct('week'))
    print(f"  WEEKLY : {weeks[0]} -> {weeks[-1]} ({len(weeks)} semaines)")

symbols_daily = db.prices_daily.distinct('symbol') if daily_total > 0 else []
print(f"\nSYMBOLES: {len(symbols_daily)} actions BRVM tracees")
print(f"Exemples: {', '.join(sorted(symbols_daily)[:15])}")

print(f"""
UTILISATION:
  - RAW     : Append-only, collecte quotidienne
  - DAILY   : Agregation RAW -> OHLC journalier (source unique)
  - WEEKLY  : Agregation DAILY -> Hebdo + RSI/ATR/SMA (pour TOP5)
  
PROCHAINES ETAPES:
  - Collecte quotidienne automatique (RAW)
  - Pipeline DAILY chaque soir 17h
  - Pipeline WEEKLY chaque lundi 8h
  - Generation TOP5 chaque semaine
""")

print("="*80 + "\n")

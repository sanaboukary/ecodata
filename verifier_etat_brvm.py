#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICATION ETAT ACTUEL BRVM
"""
from pymongo import MongoClient
from datetime import datetime
import sys
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ETAT ACTUEL DES DONNEES BRVM")
print("="*80 + "\n")

# prices_daily
daily_count = db.prices_daily.count_documents({})
daily_dates = sorted(db.prices_daily.distinct('date'))
daily_symbols = db.prices_daily.distinct('symbol')

print("PRICES_DAILY:")
print(f"  Total observations: {daily_count:,}")
print(f"  Dates uniques: {len(daily_dates)}")
print(f"  Symboles uniques: {len(daily_symbols)}")

if daily_dates:
    print(f"  Periode: {daily_dates[0]} -> {daily_dates[-1]}")
    
    # Calculer durée
    from datetime import datetime as dt
    first = dt.strptime(daily_dates[0], '%Y-%m-%d')
    last = dt.strptime(daily_dates[-1], '%Y-%m-%d')
    total_days = (last - first).days
    print(f"  Duree calendaire: {total_days} jours")
    coverage = len(daily_dates) / total_days * 100 if total_days > 0 else 0
    print(f"  Couverture: {coverage:.1f}%")

# Données restaurées
restored_count = db.prices_daily.count_documents({'is_restored': True})
if restored_count > 0:
    print(f"\n  Donnees restaurees: {restored_count} ({restored_count/daily_count*100:.1f}%)")
    
    # Sources de restauration
    sources = db.prices_daily.distinct('restored_from', {'is_restored': True})
    if sources:
        print(f"  Sources restauration: {', '.join([s for s in sources if s])}")

# Qualité OHLC
complete_ohlc = db.prices_daily.count_documents({'is_complete': True})
print(f"\n  OHLC complet: {complete_ohlc}/{daily_count} ({complete_ohlc/daily_count*100:.1f}%)")

# Données volume
with_volume = db.prices_daily.count_documents({'volume': {'$gt': 0}})
print(f"  Avec volume: {with_volume}/{daily_count} ({with_volume/daily_count*100:.1f}%)")

# prices_weekly
print("\n\nPRICES_WEEKLY:")
weekly_count = db.prices_weekly.count_documents({})
weekly_weeks = sorted(db.prices_weekly.distinct('week'))
weekly_symbols = db.prices_weekly.distinct('symbol')

print(f"  Total observations: {weekly_count:,}")
print(f"  Semaines uniques: {len(weekly_weeks)}")
print(f"  Symboles uniques: {len(weekly_symbols)}")

if weekly_weeks:
    print(f"  Periode: {weekly_weeks[0]} -> {weekly_weeks[-1]}")
    print(f"  Liste: {', '.join(weekly_weeks)}")

# Indicateurs
with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
print(f"\n  Avec indicateurs: {with_indicators}/{weekly_count} ({with_indicators/weekly_count*100:.1f}%)")

# Echantillon indicateurs
sample = db.prices_weekly.find_one({'indicators_computed': True})
if sample:
    print(f"\n  Echantillon ({sample.get('symbol')} - {sample.get('week')}):")
    print(f"    RSI: {sample.get('rsi')}")
    print(f"    ATR%: {sample.get('atr_pct')}")
    print(f"    SMA5: {sample.get('sma5')}")
    print(f"    SMA10: {sample.get('sma10')}")
    print(f"    Trend: {sample.get('trend')}")
    print(f"    Volatilite: {sample.get('volatility')}")

# VALIDATION FINALE
print("\n\n" + "="*80)
print("VALIDATION OBJECTIFS")
print("="*80)

# Objectif 1: >= 65 jours
if len(daily_dates) >= 65:
    print(f"OK Jours DAILY: {len(daily_dates)} >= 65")
else:
    print(f"ATTENTION Jours DAILY: {len(daily_dates)} < 65")

# Objectif 2: >= 14 semaines
if len(weekly_weeks) >= 14:
    print(f"OK Semaines WEEKLY: {len(weekly_weeks)} >= 14 (MODE PRODUCTION)")
else:
    print(f"ATTENTION Semaines WEEKLY: {len(weekly_weeks)} < 14 (Mode demarrage)")

# Objectif 3: Indicateurs calculés
if with_indicators >= weekly_count * 0.8:
    print(f"OK Indicateurs: {with_indicators}/{weekly_count} ({with_indicators/weekly_count*100:.1f}%)")
else:
    print(f"ATTENTION Indicateurs: {with_indicators}/{weekly_count} ({with_indicators/weekly_count*100:.1f}%)")
    print("   Action: python brvm_pipeline/pipeline_weekly.py --indicators")

# Objectif 4: ATR cohérent
if sample and sample.get('atr_pct'):
    atr = sample.get('atr_pct')
    if 5 <= atr <= 18:
        print(f"OK ATR coherent: {atr:.2f}% (entre 5% et 18%)")
    else:
        print(f"ATTENTION ATR: {atr:.2f}% (hors plage 5-18%)")

# Objectif 5: Volatilité réaliste
if sample and sample.get('volatility'):
    vol = sample.get('volatility')
    if vol <= 35:
        print(f"OK Volatilite: {vol:.2f}% (<= 35%)")
    else:
        print(f"ATTENTION Volatilite: {vol:.2f}% (> 35%)")

print("\n" + "="*80)
print("RECOMMANDATIONS")
print("="*80 + "\n")

if len(weekly_weeks) < 14:
    manque = 14 - len(weekly_weeks)
    print(f"1. Accumuler {manque} semaines supplementaires pour mode PRODUCTION")
    print(f"   - Continuer collecte quotidienne (17h)")
    print(f"   - Agregation hebdomadaire automatique (lundi 8h)")

if with_indicators < weekly_count * 0.9:
    print(f"2. Recalculer indicateurs WEEKLY")
    print(f"   python brvm_pipeline/pipeline_weekly.py --indicators")

if len(daily_dates) >= 65 and len(weekly_weeks) >= 14:
    print("OK Donnees suffisantes pour:")
    print("   - Generation TOP5 credible")
    print("   - Backtest fiable")
    print("   - Detection opportunites")
    print("\n   Lancer: python top5_engine.py --week 2026-W07")

print("\n" + "="*80 + "\n")

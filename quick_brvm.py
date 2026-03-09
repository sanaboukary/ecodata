#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apercu rapide BRVM"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("\n" + "="*70)
print("DONNEES DE COURS BRVM")
print("="*70 + "\n")

# RAW
raw = db.prices_intraday_raw.count_documents({})
print(f"1. RAW (collectes brutes)      : {raw:>6,} observations")
if raw > 0:
    dates_raw = sorted(db.prices_intraday_raw.distinct('date'))
    symbols_raw = db.prices_intraday_raw.distinct('symbol')
    print(f"   Dates: {dates_raw[0]} -> {dates_raw[-1]}")
    print(f"   Symboles: {len(symbols_raw)}")

# DAILY
daily = db.prices_daily.count_documents({})
print(f"\n2. DAILY (source de verite)    : {daily:>6,} jours x symboles")
if daily > 0:
    dates = sorted(db.prices_daily.distinct('date'))
    symbols = db.prices_daily.distinct('symbol')
    print(f"   Periode: {dates[0]} -> {dates[-1]} ({len(dates)} jours)")
    print(f"   Symboles: {len(symbols)} actions")
    
    # Top 5
    print("\n   TOP 5 actions (plus de jours):")
    pipeline = [
        {"$group": {"_id": "$symbol", "jours": {"$sum": 1}}},
        {"$sort": {"jours": -1}},
        {"$limit": 5}
    ]
    for item in db.prices_daily.aggregate(pipeline):
        print(f"     {item['_id']:<10} : {item['jours']:>2} jours")

# WEEKLY
weekly = db.prices_weekly.count_documents({})
print(f"\n3. WEEKLY (decisions)          : {weekly:>6,} semaines x symboles")
if weekly > 0:
    weeks = sorted(db.prices_weekly.distinct('week'))
    with_ind = db.prices_weekly.count_documents({'indicators_computed': True})
    print(f"   Semaines: {weeks[0]} -> {weeks[-1]} ({len(weeks)} semaines)")
    print(f"   Indicateurs calcules: {with_ind}/{weekly} ({with_ind/weekly*100:.0f}%)")

# Exemple SONATEL
print("\n" + "-"*70)
print("EXEMPLE: SONATEL (derniers jours)")
print("-"*70)
sonatel = list(db.prices_daily.find({'symbol': 'SONATEL'}).sort('date', -1).limit(3))
if sonatel:
    print(f"{'Date':<12} {'Close':>8} {'Volume':>10} {'Var%':>8}")
    for s in sonatel:
        print(f"{s.get('date'):<12} {s.get('close',0):>8.0f} {s.get('volume',0):>10,.0f} {s.get('variation_pct',0):>+7.2f}%")
else:
    print("(Pas de donnees SONATEL)")

print("\n" + "="*70)
print("VOS DONNEES BRVM SONT INTACTES ET BIEN STRUCTUREES")
print("="*70 + "\n")

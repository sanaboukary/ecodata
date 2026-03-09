#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AUDIT DONNEES WEEKLY - Pourquoi 16/17 semaines mortes?
"""
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

print("="*80)
print("AUDIT DONNEES WEEKLY")
print("="*80 + "\n")

# Examiner semaines pour SNTS en detail
symbol = 'SNTS'
weeks = list(db.prices_weekly.find({'symbol': symbol}).sort('week', 1))

print(f"ACTION: {symbol}")
print(f"Total semaines: {len(weeks)}\n")

print(f"{'Week':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Volume':>10} {'Status'}")
print("-"*80)

for w in weeks:
    week = w.get('week', 'N/A')
    open_p = w.get('open', 0)
    high = w.get('high', 0)
    low = w.get('low', 0)
    close = w.get('close', 0)
    volume = w.get('volume', 0)
    
    # Check si semaine morte
    is_dead = False
    reason = []
    
    if volume == 0:
        is_dead = True
        reason.append("VOL=0")
    
    if high == low == close:
        is_dead = True
        reason.append("BLOQUE")
    
    if open_p > 0:
        var_pct = abs((close - open_p) / open_p * 100)
        if var_pct < 0.1:
            is_dead = True
            reason.append(f"VAR<0.1%")
    
    status = "MORTE: " + ", ".join(reason) if is_dead else "ACTIVE"
    
    print(f"{week:<12} {open_p:>8.0f} {high:>8.0f} {low:>8.0f} {close:>8.0f} {volume:>10.0f} {status}")

# Stats globales
print("\n" + "="*80)
print("STATS GLOBALES WEEKLY")
print("="*80 + "\n")

total_weeks = db.prices_weekly.count_documents({})
weeks_no_volume = db.prices_weekly.count_documents({'volume': 0})
weeks_no_ohlc = db.prices_weekly.count_documents({
    '$expr': {
        '$and': [
            {'$eq': ['$high', '$low']},
            {'$eq': ['$high', '$close']}
        ]
    }
})

print(f"Total semaines: {total_weeks:,}")
print(f"Semaines volume=0: {weeks_no_volume:,} ({weeks_no_volume/total_weeks*100:.1f}%)")
print(f"Semaines prix bloques: {weeks_no_ohlc:,} ({weeks_no_ohlc/total_weeks*100:.1f}%)")

# Source du probleme
print("\n" + "="*80)
print("DIAGNOSTIC")
print("="*80 + "\n")

if weeks_no_volume > total_weeks * 0.5:
    print("PROBLEME 1: Plus de 50% des semaines ont volume=0")
    print("  => Rebuild weekly a ete fait AVANT restauration des donnees daily")
    print("  => SOLUTION: Rebuild WEEKLY depuis les 72 jours daily restaures")

if weeks_no_ohlc > total_weeks * 0.3:
    print("\nPROBLEME 2: Plus de 30% des semaines ont prix bloques (high=low=close)")
    print("  => Donnees daily aggregees ont des problemes")
    print("  => SOLUTION: Verifier qualite prices_daily avant rebuild")

print("\n" + "="*80)
print("ACTION REQUISE")
print("="*80)
print("\n1. DELETE toutes les semaines weekly actuelles")
print("2. REBUILD complet depuis prices_daily (72 jours)")
print("3. RECALCUL indicateurs avec ATR BRVM PRO")
print("\nCommande:")
print("  python brvm_pipeline/pipeline_weekly.py --rebuild")

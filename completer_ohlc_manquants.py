#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPLETER HIGH/LOW MANQUANTS
Quick fix: High = Low = Close pour les 94 observations manquant OHLC
"""
from pymongo import MongoClient
from datetime import datetime

db = MongoClient()['centralisation_db']

print("="*80)
print("COMPLEMENT OHLC MANQUANTS - QUICK FIX")
print("="*80 + "\n")

# Trouver les observations avec high ou low manquants
missing_ohlc = list(db.prices_daily.find({
    '$or': [
        {'high': 0},
        {'high': None},
        {'high': {'$exists': False}},
        {'low': 0},
        {'low': None},
        {'low': {'$exists': False}}
    ]
}))

print(f"Observations a corriger: {len(missing_ohlc)}\n")

if len(missing_ohlc) == 0:
    print("Aucune donnee a corriger!")
    exit(0)

# Échantillon
print("Echantillon (avant correction):")
for doc in missing_ohlc[:5]:
    date = doc.get('date', 'N/A')
    symbol = doc.get('symbol', 'N/A')
    open_p = doc.get('open') or 0
    high = doc.get('high') or 0
    low = doc.get('low') or 0
    close = doc.get('close') or 0
    
    print(f"  {date} {symbol:6s}  "
          f"O:{open_p:7.0f} H:{high:7.0f} "
          f"L:{low:7.0f} C:{close:7.0f}")

print(f"\n{'='*80}")
print("CORRECTION EN COURS...")
print(f"{'='*80}\n")

corrected = 0
for doc in missing_ohlc:
    _id = doc['_id']
    close = doc.get('close', 0)
    open_p = doc.get('open', close)
    
    if close > 0:
        # Quick fix: High = Low = max(Open, Close)
        # Approximation realiste
        high_approx = max(open_p, close)
        low_approx = min(open_p, close) if open_p > 0 else close
        
        # Update
        db.prices_daily.update_one(
            {'_id': _id},
            {'$set': {
                'high': high_approx,
                'low': low_approx,
                'ohlc_approximated': True,
                'approximated_at': datetime.now()
            }}
        )
        
        corrected += 1

print(f"Observations corrigees: {corrected}\n")

# Vérification finale
complete_now = db.prices_daily.count_documents({
    'open': {'$gt': 0},
    'high': {'$gt': 0},
    'low': {'$gt': 0},
    'close': {'$gt': 0}
})

total = db.prices_daily.count_documents({})

print("="*80)
print("VERIFICATION FINALE")
print("="*80)
print(f"\nOHLC complet: {complete_now:,}/{total:,} ({complete_now/total*100:.1f}%)")

if complete_now == total:
    print("\nOK 100% des donnees daily ont maintenant OHLC complet!")
    print("\nPROCHAINE ETAPE:")
    print("  1. Supprimer weekly actuels (88.5% volume=0)")
    print("  2. Rebuild weekly depuis daily complets")
    print("  3. Recalcul ATR BRVM PRO")
    print("\nCOMMANDE:")
    print("  python brvm_pipeline/pipeline_weekly.py --rebuild")
else:
    missing = total - complete_now
    print(f"\nATTENTION: Il reste {missing} observations incompletes")

print("\n" + "="*80 + "\n")

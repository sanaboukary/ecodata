#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

print("="*80)
print("AUDIT OHLC PRICES_DAILY")
print("="*80 + "\n")

total = db.prices_daily.count_documents({})

# Problèmes OHLC
missing_high = db.prices_daily.count_documents({'$or': [{'high': 0}, {'high': None}, {'high': {'$exists': False}}]})
missing_low = db.prices_daily.count_documents({'$or': [{'low': 0}, {'low': None}, {'low': {'$exists': False}}]})
missing_open = db.prices_daily.count_documents({'$or': [{'open': 0}, {'open': None}, {'open': {'$exists': False}}]})

# Données complètes
complete = db.prices_daily.count_documents({
    'open': {'$gt': 0},
    'high': {'$gt': 0},
    'low': {'$gt': 0},
    'close': {'$gt': 0}
})

print(f"Total observations: {total:,}\n")
print(f"OHLC manquants:")
print(f"  High = 0/null: {missing_high:,} ({missing_high/total*100:.1f}%)")
print(f"  Low = 0/null:  {missing_low:,} ({missing_low/total*100:.1f}%)")
print(f"  Open = 0/null: {missing_open:,} ({missing_open/total*100:.1f}%)")
print(f"\nOHLC complet: {complete:,} ({complete/total*100:.1f}%)")

# Par source
print("\n" + "="*80)
print("PAR SOURCE DE RESTAURATION")
print("="*80 + "\n")

sources = db.prices_daily.distinct('restored_from')
for source in sources:
    if source:
        count_source = db.prices_daily.count_documents({'restored_from': source})
        complete_source = db.prices_daily.count_documents({
            'restored_from': source,
            'open': {'$gt': 0},
            'high': {'$gt': 0},
            'low': {'$gt': 0},
            'close': {'$gt': 0}
        })
        print(f"{source:30s}: {count_source:5,} dont {complete_source:5,} complets ({complete_source/count_source*100:.1f}%)")

# Recommandation
print("\n" + "="*80)
print("SOLUTION")
print("="*80 + "\n")

if missing_high > total * 0.05:
    print("PROBLEME: Plus de 5% des donnees manquent high/low")
    print("\nCAUSE:")
    print("  - CSV_HISTORIQUE n'a que close+volume (pas OHLC)")
    print("  - Restauration a utilise CSV_HISTORIQUE comme fallback")
    print("\nSOLUTION 1 (Quick fix):")
    print("  - Completer high/low manquants avec close (approximation)")
    print("  - High = Low = Close (flat)")
    print("  - Permet rebuild weekly immédiat")
    print("\nSOLUTION 2 (Proper fix):")
    print("  - Re-restaurer en privilegiant BRVM_AGGREGATED (OHLC complet)")
    print("  - Fallback CSV_HISTORIQUE seulement si AGGREGATED manque")
    print("\nCOMMANDE:")
    print("  python completer_ohlc_manquants.py   # Quick fix")
    print("  python restauration_brvm_production.py --force  # Proper fix")

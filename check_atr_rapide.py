#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICATION RAPIDE ATR
"""
from pymongo import MongoClient
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# ATR actuels en DB
all_weekly = list(db.prices_weekly.find({'atr_pct': {'$exists': True, '$ne': None}}))

if all_weekly:
    atr_values = [doc['atr_pct'] for doc in all_weekly if doc.get('atr_pct') is not None]
    
    if atr_values:
        avg_atr = sum(atr_values) / len(atr_values)
        max_atr = max(atr_values)
        
        print(f"Total: {len(atr_values)} observations")
        print(f"ATR moyen: {avg_atr:.2f}%")
        print(f"ATR max: {max_atr:.2f}%")
        
        # Outliers
        outliers = [a for a in atr_values if a > 40]
        if outliers:
            print(f"\nOUTLIERS (>40%): {len(outliers)}")
            print(f"Valeurs: {sorted(outliers, reverse=True)[:10]}")
        else:
            print("\nOK - Aucun outlier >40%")
        
        # Distribution
        ideal = len([a for a in atr_values if 8 <= a <= 18])
        print(f"\nZone IDEALE (8-18%): {ideal} ({ideal/len(atr_values)*100:.1f}%)")
        
        # Tradables
        tradable = db.prices_weekly.count_documents({'tradable': True})
        print(f"Tradables (6-25%): {tradable}")

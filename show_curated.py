#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apercu curated_observations - version simple"""
import os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("APERCU curated_observations")
print("="*80 + "\n")

# Total
total = db.curated_observations.count_documents({})
print(f"Total documents: {total:,}\n")

# Echantillon
sample = db.curated_observations.find_one()
if sample:
    print("STRUCTURE (champs disponibles):")
    print("-"*80)
    for key in list(sample.keys())[:20]:
        print(f"  - {key}")

# Symboles
print("\n\nSYMBOLES:")
print("-"*80)
symbols = db.curated_observations.distinct('symbol')
print(f"Total symboles uniques: {len(symbols)}")
print(f"Exemples: {', '.join(symbols[:10])}")

# Sources
print("\n\nSOURCES:")
print("-"*80)
sources = db.curated_observations.distinct('source')
for src in sources[:5]:
    count = db.curated_observations.count_documents({'source': src})
    print(f"  {src:<30} : {count:>6,} docs")

# Dates
print("\n\nDATES:")
print("-"*80)
dates = db.curated_observations.distinct('date')
if dates:
    dates = sorted([d for d in dates if d])
    print(f"  Premiere: {dates[0]}")
    print(f"  Derniere: {dates[-1]}")
    print(f"  Total: {len(dates)} dates")

# Exemple concret
print("\n\nEXEMPLE:")
print("-"*80)
ex = db.curated_observations.find_one({'symbol': 'SONATEL'})
if ex:
    fields = ['symbol', 'date', 'price', 'close', 'volume', 'source']
    for f in fields:
        if f in ex:
            print(f"  {f}: {ex[f]}")

print("\n" + "="*80)
print("\nCONCLUSION: Ces donnees sont votre historique BRVM collecte au fil du temps.")
print("Elles servent de source pour construire DAILY et WEEKLY.")
print("="*80 + "\n")

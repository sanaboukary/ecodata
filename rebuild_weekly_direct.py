#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REBUILD WEEKLY - DIRECT ET VERBEUX
"""
import sys
from pymongo import MongoClient

print("="*80)
print("REBUILD WEEKLY DIRECT")
print("="*80 + "\n")

db = MongoClient()['centralisation_db']

# Step 1: Supprimer anciennes weekly
print("ETAPE 1: Suppression anciennes weekly...")
result = db.prices_weekly.delete_many({})
print(f"  OK - Supprime: {result.deleted_count} observations\n")

# Step 2: Lancer rebuild
print("ETAPE 2: Import module pipeline_weekly...")
sys.path.insert(0, 'brvm_pipeline')

try:
    from pipeline_weekly import rebuild_all_weekly
    print("  OK - Module charge\n")
    
    print("ETAPE 3: Execution rebuild_all_weekly()...")
    rebuild_all_weekly()
    print("\n  OK - Rebuild termine\n")
    
except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Verifier resultats
print("ETAPE 4: Verification resultats...")
weekly_count = db.prices_weekly.count_documents({})
weeks_count = len(db.prices_weekly.distinct('week'))
with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})

print(f"  Total observations: {weekly_count}")
print(f"  Semaines uniques: {weeks_count}")
print(f"  Avec indicateurs: {with_indicators} ({with_indicators/weekly_count*100:.1f}%)")

# Verifier ATR
atr_docs = list(db.prices_weekly.find({'atr_pct': {'$exists': True, '$ne': None}}).limit(5))
if atr_docs:
    print(f"\n  Echantillon ATR:")
    for doc in atr_docs:
        print(f"    {doc['symbol']}: {doc.get('atr_pct')}% (tradable: {doc.get('tradable')})")

print("\n" + "="*80)
print("REBUILD TERMINE")
print("="*80 + "\n")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérification rapide des données collectées par source"""

import sys
import io
from pymongo import MongoClient

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*100)
print(" " * 30 + "VERIFICATION COLLECTE - TOUTES SOURCES")
print("="*100)

try:
    client = MongoClient('mongodb://localhost:27017')
    db = client['centralisation_db']
    
    # Total
    total = db.curated_observations.count_documents({})
    print(f"\nTOTAL OBSERVATIONS: {total:,}")
    
    # Par source
    print("\n" + "-"*100)
    print("SOURCES COLLECTEES:")
    print("-"*100)
    
    sources = db.curated_observations.distinct('source')
    
    for source in sorted(sources):
        count = db.curated_observations.count_documents({'source': source})
        keys = db.curated_observations.distinct('key', {'source': source})
        dates = db.curated_observations.distinct('ts', {'source': source})
        
        print(f"\n{source}:")
        print(f"   Documents: {count:,}")
        print(f"   Keys/Indicateurs: {len(keys)}")
        print(f"   Dates distinctes: {len(dates)}")
        
        if dates:
            dates_sorted = sorted(dates)
            print(f"   Periode: {dates_sorted[0]} -> {dates_sorted[-1]}")
        
        # Exemples de keys
        if len(keys) <= 10:
            print(f"   Keys: {', '.join(sorted(keys)[:10])}")
        else:
            print(f"   Exemples keys: {', '.join(sorted(keys)[:5])}...")
    
    # Sources attendues
    print("\n" + "="*100)
    print("VERIFICATION SOURCES ATTENDUES:")
    print("="*100)
    
    expected = {
        'BRVM': 'Bourse Regionale (47 actions)',
        'WorldBank': 'Banque Mondiale (indicateurs macro)',
        'IMF': 'Fonds Monetaire International',
        'AfDB': 'Banque Africaine de Developpement', 
        'UN_SDG': 'Objectifs Developpement Durable ONU',
        'AI_ANALYSIS': 'Recommandations IA'
    }
    
    for source, desc in expected.items():
        count = db.curated_observations.count_documents({'source': source})
        status = "OK" if count > 0 else "MANQUANT"
        symbol = "✓" if count > 0 else "✗"
        print(f"   {symbol} {source:<20} ({desc:<45}) {count:>8,} docs")
    
    # Collections
    print("\n" + "="*100)
    print("COLLECTIONS MONGODB:")
    print("="*100)
    
    collections = db.list_collection_names()
    for coll in collections:
        count = db[coll].count_documents({})
        print(f"   - {coll:<30} {count:>10,} documents")
    
    client.close()
    
    print("\n" + "="*100)
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()

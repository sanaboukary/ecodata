#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXAMINER STRUCTURE DES DONNÉES BRVM DANS curated_observations
"""
from pymongo import MongoClient
import json
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("STRUCTURE DES DONNEES BRVM")
print("="*80 + "\n")

brvm_sources = ['BRVM', 'BRVM_AGGREGATED', 'BRVM_CSV_HISTORIQUE', 'BRVM_CSV_RESTAURATION']

for source in brvm_sources:
    count = db.curated_observations.count_documents({'source': source})
    if count > 0:
        print(f"\n{'='*80}")
        print(f"SOURCE: {source} ({count:,} observations)")
        print(f"{'='*80}")
        
        # Prendre 3 exemples
        samples = list(db.curated_observations.find(
            {'source': source}
        ).limit(3))
        
        for i, doc in enumerate(samples, 1):
            print(f"\nExemple {i}:")
            print("-"*40)
            
            # Afficher tous les champs de niveau supérieur
            for key in doc.keys():
                if key != '_id':
                    value = doc[key]
                    if isinstance(value, dict):
                        print(f"  {key}: {json.dumps(value, indent=4, default=str)}")
                    else:
                        print(f"  {key}: {value}")
            
            # Si attrs existe, montrer sa structure
            if 'attrs' in doc:
                print(f"\n  Champs dans 'attrs':")
                for attr_key in doc['attrs'].keys():
                    print(f"    - {attr_key}: {doc['attrs'][attr_key]}")

print("\n" + "="*80)
print("\n✅ Analyse de structure terminée")

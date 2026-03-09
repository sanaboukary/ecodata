#!/usr/bin/env python3
"""Import massif des donnees historiques CSV vers MongoDB"""

import sys
import os
import csv
from datetime import datetime
from pymongo import MongoClient

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("="*80)
print("IMPORT DONNEES HISTORIQUES BRVM")
print("="*80)

fichier_csv = "historique_brvm.csv"

if not os.path.exists(fichier_csv):
    print(f"Erreur: {fichier_csv} introuvable")
    sys.exit(1)

# Lire CSV
with open(fichier_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"\n{len(rows)} lignes trouvees dans {fichier_csv}")

# Preparer documents pour MongoDB
documents = []
dates_set = set()

for row in rows:
    try:
        date = row['DATE']
        symbol = row['SYMBOL']
        close = float(row['CLOSE'].replace(',', ''))
        volume = float(row['VOLUME'].replace(',', '')) if row['VOLUME'] else 0
        variation = float(row['VARIATION'].replace(',', '')) if row['VARIATION'] else 0
        
        doc = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': symbol,
            'ts': date,
            'value': close,
            'attrs': {
                'close': close,
                'volume': volume,
                'variation_pct': variation,
                'data_quality': 'REAL_HISTORICAL',
                'import_source': 'historique_brvm.csv',
                'import_timestamp': datetime.now().isoformat()
            }
        }
        
        documents.append(doc)
        dates_set.add(date)
        
    except Exception as e:
        print(f"Erreur ligne {row}: {e}")

print(f"\n{len(documents)} documents prepares")
print(f"{len(dates_set)} dates uniques")

# Supprimer anciennes donnees BRVM pour eviter doublons
print("\nSuppression anciennes donnees BRVM...")
deleted = db.curated_observations.delete_many({'source': 'BRVM'})
print(f"   {deleted.deleted_count} documents supprimes")

# Inserer nouveaux documents
if documents:
    print(f"\nInsertion {len(documents)} documents...")
    result = db.curated_observations.insert_many(documents)
    print(f"   {len(result.inserted_ids)} documents inseres")
    
    # Verification
    total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
    actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
    dates = db.curated_observations.distinct('ts', {'source': 'BRVM'})
    
    print(f"\nVERIFICATION:")
    print(f"   Total observations BRVM: {total_brvm}")
    print(f"   Actions uniques: {len(actions)}")
    print(f"   Dates uniques: {len(dates)}")
    print(f"   Periode: {min(dates)} -> {max(dates)}")
    
    # Echantillon par action
    print(f"\n   Observations par action (10 premieres):")
    for action in sorted(actions)[:10]:
        count = db.curated_observations.count_documents({'source': 'BRVM', 'key': action})
        print(f"      {action}: {count} obs")

client.close()

print("\n" + "="*80)
print("IMPORT TERMINE")
print("="*80)

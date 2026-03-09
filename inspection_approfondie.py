#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspection approfondie MongoDB - Toutes collections et sources"""

import sys
from pymongo import MongoClient

# Fix encoding pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("="*100)
print("INSPECTION APPROFONDIE - TOUTES SOURCES")
print("="*100)

# 1. Lister TOUTES les collections
print("\n1. COLLECTIONS DISPONIBLES:")
print("-" * 100)
for coll_name in db.list_collection_names():
    count = db[coll_name].count_documents({})
    print(f"   {coll_name:<30} {count:>10,} documents")

# 2. Pour chaque collection, lister les sources
print("\n" + "="*100)
print("2. SOURCES PAR COLLECTION")
print("="*100)

for coll_name in db.list_collection_names():
    coll = db[coll_name]
    
    # Vérifier si le champ 'source' existe
    if coll.find_one({'source': {'$exists': True}}):
        print(f"\nCollection: {coll_name}")
        print("-" * 100)
        
        sources = coll.distinct('source')
        for source in sorted(sources):
            count = coll.count_documents({'source': source})
            
            # Datasets pour cette source
            datasets = coll.distinct('dataset', {'source': source})
            
            # Keys/indicateurs
            keys = coll.distinct('key', {'source': source})
            
            # Plage de dates
            dates = coll.distinct('ts', {'source': source})
            dates_sorted = sorted(dates) if dates else []
            
            print(f"\n   SOURCE: {source}")
            print(f"      Documents: {count:,}")
            print(f"      Keys/Indicateurs: {len(keys)}")
            if datasets and datasets != [None]:
                print(f"      Datasets: {len(datasets)} - {', '.join(str(d) for d in datasets[:3])}")
            if dates_sorted:
                print(f"      Dates: {len(dates_sorted)} ({dates_sorted[0]} -> {dates_sorted[-1]})")
            
            # Exemple de keys
            if len(keys) > 0:
                print(f"      Exemples keys: {', '.join(str(k) for k in sorted(keys)[:5])}")

# 3. Recherche de termes spécifiques dans tous les documents
print("\n" + "="*100)
print("3. RECHERCHE PAR MOTS-CLES")
print("="*100)

keywords = ['WorldBank', 'World Bank', 'IMF', 'AfDB', 'UN_SDG', 'UN', 'SDG']

for keyword in keywords:
    # Recherche dans source
    count_source = db.curated_observations.count_documents({
        'source': {'$regex': keyword, '$options': 'i'}
    })
    
    # Recherche dans dataset
    count_dataset = db.curated_observations.count_documents({
        'dataset': {'$regex': keyword, '$options': 'i'}
    })
    
    # Recherche dans key
    count_key = db.curated_observations.count_documents({
        'key': {'$regex': keyword, '$options': 'i'}
    })
    
    total = count_source + count_dataset + count_key
    if total > 0:
        print(f"\n   '{keyword}':")
        if count_source > 0:
            print(f"      Dans 'source': {count_source:,} docs")
        if count_dataset > 0:
            print(f"      Dans 'dataset': {count_dataset:,} docs")
        if count_key > 0:
            print(f"      Dans 'key': {count_key:,} docs")

# 4. Vérifier raw_events et ingestion_runs
print("\n" + "="*100)
print("4. HISTORIQUE INGESTION (ingestion_runs)")
print("="*100)

if 'ingestion_runs' in db.list_collection_names():
    runs = db.ingestion_runs.find().sort('start_time', -1).limit(20)
    
    print(f"\n{'Source':<20} {'Status':<10} {'Date':<20} {'Observations':<15}")
    print("-" * 80)
    
    for run in runs:
        source = run.get('source', 'N/A')
        status = run.get('status', 'N/A')
        start = str(run.get('start_time', 'N/A'))[:19]
        obs = run.get('obs_count', 0)
        print(f"{source:<20} {status:<10} {start:<20} {obs:<15,}")

# 5. Statistiques détaillées par source
print("\n" + "="*100)
print("5. STATISTIQUES DETAILLEES")
print("="*100)

sources = db.curated_observations.distinct('source')
for source in sorted(sources):
    print(f"\nSOURCE: {source}")
    print("-" * 100)
    
    total = db.curated_observations.count_documents({'source': source})
    keys = db.curated_observations.distinct('key', {'source': source})
    dates = db.curated_observations.distinct('ts', {'source': source})
    
    print(f"   Total observations: {total:,}")
    print(f"   Indicateurs/Actions: {len(keys)}")
    print(f"   Periodes: {len(dates)} dates")
    
    # Top 5 indicateurs/keys
    print(f"\n   Top 5 indicateurs:")
    pipeline = [
        {'$match': {'source': source}},
        {'$group': {'_id': '$key', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    
    for item in db.curated_observations.aggregate(pipeline):
        key = item['_id']
        count = item['count']
        
        # Exemple de valeur
        doc = db.curated_observations.find_one({'source': source, 'key': key})
        value = doc.get('value', 'N/A') if doc else 'N/A'
        
        print(f"      {key:<30} {count:>8,} obs  (ex: {value})")

client.close()

print("\n" + "="*100)
print("FIN INSPECTION")
print("="*100)

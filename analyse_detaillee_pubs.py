#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE DÉTAILLÉE - Où sont les publications BRVM ?
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ANALYSE DETAILLEE - PUBLICATIONS BRVM")
print("="*80)

# Analyser curated_observations en détail
print("\n[1] CURATED_OBSERVATIONS - SOURCE ANALYSIS")
coll = db['curated_observations']

# Grouper par source
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
sources = list(coll.aggregate(pipeline))
print("\nRepartition par source:")
for s in sources:
    print(f"   {s['_id']}: {s['count']:,} documents")

# Analyser les datasets
pipeline = [
    {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
datasets = list(coll.aggregate(pipeline))
print("\nRepartition par dataset:")
for d in datasets[:20]:
    print(f"   {d['_id']}: {d['count']:,} documents")

# Chercher les documents BRVM
print("\n\nEXEMPLES CURATED_OBSERVATIONS:")
for i, doc in enumerate(coll.find({'source': 'AI_ANALYSIS'}).limit(5), 1):
    print(f"\nExample {i}:")
    print(f"  dataset: {doc.get('dataset')}")
    print(f"  key: {doc.get('key')}")
    print(f"  sector: {doc.get('sector')}")
    print(f"  ts: {doc.get('ts')}")
    print(f"  value: {doc.get('value')}")
    if 'attrs' in doc:
        print(f"  attrs: {json.dumps(doc['attrs'], indent=4)[:200]}...")

# Analyser raw_events
print("\n\n" + "="*80)
print("[2] RAW_EVENTS - SOURCE ANALYSIS")
coll = db['raw_events']

# Grouper par source
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
sources = list(coll.aggregate(pipeline))
print("\nRepartition par source:")
for s in sources:
    print(f"   {s['_id']}: {s['count']:,} documents")

# Chercher les plus récents
print("\n\nDOCUMENTS LES PLUS RECENTS (TOP 10):")
for i, doc in enumerate(coll.find().sort('fetched_at', -1).limit(10), 1):
    print(f"\n{i}. {doc.get('source')} - {doc.get('fetched_at')}")
    if 'payload' in doc:
        payload = doc['payload']
        if isinstance(payload, dict):
            print(f"   Payload keys: {list(payload.keys())}")
            # Afficher un extrait
            for key in list(payload.keys())[:3]:
                val = payload[key]
                if isinstance(val, str) and len(val) > 60:
                    print(f"   {key}: {val[:60]}...")
                elif isinstance(val, (list, dict)):
                    print(f"   {key}: {type(val).__name__}({len(val)})")
                else:
                    print(f"   {key}: {val}")

# Chercher spécifiquement des publications BRVM
print("\n\n" + "="*80)
print("[3] RECHERCHE PUBLICATIONS BRVM")
print("="*80)

# Dans ingestion_runs
coll = db['ingestion_runs']
print(f"\nINGESTION_RUNS: {coll.count_documents({}):,} documents")

# Récents
recent = coll.find().sort('_id', -1).limit(5)
print("\n5 derniers runs:")
for i, doc in enumerate(recent, 1):
    print(f"\n{i}. ID: {doc['_id']}")
    for key in doc.keys():
        if key != '_id':
            val = doc[key]
            if isinstance(val, str) and len(val) > 60:
                print(f"   {key}: {val[:60]}...")
            else:
                print(f"   {key}: {val}")

# Chercher dans toutes les collections avec "brvm" dans le nom
print("\n\n" + "="*80)
print("[4] COLLECTIONS BRVM")
print("="*80)

all_collections = db.list_collection_names()
for coll_name in all_collections:
    coll = db[coll_name]
    count = coll.count_documents({})
    
    # Chercher des documents avec "brvm" ou des tickers
    if count > 0:
        sample = coll.find_one()
        has_brvm_data = False
        
        # Vérifier si contient des données BRVM
        for key in ['ticker', 'symbole', 'action', 'code_isin']:
            if key in str(sample).lower():
                has_brvm_data = True
                break
        
        if has_brvm_data or 'brvm' in coll_name.lower():
            print(f"\n{coll_name}: {count:,} documents")
            if sample:
                print("  Sample keys:", list(sample.keys())[:10])

print("\n" + "="*80)
print("FIN ANALYSE")
print("="*80)

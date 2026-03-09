#!/usr/bin/env python3
"""Inspection complète MongoDB pour trouver données historiques BRVM"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("="*80)
print("🔍 INSPECTION MONGODB - DONNÉES BRVM")
print("="*80)

# 1. Toutes les collections
print("\n📚 Collections disponibles:")
collections = db.list_collection_names()
for coll in collections:
    count = db[coll].count_documents({})
    print(f"   {coll}: {count} documents")

# 2. Collection curated_observations
print("\n" + "="*80)
print("📊 COLLECTION: curated_observations")
print("="*80)

total = db.curated_observations.count_documents({})
print(f"\n📈 Total documents: {total}")

# Sources
print("\n📦 Sources disponibles:")
sources = db.curated_observations.distinct('source')
for source in sources:
    count = db.curated_observations.count_documents({'source': source})
    print(f"   {source}: {count} documents")

# BRVM détaillé
brvm_total = db.curated_observations.count_documents({'source': 'BRVM'})
print(f"\n🎯 BRVM: {brvm_total} documents")

if brvm_total > 0:
    # Datasets BRVM
    print("\n📋 Datasets BRVM:")
    datasets = db.curated_observations.distinct('dataset', {'source': 'BRVM'})
    for dataset in datasets:
        count = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': dataset})
        print(f"   {dataset}: {count} documents")
    
    # Actions (keys)
    print("\n🏢 Actions BRVM:")
    keys = db.curated_observations.distinct('key', {'source': 'BRVM'})
    print(f"   Total actions: {len(keys)}")
    
    # Pour chaque action, compter observations
    print(f"\n📊 Observations par action (10 premières):")
    print(f"{'Action':<15} {'Observations':<15} {'Dates'}")
    print("-" * 70)
    
    for key in sorted(keys)[:10]:
        count = db.curated_observations.count_documents({'source': 'BRVM', 'key': key})
        
        # Trouver plage de dates
        docs = list(db.curated_observations.find(
            {'source': 'BRVM', 'key': key}
        ).sort('ts', 1).limit(1))
        
        date_debut = docs[0]['ts'] if docs else 'N/A'
        
        docs_fin = list(db.curated_observations.find(
            {'source': 'BRVM', 'key': key}
        ).sort('ts', -1).limit(1))
        
        date_fin = docs_fin[0]['ts'] if docs_fin else 'N/A'
        
        print(f"{key:<15} {count:<15} {date_debut} → {date_fin}")
    
    # Exemple de document
    print("\n" + "="*80)
    print("📄 EXEMPLE DE DOCUMENT BRVM:")
    print("="*80)
    
    doc = db.curated_observations.find_one({'source': 'BRVM'})
    if doc:
        print(f"\n_id: {doc['_id']}")
        print(f"source: {doc.get('source')}")
        print(f"dataset: {doc.get('dataset')}")
        print(f"key: {doc.get('key')}")
        print(f"ts: {doc.get('ts')}")
        print(f"value: {doc.get('value')}")
        
        if 'attrs' in doc:
            print(f"\nattrs:")
            for k, v in doc['attrs'].items():
                print(f"   {k}: {v}")

# 3. Collection raw_events
print("\n" + "="*80)
print("📊 COLLECTION: raw_events")
print("="*80)

raw_total = db.raw_events.count_documents({})
print(f"\n📈 Total raw_events: {raw_total}")

if raw_total > 0:
    raw_sources = db.raw_events.distinct('source')
    print(f"\nSources raw_events:")
    for source in raw_sources:
        count = db.raw_events.count_documents({'source': source})
        print(f"   {source}: {count} documents")

print("\n" + "="*80)

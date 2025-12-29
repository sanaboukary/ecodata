#!/usr/bin/env python
"""Script de vérification des données collectées"""
from scripts.mongo_utils import get_db
from datetime import datetime

# Connexion à MongoDB
MONGO_URI = 'mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin'
db = get_db(MONGO_URI, 'centralisation_db')

print("=" * 60)
print("VÉRIFICATION DES DONNÉES COLLECTÉES")
print("=" * 60)

# 1. Collections disponibles
print("\n📁 COLLECTIONS DISPONIBLES:")
collections = db.list_collection_names()
for col in collections:
    if col not in ['__schema__', 'system.indexes']:
        print(f"  • {col}")

# 2. Comptage global
print("\n📊 COMPTAGE GLOBAL:")
raw_count = db.raw_events.count_documents({})
curated_count = db.curated_observations.count_documents({})
print(f"  • raw_events (traces brutes): {raw_count}")
print(f"  • curated_observations (données normalisées): {curated_count}")

# 3. Observations par source
print("\n🌍 OBSERVATIONS PAR SOURCE:")
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
for doc in db.curated_observations.aggregate(pipeline):
    source = doc['_id'] or 'Non spécifié'
    count = doc['count']
    print(f"  • {source}: {count} observations")

# 4. Dernières observations par source
print("\n🕒 DERNIÈRES OBSERVATIONS PAR SOURCE:")
sources = db.curated_observations.distinct('source')
for source in sources:
    if source:
        latest = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', -1)]
        )
        if latest:
            ts = latest.get('ts', 'N/A')
            key = latest.get('key', 'N/A')
            value = latest.get('value', 'N/A')
            print(f"  • {source}:")
            print(f"    - Clé: {key}")
            print(f"    - Valeur: {value}")
            print(f"    - Date: {ts}")

# 5. Événements bruts récents
print("\n📝 DERNIERS ÉVÉNEMENTS BRUTS:")
raw_events = db.raw_events.find().sort('timestamp', -1).limit(5)
for idx, event in enumerate(raw_events, 1):
    source = event.get('source', 'N/A')
    timestamp = event.get('timestamp', 'N/A')
    print(f"  {idx}. {source} - {timestamp}")

# 6. Statistiques par dataset
print("\n📈 OBSERVATIONS PAR DATASET:")
pipeline = [
    {'$group': {
        '_id': {'source': '$source', 'dataset': '$dataset'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'count': -1}}
]
for doc in db.curated_observations.aggregate(pipeline):
    source = doc['_id'].get('source', 'N/A')
    dataset = doc['_id'].get('dataset', 'N/A')
    count = doc['count']
    print(f"  • {source}/{dataset}: {count} observations")

# 7. Plage temporelle des données
print("\n📅 PLAGE TEMPORELLE DES DONNÉES:")
for source in sources:
    if source:
        oldest = db.curated_observations.find_one(
            {'source': source, 'ts': {'$exists': True}},
            sort=[('ts', 1)]
        )
        newest = db.curated_observations.find_one(
            {'source': source, 'ts': {'$exists': True}},
            sort=[('ts', -1)]
        )
        if oldest and newest:
            print(f"  • {source}:")
            print(f"    De: {oldest.get('ts', 'N/A')}")
            print(f"    À:  {newest.get('ts', 'N/A')}")

print("\n" + "=" * 60)
print("✅ VÉRIFICATION TERMINÉE")
print("=" * 60)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECHERCHE DES PUBLICATIONS BRVM DANS MONGODB
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("RECHERCHE PUBLICATIONS BRVM")
print("="*80)

# Lister toutes les collections
collections = db.list_collection_names()
print(f"\n{len(collections)} collections trouvees:")
for coll in collections:
    count = db[coll].count_documents({})
    print(f"   - {coll}: {count:,} documents")

print("\n" + "="*80)
print("ANALYSE COLLECTIONS CANDIDATES")
print("="*80)

# Chercher dans curated_observations
print("\n[1] CURATED_OBSERVATIONS")
coll = db['curated_observations']
count = coll.count_documents({})
print(f"Total: {count:,} documents")

sample = coll.find_one()
if sample:
    print("\nChamps disponibles:")
    for key in sorted(sample.keys()):
        print(f"   - {key}: {type(sample[key]).__name__}")

# Chercher les 7 derniers jours
seven_days_ago = datetime.now() - timedelta(days=7)
try:
    recent = coll.count_documents({'date': {'$gte': seven_days_ago}})
    print(f"\nDocuments recents (7j): {recent}")
except:
    pass

# Afficher 3 exemples
print("\nExemples:")
for i, doc in enumerate(coll.find().limit(3), 1):
    print(f"\n  Exemple {i}:")
    for key in ['titre', 'text', 'action', 'date', 'source']:
        if key in doc:
            val = doc[key]
            if isinstance(val, str) and len(val) > 60:
                print(f"    {key}: {val[:60]}...")
            else:
                print(f"    {key}: {val}")

# Chercher dans raw_events
print("\n" + "="*80)
print("[2] RAW_EVENTS")
coll = db['raw_events']
count = coll.count_documents({})
print(f"Total: {count:,} documents")

sample = coll.find_one()
if sample:
    print("\nChamps disponibles:")
    for key in sorted(sample.keys()):
        print(f"   - {key}: {type(sample[key]).__name__}")

# Chercher recent
try:
    recent = coll.count_documents({'timestamp': {'$gte': seven_days_ago}})
    print(f"\nDocuments recents (7j): {recent}")
except:
    try:
        recent = coll.count_documents({'date': {'$gte': seven_days_ago}})
        print(f"\nDocuments recents (7j, champ date): {recent}")
    except:
        pass

print("\nExemples:")
for i, doc in enumerate(coll.find().limit(3), 1):
    print(f"\n  Exemple {i}:")
    for key in list(doc.keys())[:10]:  # Premiers 10 champs
        val = doc[key]
        if isinstance(val, str) and len(val) > 60:
            print(f"    {key}: {val[:60]}...")
        elif isinstance(val, list):
            print(f"    {key}: list({len(val)} items)")
        elif isinstance(val, dict):
            print(f"    {key}: dict({len(val)} keys)")
        else:
            print(f"    {key}: {val}")

# Chercher autres collections avec "publication" dans le nom
print("\n" + "="*80)
print("AUTRES COLLECTIONS")
print("="*80)

for coll_name in collections:
    if 'pub' in coll_name.lower() or 'article' in coll_name.lower() or 'news' in coll_name.lower():
        coll = db[coll_name]
        count = coll.count_documents({})
        print(f"\n{coll_name}: {count:,} documents")
        
        if count > 0:
            sample = coll.find_one()
            if sample:
                print("  Champs:")
                for key in list(sample.keys())[:8]:
                    print(f"    - {key}")

print("\n" + "="*80)
print("FIN")
print("="*80)

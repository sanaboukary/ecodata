#!/usr/bin/env python3
"""Connexion directe MongoDB - centralisation_db"""

from pymongo import MongoClient

# Connexion directe
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("="*80)
print("📊 BASE DE DONNÉES: centralisation_db")
print("="*80)

# Collections
print("\n📚 Collections:")
for coll in db.list_collection_names():
    count = db[coll].count_documents({})
    print(f"   {coll}: {count:,} documents")

# curated_observations
print("\n" + "="*80)
print("📊 COLLECTION: curated_observations")
print("="*80)

if 'curated_observations' in db.list_collection_names():
    # Sources
    print("\n📦 Sources:")
    sources = db.curated_observations.distinct('source')
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        print(f"   {source}: {count:,} documents")
    
    # BRVM spécifique
    brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
    if brvm_count > 0:
        print(f"\n🎯 BRVM: {brvm_count:,} documents")
        
        # Actions BRVM
        actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
        print(f"   Actions: {len(actions)}")
        
        # Compter observations par action
        print(f"\n📊 Top 10 actions avec le plus d'historique:")
        print(f"{'Action':<12} {'Observations':<15} {'Début':<12} {'Fin':<12}")
        print("-" * 60)
        
        action_counts = []
        for action in actions:
            count = db.curated_observations.count_documents({'source': 'BRVM', 'key': action})
            action_counts.append((action, count))
        
        # Trier par nombre d'observations
        action_counts.sort(key=lambda x: x[1], reverse=True)
        
        for action, count in action_counts[:10]:
            # Dates
            docs = list(db.curated_observations.find(
                {'source': 'BRVM', 'key': action}
            ).sort('ts', 1).limit(1))
            debut = docs[0]['ts'] if docs else 'N/A'
            
            docs = list(db.curated_observations.find(
                {'source': 'BRVM', 'key': action}
            ).sort('ts', -1).limit(1))
            fin = docs[0]['ts'] if docs else 'N/A'
            
            print(f"{action:<12} {count:<15} {debut:<12} {fin:<12}")
        
        # Exemple document
        print(f"\n📄 Exemple document BRVM:")
        doc = db.curated_observations.find_one({'source': 'BRVM'})
        if doc:
            print(f"   key: {doc.get('key')}")
            print(f"   ts: {doc.get('ts')}")
            print(f"   value: {doc.get('value')}")
            print(f"   dataset: {doc.get('dataset', 'N/A')}")
            if 'attrs' in doc:
                print(f"   attrs: {list(doc['attrs'].keys())[:5]}")

client.close()
print("\n" + "="*80)

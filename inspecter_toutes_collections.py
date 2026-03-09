#!/usr/bin/env python3
"""Inspection complète de TOUTES les collections MongoDB"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')

print("="*80)
print("🔍 INSPECTION COMPLÈTE MongoDB")
print("="*80)

# Toutes les bases
print("\n📚 Bases de données disponibles:")
for db_name in client.list_database_names():
    if db_name not in ['admin', 'config', 'local']:
        db = client[db_name]
        total = sum(db[coll].count_documents({}) for coll in db.list_collection_names())
        print(f"   {db_name}: {total:,} documents")

# Focaliser sur centralisation_db
db = client['centralisation_db']

print("\n" + "="*80)
print("📊 BASE: centralisation_db")
print("="*80)

for coll_name in db.list_collection_names():
    coll = db[coll_name]
    count = coll.count_documents({})
    
    print(f"\n📂 {coll_name}: {count:,} documents")
    
    if count > 0:
        # Exemple de document
        doc = coll.find_one()
        print(f"   Structure: {list(doc.keys())[:8]}")
        
        # Si c'est curated_observations, détailler
        if coll_name == 'curated_observations':
            sources = coll.distinct('source')
            print(f"   Sources: {sources}")
            
            for source in sources:
                source_count = coll.count_documents({'source': source})
                print(f"      {source}: {source_count:,} docs")
                
                # Pour BRVM, vérifier les dates
                if source == 'BRVM':
                    pipeline = [
                        {'$match': {'source': 'BRVM'}},
                        {'$group': {
                            '_id': '$ts',
                            'count': {'$sum': 1}
                        }},
                        {'$sort': {'_id': 1}}
                    ]
                    dates = list(coll.aggregate(pipeline))
                    print(f"\n      📅 Dates disponibles pour BRVM:")
                    for d in dates[:10]:
                        print(f"         {d['_id']}: {d['count']} observations")
                    if len(dates) > 10:
                        print(f"         ... et {len(dates) - 10} autres dates")
        
        # Si c'est raw_events
        elif coll_name == 'raw_events':
            sources = coll.distinct('source')
            print(f"   Sources: {sources}")
            for source in sources:
                source_count = coll.count_documents({'source': source})
                print(f"      {source}: {source_count:,} docs")

client.close()
print("\n" + "="*80)

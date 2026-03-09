#!/usr/bin/env python3
"""Check MongoDB databases and collections"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

print("="*60)
print("BASES MONGODB DISPONIBLES")
print("="*60)

for db_name in client.list_database_names():
    if db_name not in ['admin', 'config', 'local']:
        print(f"\n📊 Base: {db_name}")
        db = client[db_name]
        
        for coll_name in db.list_collection_names():
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name}: {count} docs")
            
            # Si c'est curated_observations, montrer les sources
            if coll_name == "curated_observations" and count > 0:
                sources = db[coll_name].distinct("source")
                for src in sources:
                    src_count = db[coll_name].count_documents({"source": src})
                    print(f"      > {src}: {src_count}")

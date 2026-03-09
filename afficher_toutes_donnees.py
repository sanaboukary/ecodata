#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Affichage complet de toutes les données dans centralisation_db"""

import sys
from pymongo import MongoClient
from datetime import datetime

# Fix encoding pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("="*100)
print("TOUTES LES DONNEES - centralisation_db")
print("="*100)

# Pour chaque collection
for coll_name in db.list_collection_names():
    coll = db[coll_name]
    total = coll.count_documents({})
    
    print(f"\n{'='*100}")
    print(f"COLLECTION: {coll_name}")
    print(f"{'='*100}")
    print(f"Total documents: {total:,}")
    
    if total == 0:
        print("   Collection vide")
        continue
    
    # Si curated_observations
    if coll_name == 'curated_observations':
        sources = coll.distinct('source')
        
        for source in sources:
            source_docs = coll.count_documents({'source': source})
            print(f"\nSOURCE: {source} ({source_docs:,} documents)")
            print("-" * 100)
            
            # Distinct keys pour cette source
            keys = coll.distinct('key', {'source': source})
            print(f"   {len(keys)} cles/indicateurs uniques")
            
            # Dates disponibles
            dates = coll.distinct('ts', {'source': source})
            dates_sorted = sorted(dates)
            print(f"   {len(dates_sorted)} dates: {dates_sorted[0]} -> {dates_sorted[-1]}")
            
            # Datasets si disponibles
            datasets = coll.distinct('dataset', {'source': source})
            if datasets and datasets != [None]:
                print(f"   Datasets: {datasets}")
            
            # Exemples de données par clé
            print(f"\n   Detail par cle (top 20):")
            print(f"   {'Clé':<20} {'Observations':<15} {'Dernière valeur':<20} {'Date'}")
            print("   " + "-" * 90)
            
            for key in sorted(keys)[:20]:
                count = coll.count_documents({'source': source, 'key': key})
                
                # Dernier document
                last_doc = coll.find_one(
                    {'source': source, 'key': key},
                    sort=[('ts', -1)]
                )
                
                if last_doc:
                    value = last_doc.get('value', 'N/A')
                    ts = last_doc.get('ts', 'N/A')
                    
                    # Formater la valeur
                    if isinstance(value, (int, float)):
                        value_str = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                    else:
                        value_str = str(value)[:17]
                    
                    print(f"   {key:<20} {count:<15} {value_str:<20} {ts}")
            
            if len(keys) > 20:
                print(f"   ... et {len(keys) - 20} autres clés")
            
            # Exemples de documents complets
            print(f"\n   Exemples de documents (3 premiers):")
            for i, doc in enumerate(coll.find({'source': source}).limit(3), 1):
                print(f"\n   Document {i}:")
                print(f"      _id: {doc.get('_id')}")
                print(f"      source: {doc.get('source')}")
                print(f"      dataset: {doc.get('dataset', 'N/A')}")
                print(f"      key: {doc.get('key')}")
                print(f"      ts: {doc.get('ts')}")
                print(f"      value: {doc.get('value')}")
                
                if 'attrs' in doc and doc['attrs']:
                    print(f"      attrs:")
                    for k, v in list(doc['attrs'].items())[:10]:
                        print(f"         {k}: {v}")
                    if len(doc['attrs']) > 10:
                        print(f"         ... et {len(doc['attrs']) - 10} autres attributs")
    
    # Si raw_events
    elif coll_name == 'raw_events':
        sources = coll.distinct('source')
        
        for source in sources:
            source_docs = coll.count_documents({'source': source})
            print(f"\n📦 SOURCE: {source} ({source_docs:,} documents)")
            
            # Exemple
            doc = coll.find_one({'source': source})
            if doc:
                print(f"   Structure: {list(doc.keys())[:10]}")
    
    # Si ingestion_runs
    elif coll_name == 'ingestion_runs':
        sources = coll.distinct('source')
        
        for source in sources:
            runs = coll.count_documents({'source': source})
            print(f"\nSOURCE: {source} ({runs:,} executions)")
            
            # Dernière exécution
            last_run = coll.find_one({'source': source}, sort=[('start_time', -1)])
            if last_run:
                print(f"   Dernière exécution: {last_run.get('start_time')}")
                print(f"   Status: {last_run.get('status')}")
                print(f"   Observations: {last_run.get('obs_count', 0)}")

client.close()

print("\n" + "="*100)
print("Inspection terminee")
print("="*100)

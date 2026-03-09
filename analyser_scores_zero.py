#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSER LES PUBLICATIONS BRVM - Pourquoi scores à 0 ?
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ANALYSE PUBLICATIONS BRVM - Scores semantiques")
print("="*80)

coll = db['curated_observations']

# 1. Publications BRVM
print("\n[1] BRVM_PUBLICATION (249 docs)")
docs = list(coll.find({'source': 'BRVM_PUBLICATION'}).limit(10))
for i, doc in enumerate(docs, 1):
    print(f"\n  Doc {i}:")
    print(f"    dataset: {doc.get('dataset')}")
    print(f"    key: {doc.get('key')}")
    print(f"    ts: {doc.get('ts')}")
    print(f"    value: {doc.get('value')}")
    if 'attrs' in doc:
        attrs = doc['attrs']
        print(f"    attrs keys: {list(attrs.keys())}")
        for k, v in attrs.items():
            if isinstance(v, str) and len(v) > 80:
                print(f"      {k}: {v[:80]}...")
            else:
                print(f"      {k}: {v}")

# 2. RICHBOURSE
print("\n\n" + "="*80)
print("[2] RICHBOURSE (116 docs)")
docs = list(coll.find({'source': 'RICHBOURSE'}).limit(10))
for i, doc in enumerate(docs, 1):
    print(f"\n  Doc {i}:")
    print(f"    dataset: {doc.get('dataset')}")
    print(f"    key: {doc.get('key')}")
    print(f"    ts: {doc.get('ts')}")
    if 'attrs' in doc:
        attrs = doc['attrs']
        print(f"    attrs keys: {list(attrs.keys())}")
        for k in ['titre', 'title', 'text', 'contenu', 'content']:
            if k in attrs:
                v = attrs[k]
                if isinstance(v, str) and len(v) > 80:
                    print(f"      {k}: {v[:80]}...")
                else:
                    print(f"      {k}: {v}")

# 3. Dates des publications
print("\n\n" + "="*80)
print("[3] DATES DES PUBLICATIONS")
print("="*80)

for source_name in ['BRVM_PUBLICATION', 'RICHBOURSE', 'BRVM']:
    docs = coll.find({'source': source_name}).sort('ts', -1).limit(5)
    print(f"\n{source_name} - 5 plus recentes:")
    for i, doc in enumerate(docs, 1):
        print(f"  {i}. {doc.get('ts')} - {doc.get('dataset', 'N/A')}")

# 4. Chercher dans agregation_semantique_action
print("\n\n" + "="*80)
print("[4] AGREGATION_SEMANTIQUE_ACTION")
print("="*80)

coll2 = db['agregation_semantique_action']
count = coll2.count_documents({})
print(f"Total: {count} documents\n")

for doc in coll2.find().limit(5):
    print(f"\nAction: {doc.get('action', 'N/A')}")
    print(f"  publications_count: {doc.get('publications_count', 0)}")
    print(f"  score_ct: {doc.get('score_ct', 0)}")
    print(f"  score_mt: {doc.get('score_mt', 0)}")
    print(f"  score_lt: {doc.get('score_lt', 0)}")
    print(f"  risque_eleve: {doc.get('risque_eleve', 0)}")
    
    if 'publications' in doc:
        pubs = doc['publications']
        print(f"  publications: {type(pubs)} - {len(pubs) if isinstance(pubs, list) else 'N/A'}")
        if isinstance(pubs, list) and len(pubs) > 0:
            print(f"    Exemple pub 1: {list(pubs[0].keys() if isinstance(pubs[0], dict) else 'N/A')}")

print("\n" + "="*80)
print("FIN")
print("="*80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTIC FINAL - Pourquoi scores à 0 ?
"""

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("DIAGNOSTIC - SCORES SEMANTIQUES A 0")
print("="*80)

#  1. Compter publications par source
print("\n[1] PUBLICATIONS PAR SOURCE")
coll = db['curated_observations']

for source in ['RICHBOURSE', 'BRVM_PUBLICATION', 'BRVM']:
    total = coll.count_documents({'source': source})
    with_semantic = coll.count_documents({
        'source': source,
        'attrs.semantic_score_base': {'$exists': True}
    })
    with_tags = coll.count_documents({
        'source': source,
        'attrs.semantic_tags': {'$exists': True}
    })
    
    print(f"\n{source}:")
    print(f"  Total: {total}")
    print(f"  Avec semantic_score_base: {with_semantic}")
    print(f"  Avec semantic_tags: {with_tags}")

# 2. Regarder agregation_semantique_action
print("\n\n[2] AGREGATION_SEMANTIQUE_ACTION")
coll2 = db['agregation_semantique_action']

for doc in coll2.find():
    action = doc.get('action', 'N/A')
    count = doc.get('publications_count', 0)
    score_ct = doc.get('score_ct', 0)
    score_mt = doc.get('score_mt', 0)
    score_lt = doc.get('score_lt', 0)
    
    print(f"\n{action}:")
    print(f"  publications_count: {count}")
    print(f"  score_ct: {score_ct}")
    print(f"  score_mt: {score_mt}")
    print(f"  score_lt: {score_lt}")

# 3. Chercher publications avec semantic_tags
print("\n\n[3] PUBLICATIONS AVEC semantic_tags")
docs = list(coll.find({'attrs.semantic_tags': {'$exists': True}}).limit(5))

if len(docs) == 0:
    print("❌ AUCUNE publication avec semantic_tags!")
    print("\nCHERCHONS POURQUOI...")
    
    # Regarder un exemple de publication BRVM
    sample = coll.find_one({'source': 'BRVM_PUBLICATION'})
    if sample:
        print("\nExemple BRVM_PUBLICATION:")
        print(f"  _id: {sample.get('_id')}")
        print(f"  dataset: {sample.get('dataset')}")
        print(f"  ts: {sample.get('ts')}")
        print(f"  attrs keys: {list(sample.get('attrs', {}).keys())}")
        
        attrs = sample.get('attrs', {})
        if 'full_text' in attrs:
            print(f"  full_text: {attrs['full_text'][:100]}...")
        if 'description' in attrs:
            print(f"  description: {attrs['description'][:100]}...")
        if 'titre' in attrs:
            print(f"  titre: {attrs['titre']}")
    
    # Regarder Richbourse
    sample2 = coll.find_one({'source': 'RICHBOURSE'})
    if sample2:
        print("\nExemple RICHBOURSE:")
        print(f"  _id: {sample2.get('_id')}")
        print(f"  dataset: {sample2.get('dataset')}")
        print(f"  ts: {sample2.get('ts')}")
        attrs = sample2.get('attrs', {})
        print(f"  attrs keys: {list(attrs.keys())}")
        
        if 'full_text' in attrs:
            print(f"  full_text: {attrs['full_text'][:100]}...")
        if 'description' in attrs:
            print(f"  description: {attrs['description'][:100]}...")

else:
    print(f"✓ {len(docs)} publications trouvees avec semantic_tags")
    for doc in docs[:3]:
        attrs = doc.get('attrs', {})
        print(f"\n  Source: {doc.get('source')}")
        print(f"  Titre: {attrs.get('titre', 'N/A')}")
        print(f"  semantic_tags: {attrs.get('semantic_tags')}")
        print(f"  semantic_score_base: {attrs.get('semantic_score_base')}")

print("\n" + "="*80)
print("FIN DIAGNOSTIC")
print("="*80)

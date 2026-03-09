#!/usr/bin/env python3
"""Vérification données historiques MongoDB"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("="*80)
print("📊 VÉRIFICATION DONNÉES HISTORIQUES MONGODB")
print("="*80)

# Total observations BRVM
total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
print(f"\n📈 Total observations BRVM: {total_brvm}")

# Actions uniques
actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
print(f"🎯 Actions uniques: {len(actions)}")

if actions:
    print(f"\n📋 Première action: {actions[0]}")
    
    # Historique pour première action
    docs = list(db.curated_observations.find(
        {'source': 'BRVM', 'key': actions[0]}
    ).sort('ts', 1))
    
    print(f"\n📊 Historique {actions[0]}: {len(docs)} observations")
    
    if docs:
        print(f"\n📅 Période:")
        print(f"   Début: {docs[0]['ts']}")
        print(f"   Fin:   {docs[-1]['ts']}")
        
        print(f"\n📋 Exemple observation:")
        doc = docs[0]
        print(f"   source: {doc['source']}")
        print(f"   dataset: {doc.get('dataset', 'N/A')}")
        print(f"   key: {doc['key']}")
        print(f"   ts: {doc['ts']}")
        print(f"   value: {doc['value']}")
        print(f"   attrs: {list(doc.get('attrs', {}).keys())}")
        
        if 'attrs' in doc:
            print(f"\n🔍 Attributs disponibles:")
            for k, v in doc['attrs'].items():
                print(f"      {k}: {v}")

# Statistiques par action
print(f"\n📊 STATISTIQUES PAR ACTION:")
print(f"{'Action':<10} {'Observations':<15} {'Date début':<12} {'Date fin':<12}")
print("-" * 60)

for action in actions[:10]:
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'key': action
    })
    
    docs = list(db.curated_observations.find(
        {'source': 'BRVM', 'key': action}
    ).sort('ts', 1).limit(1))
    
    debut = docs[0]['ts'] if docs else 'N/A'
    
    docs_fin = list(db.curated_observations.find(
        {'source': 'BRVM', 'key': action}
    ).sort('ts', -1).limit(1))
    
    fin = docs_fin[0]['ts'] if docs_fin else 'N/A'
    
    print(f"{action:<10} {count:<15} {debut:<12} {fin:<12}")

# Vérifier data_quality
print(f"\n🔍 VÉRIFICATION data_quality:")
with_quality = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$exists': True}
})
print(f"   Avec data_quality: {with_quality}/{total_brvm}")

without_quality = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$exists': False}
})
print(f"   Sans data_quality: {without_quality}/{total_brvm}")

if with_quality > 0:
    qualities = db.curated_observations.distinct('attrs.data_quality', {'source': 'BRVM'})
    print(f"   Types: {qualities}")

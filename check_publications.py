#!/usr/bin/env python3
"""Vérification rapide publications BRVM"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("\n" + "="*80)
print(f"VERIFICATION PUBLICATIONS BRVM - {datetime.now().strftime('%H:%M:%S')}")
print("="*80)

# Total publications
total = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATION'
})

print(f"\nTotal publications: {total}")

# Par type
print(f"\nPar type de document:")
types = db.curated_observations.aggregate([
    {'$match': {'source': 'BRVM_PUBLICATION'}},
    {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
])

for t in types:
    print(f"  {t['_id']:25s}: {t['count']:4d}")

# Exemples récents
print(f"\nExemples (5 publications récentes):")
print(f"{'TYPE':<20} {'TITRE':<60}")
print("-" * 80)

pubs = db.curated_observations.find({
    'source': 'BRVM_PUBLICATION'
}).sort('attrs.collecte_datetime', -1).limit(5)

for pub in pubs:
    attrs = pub.get('attrs', {})
    titre = attrs.get('titre', 'N/A')[:57]
    type_doc = pub.get('dataset', 'N/A')[:17]
    print(f"{type_doc:<20} {titre:<60}")

print("="*80)
client.close()

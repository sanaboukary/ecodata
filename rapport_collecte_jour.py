#!/usr/bin/env python3
"""Rapport complet de la collecte du jour"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

today = datetime.now().strftime('%Y-%m-%d')

print("\n" + "="*80)
print(f"RAPPORT COLLECTE DU JOUR - {today}")
print("="*80)

print(f"\n1. BRVM ACTIONS (cours + attributs)")
brvm_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today
})
brvm_reel = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today,
    'attrs.data_quality': {'$in': ['REAL_SCRAPER', 'REAL_MANUAL']}
})
print(f"   Total      : {brvm_today}")
print(f"   REEL       : {brvm_reel}")
print(f"   Status     : {'OK' if brvm_reel > 0 else 'AUCUNE DONNEE'}")

print(f"\n2. BRVM PUBLICATIONS")
pubs_today = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATION',
    'ts': today
})
print(f"   Total      : {pubs_today}")
print(f"   Status     : {'OK' if pubs_today > 0 else 'AUCUNE DONNEE'}")

print(f"\n3. WORLDBANK")
wb_total = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"   Total      : {wb_total}")

print(f"\n4. IMF")
imf_total = db.curated_observations.count_documents({'source': 'IMF'})
print(f"   Total      : {imf_total}")

print(f"\n5. AfDB")
afdb_total = db.curated_observations.count_documents({'source': 'AfDB'})
print(f"   Total      : {afdb_total}")

print(f"\n6. UN SDG")
un_total = db.curated_observations.count_documents({'source': 'UN_SDG'})
print(f"   Total      : {un_total}")

# Total général
grand_total = db.curated_observations.count_documents({})

print("\n" + "="*80)
print(f"TOTAL GÉNÉRAL : {grand_total:,} observations")
print("="*80)

# Dernières collectes
print(f"\nDernières collectes (top 10):")
print(f"{'SOURCE':<15} {'DATASET':<20} {'DATE':<12} {'COUNT':>6}")
print("-" * 60)

pipeline = [
    {'$group': {
        '_id': {'source': '$source', 'dataset': '$dataset', 'date': '$ts'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'_id.date': -1}},
    {'$limit': 10}
]

for doc in db.curated_observations.aggregate(pipeline):
    source = doc['_id']['source'][:14]
    dataset = str(doc['_id']['dataset'])[:19]
    date = doc['_id']['date'][:11]
    count = doc['count']
    print(f"{source:<15} {dataset:<20} {date:<12} {count:>6}")

print("="*80)
client.close()

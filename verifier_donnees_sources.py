#!/usr/bin/env python3
"""
Vérification des données par source dans MongoDB
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

client, db = get_mongo_db()

print("=" * 80)
print("📊 VÉRIFICATION DONNÉES PAR SOURCE")
print("=" * 80)

# Compter observations par source
sources = db.curated_observations.distinct('source')

print(f"\n🔍 Sources disponibles: {len(sources)}")
print()

total_obs = 0

for source in sorted(sources):
    count = db.curated_observations.count_documents({'source': source})
    total_obs += count
    
    print(f"📌 {source:20s}: {count:>8,} observations")
    
    # Exemples de données récentes
    recent = list(db.curated_observations.find(
        {'source': source}
    ).sort('ts', -1).limit(3))
    
    if recent:
        print(f"   Dernière date: {recent[0].get('ts', 'N/A')}")
        
        # Afficher datasets distincts
        datasets = db.curated_observations.distinct('dataset', {'source': source})
        print(f"   Datasets: {len(datasets)}")
        
        # Afficher pays/clés distincts
        keys = db.curated_observations.distinct('key', {'source': source})
        print(f"   Entités: {len(keys)} (pays, actions, etc.)")
        
    print()

print("=" * 80)
print(f"✅ TOTAL: {total_obs:,} observations")
print("=" * 80)

# Vérifier données téléchargeables
print("\n📥 VÉRIFICATION TÉLÉCHARGEMENT:")
print()

for source in sorted(sources):
    # Test requête pour téléchargement
    sample = db.curated_observations.find_one({'source': source})
    
    if sample:
        has_value = 'value' in sample
        has_ts = 'ts' in sample
        has_key = 'key' in sample
        
        status = "✅" if (has_value and has_ts and has_key) else "❌"
        print(f"{status} {source:20s}: value={has_value}, ts={has_ts}, key={has_key}")
        
        if not (has_value and has_ts and has_key):
            print(f"   ⚠️ Données incomplètes - impossible à télécharger!")
            print(f"   Exemple: {sample}")
    else:
        print(f"❌ {source:20s}: Aucune donnée")

print()
print("=" * 80)

# Vérifier années disponibles par source
print("\n📅 ANNÉES DISPONIBLES PAR SOURCE:")
print()

for source in ['WorldBank', 'IMF', 'UN_SDG', 'AfDB']:
    if source in sources:
        # Extraire années depuis ts
        pipeline = [
            {'$match': {'source': source}},
            {'$project': {
                'year': {'$substr': ['$ts', 0, 4]}
            }},
            {'$group': {'_id': '$year'}},
            {'$sort': {'_id': 1}}
        ]
        
        years = [doc['_id'] for doc in db.curated_observations.aggregate(pipeline)]
        
        if years:
            print(f"{source:20s}: {years[0]} à {years[-1]} ({len(years)} années)")
        else:
            print(f"{source:20s}: Aucune année")

print()
print("=" * 80)

client.close()

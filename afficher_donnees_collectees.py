#!/usr/bin/env python3
"""
📊 AFFICHAGE DES DONNÉES COLLECTÉES
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("=" * 100)
print("📊 DONNÉES COLLECTÉES - VUE D'ENSEMBLE")
print("=" * 100)
print()

_, db = get_mongo_db()

# 1. PUBLICATIONS BRVM
print("📰 PUBLICATIONS BRVM")
print("-" * 100)
publications = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATION'
})
print(f"Total publications : {publications}")

if publications > 0:
    # Par catégorie
    pipeline = [
        {'$match': {'source': 'BRVM_PUBLICATION'}},
        {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    print("\nPar catégorie :")
    for item in db.curated_observations.aggregate(pipeline):
        print(f"  {item['_id']:25s} : {item['count']:3d} documents")
    
    # Dernière publication
    latest_pub = db.curated_observations.find_one(
        {'source': 'BRVM_PUBLICATION'},
        sort=[('ts', -1)]
    )
    if latest_pub:
        print(f"\nDernière publication :")
        print(f"  Date     : {latest_pub.get('ts', 'N/A')[:10]}")
        print(f"  Titre    : {latest_pub.get('attrs', {}).get('title', 'N/A')[:70]}")
        print(f"  Catégorie: {latest_pub.get('dataset', 'N/A')}")

print()
print("=" * 100)

# 2. COURS BRVM
print("📈 COURS DES ACTIONS BRVM")
print("-" * 100)
cours = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': {'$ne': 'PUBLICATION'}
})
print(f"Total observations de cours : {cours}")

if cours > 0:
    # Dernière date
    latest = db.curated_observations.find_one(
        {'source': 'BRVM', 'dataset': {'$ne': 'PUBLICATION'}},
        sort=[('ts', -1)]
    )
    if latest:
        latest_date = latest.get('ts', '')[:10]
        print(f"\nDernière date de cours : {latest_date}")
        
        # Actions pour cette date
        actions_jour = list(db.curated_observations.find(
            {
                'source': 'BRVM',
                'dataset': {'$ne': 'PUBLICATION'},
                'ts': {'$regex': f'^{latest_date}'}
            },
            {'key': 1, 'value': 1, 'attrs.volume': 1, 'attrs.variation': 1}
        ).sort('value', -1).limit(15))
        
        if actions_jour:
            print(f"\nTop 15 actions au {latest_date} :")
            print(f"  {'Symbole':<10} {'Cours (FCFA)':>15} {'Volume':>12} {'Variation':>12}")
            print(f"  {'-'*10} {'-'*15} {'-'*12} {'-'*12}")
            for action in actions_jour:
                symbole = action.get('key', 'N/A')
                cours = action.get('value', 0)
                volume = action.get('attrs', {}).get('volume', 0)
                variation = action.get('attrs', {}).get('variation', 0)
                
                # Indicateur variation
                if variation > 0:
                    var_icon = "🟢"
                elif variation < 0:
                    var_icon = "🔴"
                else:
                    var_icon = "⚪"
                
                print(f"  {symbole:<10} {cours:>15,.0f} {volume:>12,} {var_icon} {variation:>10.2f}%")
    
    # Statistiques par action
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': {'$ne': 'PUBLICATION'}}},
        {'$group': {'_id': '$key', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    print(f"\nTop 10 actions par nombre d'observations :")
    for item in db.curated_observations.aggregate(pipeline):
        print(f"  {item['_id']:10s} : {item['count']:4d} observations")

else:
    print("\n⚠️  Aucun cours d'action collecté")
    print("💡 Utiliser : mettre_a_jour_cours_brvm.py ou collecter_quotidien_intelligent.py")

print()
print("=" * 100)

# 3. AUTRES SOURCES
print("🌍 AUTRES SOURCES DE DONNÉES")
print("-" * 100)

sources = ['WorldBank', 'IMF', 'AfDB', 'UN_SDG']
for source in sources:
    count = db.curated_observations.count_documents({'source': source})
    if count > 0:
        latest = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', -1)]
        )
        latest_date = latest.get('ts', '')[:10] if latest else 'N/A'
        print(f"  {source:12s} : {count:6d} observations (dernière : {latest_date})")
    else:
        print(f"  {source:12s} : {count:6d} observations")

print()
print("=" * 100)

# 4. RÉSUMÉ GLOBAL
print("📊 RÉSUMÉ GLOBAL")
print("-" * 100)
total = db.curated_observations.count_documents({})
print(f"Total observations MongoDB : {total:,}")

# Par source
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
print("\nPar source :")
for item in db.curated_observations.aggregate(pipeline):
    pct = (item['count'] / total * 100) if total > 0 else 0
    print(f"  {item['_id']:20s} : {item['count']:6d} ({pct:5.1f}%)")

print()
print("=" * 100)
print("✅ Affichage terminé")
print("=" * 100)

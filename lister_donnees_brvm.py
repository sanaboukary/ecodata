#!/usr/bin/env python3
"""
Liste complète de toutes les données BRVM disponibles
"""
import os, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*100)
print(" " * 30 + "INVENTAIRE COMPLET DONNÉES BRVM")
print("="*100 + "\n")

# 1. Total global
total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"📊 TOTAL GLOBAL STOCK_PRICE : {total:,} observations\n")

# 2. Par source
print("="*100)
print("📁 DÉTAIL PAR SOURCE :")
print("="*100 + "\n")

sources = db.curated_observations.distinct('source', {'dataset': 'STOCK_PRICE'})

for source in sorted(sources):
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'source': source
    })
    
    print(f"┌─ {source}")
    print(f"│  Total observations : {count:,}")
    
    # Période
    pipeline_dates = [
        {'$match': {'dataset': 'STOCK_PRICE', 'source': source}},
        {'$group': {'_id': None, 'min_ts': {'$min': '$ts'}, 'max_ts': {'$max': '$ts'}}}
    ]
    dates = list(db.curated_observations.aggregate(pipeline_dates))
    if dates:
        print(f"│  Période : {dates[0]['min_ts']} → {dates[0]['max_ts']}")
    
    # Jours uniques
    jours = db.curated_observations.distinct('ts', {'dataset': 'STOCK_PRICE', 'source': source})
    print(f"│  Jours de collecte : {len(jours)}")
    
    # Actions uniques
    actions = db.curated_observations.distinct('key', {'dataset': 'STOCK_PRICE', 'source': source})
    # Filtrer les clés bizarres (avec timestamps)
    actions_clean = [a for a in actions if a and '_2025' not in a and '_2026' not in a and len(a) <= 10]
    print(f"│  Actions : {len(actions_clean)}")
    
    # Top 10 jours avec le plus d'observations
    pipeline_top_jours = [
        {'$match': {'dataset': 'STOCK_PRICE', 'source': source}},
        {'$group': {'_id': '$ts', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    top_jours = list(db.curated_observations.aggregate(pipeline_top_jours))
    
    if top_jours:
        print(f"│  Top 5 jours (plus de données) :")
        for j in top_jours:
            print(f"│    • {j['_id']} : {j['count']} obs")
    
    print(f"└─\n")

# 3. Répartition par mois
print("="*100)
print("📅 RÉPARTITION PAR MOIS :")
print("="*100 + "\n")

pipeline_mois = [
    {'$match': {'dataset': 'STOCK_PRICE'}},
    {'$project': {
        'mois': {'$substr': ['$ts', 0, 7]},  # YYYY-MM
        'source': 1
    }},
    {'$group': {
        '_id': {'mois': '$mois', 'source': '$source'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'_id.mois': 1, '_id.source': 1}}
]

mois_data = list(db.curated_observations.aggregate(pipeline_mois))

# Organiser par mois
mois_dict = defaultdict(lambda: defaultdict(int))
for item in mois_data:
    mois = item['_id']['mois']
    source = item['_id']['source']
    count = item['count']
    mois_dict[mois][source] = count

for mois in sorted(mois_dict.keys()):
    total_mois = sum(mois_dict[mois].values())
    print(f"📆 {mois} : {total_mois:,} observations")
    for source, count in sorted(mois_dict[mois].items()):
        print(f"   └─ {source:<30} : {count:>6,} obs")
    print()

# 4. Actions BRVM disponibles
print("="*100)
print("🏢 ACTIONS BRVM COLLECTÉES :")
print("="*100 + "\n")

# Trouver toutes les actions uniques
all_actions = set()
for source in sources:
    actions = db.curated_observations.distinct('key', {'dataset': 'STOCK_PRICE', 'source': source})
    actions_clean = [a for a in actions if a and '_2025' not in a and '_2026' not in a and len(a) <= 10]
    all_actions.update(actions_clean)

actions_list = sorted(all_actions)

print(f"Total actions uniques : {len(actions_list)}\n")

# Pour chaque action, compter les observations
print(f"{'ACTION':<10} {'TOTAL OBS':>12} {'SOURCES':>8} {'PREMIÈRE DATE':<15} {'DERNIÈRE DATE':<15}")
print("-"*70)

for action in actions_list:
    count_action = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'key': action
    })
    
    sources_action = db.curated_observations.distinct('source', {
        'dataset': 'STOCK_PRICE',
        'key': action
    })
    
    # Dates
    pipeline_dates_action = [
        {'$match': {'dataset': 'STOCK_PRICE', 'key': action}},
        {'$group': {'_id': None, 'min_ts': {'$min': '$ts'}, 'max_ts': {'$max': '$ts'}}}
    ]
    dates_action = list(db.curated_observations.aggregate(pipeline_dates_action))
    
    min_date = dates_action[0]['min_ts'] if dates_action else 'N/A'
    max_date = dates_action[0]['max_ts'] if dates_action else 'N/A'
    
    print(f"{action:<10} {count_action:>12,} {len(sources_action):>8} {str(min_date)[:15]:<15} {str(max_date)[:15]:<15}")

# 5. Période manquante
print("\n" + "="*100)
print("⚠️  PÉRIODES MANQUANTES :")
print("="*100 + "\n")

print("❌ 2025-12-13 → 2026-01-06 (~25 jours)")
print("   └─ Données supprimées par nettoyer_outliers_trading.py")
print("   └─ Aucun fichier CSV de sauvegarde disponible")
print()

print("⚠️  2026-01-07 → 2026-02-09")
print("   └─ Seulement 5 jours collectés au lieu de 34")
print("   └─ Collections multiples/jour perdues (problème ts=date)")
print()

# 6. Qualité des données
print("="*100)
print("✅ QUALITÉ DES DONNÉES :")
print("="*100 + "\n")

# Vérifier les champs essentiels
essential_fields = ['symbole', 'cours', 'volume', 'variation_pct']
quality_report = {}

for field in essential_fields:
    with_field = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        f'attrs.{field}': {'$exists': True, '$ne': None}
    })
    quality_report[field] = (with_field / total * 100) if total > 0 else 0

print("Complétude des champs (%):")
for field, percentage in quality_report.items():
    bar_length = int(percentage / 2)
    bar = '█' * bar_length + '░' * (50 - bar_length)
    print(f"  {field:<20} : {bar} {percentage:>6.2f}%")

# 7. Résumé final
print("\n" + "="*100)
print("📋 RÉSUMÉ FINAL :")
print("="*100 + "\n")

print(f"✅ Données disponibles      : {total:,} observations")
print(f"✅ Actions couvertes        : {len(actions_list)} titres BRVM")
print(f"✅ Sources de données       : {len(sources)}")
print(f"✅ Période globale          : 2025-09-15 → 2026-02-10")
print(f"✅ Jours de collecte        : ~68 jours (avec trous)")
print(f"❌ Jours manquants          : ~29 jours")
print(f"📊 Taux de couverture       : {((68-29)/68*100):.1f}% de la période")

print("\n" + "="*100 + "\n")

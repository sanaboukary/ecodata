#!/usr/bin/env python3
"""
Rapport complet et détaillé de toutes les sources de données
"""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("=" * 120)
print(" " * 35 + "PLATEFORME DE CENTRALISATION DE DONNÉES")
print(" " * 45 + "RAPPORT COMPLET")
print("=" * 120)

# Statistiques globales
total_obs = db.curated_observations.count_documents({})
total_events = db.raw_events.count_documents({})
total_runs = db.ingestion_runs.count_documents({})

print(f"\n📊 STATISTIQUES GLOBALES")
print(f"{'─' * 120}")
print(f"  Total observations normalisées : {total_obs:>10,}")
print(f"  Total événements bruts         : {total_events:>10,}")
print(f"  Total exécutions d'ingestion   : {total_runs:>10,}")

# Par source
sources = db.curated_observations.distinct('source')
print(f"\n📈 DONNÉES PAR SOURCE")
print(f"{'─' * 120}")
print(f"{'Source':<20} {'Observations':>15} {'Datasets':>15} {'Clés uniques':>15} {'Période':<30}")
print(f"{'─' * 120}")

for source in sorted(sources):
    count = db.curated_observations.count_documents({'source': source})
    datasets = db.curated_observations.distinct('dataset', {'source': source})
    datasets_count = len([d for d in datasets if d is not None])
    keys = db.curated_observations.distinct('key', {'source': source})
    keys_count = len([k for k in keys if k is not None])
    
    # Période
    pipeline = [
        {'$match': {'source': source, 'ts': {'$ne': None}}},
        {'$group': {
            '_id': None,
            'min_date': {'$min': '$ts'},
            'max_date': {'$max': '$ts'}
        }}
    ]
    
    result = list(db.curated_observations.aggregate(pipeline))
    if result and result[0].get('min_date'):
        min_d = str(result[0]['min_date'])[:10]
        max_d = str(result[0]['max_date'])[:10]
        period = f"{min_d} → {max_d}"
    else:
        period = "N/A"
    
    print(f"{source:<20} {count:>15,} {datasets_count:>15} {keys_count:>15} {period:<30}")

# Détails BRVM
print(f"\n{'=' * 120}")
print("🏦 DÉTAILS BRVM - BOURSE RÉGIONALE DES VALEURS MOBILIÈRES")
print(f"{'=' * 120}")

brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
brvm_symbols = db.curated_observations.distinct('key', {'source': 'BRVM'})

print(f"\n  Total observations : {brvm_count:,}")
print(f"  Actions cotées     : {len(brvm_symbols)}")

# Par secteur
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$group': {
        '_id': '$attrs.sector',
        'actions': {'$addToSet': '$key'},
        'observations': {'$sum': 1}
    }},
    {'$sort': {'observations': -1}}
]

print(f"\n  Répartition par secteur:")
print(f"  {'Secteur':<25} {'Actions':>10} {'Observations':>15}")
print(f"  {'─' * 60}")

for doc in db.curated_observations.aggregate(pipeline):
    sector = doc['_id'] or 'Non spécifié'
    actions = len(doc['actions'])
    obs = doc['observations']
    print(f"  {sector:<25} {actions:>10} {obs:>15,}")

# Par pays
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$group': {
        '_id': '$attrs.country',
        'actions': {'$addToSet': '$key'},
        'observations': {'$sum': 1}
    }},
    {'$sort': {'observations': -1}}
]

country_names = {
    'CI': 'Côte d\'Ivoire', 'SN': 'Sénégal', 'BF': 'Burkina Faso',
    'BJ': 'Bénin', 'TG': 'Togo', 'ML': 'Mali', 'NE': 'Niger', 'SL': 'Sierra Leone'
}

print(f"\n  Répartition par pays:")
print(f"  {'Pays':<25} {'Actions':>10} {'Observations':>15}")
print(f"  {'─' * 60}")

for doc in db.curated_observations.aggregate(pipeline):
    country_code = doc['_id'] or 'N/A'
    country = country_names.get(country_code, country_code)
    actions = len(doc['actions'])
    obs = doc['observations']
    print(f"  {country:<25} {actions:>10} {obs:>15,}")

# Résumé final
print(f"\n{'=' * 120}")
print("✅ RÉSUMÉ")
print(f"{'=' * 120}")
print(f"\n  Sources actives : {len(sources)}")
print(f"  Total données   : {total_obs:,} observations")
print(f"\n  Sources disponibles:")
for source in sorted(sources):
    count = db.curated_observations.count_documents({'source': source})
    print(f"    ✓ {source:<15} : {count:>8,} observations")

print(f"\n{'=' * 120}")

client.close()

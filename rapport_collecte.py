#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapport rapide post-collecte
"""

import subprocess
import sys

python_path = sys.executable

print("\n" + "=" * 80)
print("📊 RAPPORT POST-COLLECTE")
print("=" * 80)

# Utiliser un script simple pour afficher les données
script_code = """
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

client, db = get_mongo_db()
date_aujourdhui = datetime.now().strftime('%Y-%m-%d')

# Stats du jour
obs_aujourdhui = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': date_aujourdhui
})

obs_reelles_aujourdhui = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': date_aujourdhui,
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

# Stats totales
obs_total = db.curated_observations.count_documents({'source': 'BRVM'})

obs_reelles_total = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

actions = len(db.curated_observations.distinct('key', {'source': 'BRVM'}))

# Plage de dates
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$group': {
        '_id': None,
        'min_date': {'$min': '$ts'},
        'max_date': {'$max': '$ts'}
    }}
]
dates = list(db.curated_observations.aggregate(pipeline))

print(f"\\n📅 DONNÉES DU JOUR ({date_aujourdhui})")
print("─" * 80)
print(f"  Observations totales : {obs_aujourdhui}")
print(f"  Observations réelles : {obs_reelles_aujourdhui}")
print(f"  Qualité des données  : {obs_reelles_aujourdhui/max(obs_aujourdhui,1)*100:.1f}%")

print(f"\\n📊 DONNÉES BRVM TOTALES")
print("─" * 80)
print(f"  Observations totales : {obs_total:,}")
print(f"  Observations réelles : {obs_reelles_total:,} ({obs_reelles_total/max(obs_total,1)*100:.1f}%)")
print(f"  Actions distinctes   : {actions}")

if dates and dates[0]['min_date']:
    print(f"  Période de données   : {dates[0]['min_date']} → {dates[0]['max_date']}")

# Échantillon du jour
print(f"\\n📈 ÉCHANTILLON (Observations du jour)")
print("─" * 80)

echantillon = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': date_aujourdhui
}).limit(5))

for obs in echantillon:
    symbol = obs.get('key', 'N/A')
    price = obs.get('value', 0)
    quality = obs.get('attrs', {}).get('data_quality', 'UNKNOWN')
    print(f"  {symbol:12} : {price:>10.2f} FCFA  [{quality}]")

print("\\n" + "=" * 80)
"""

try:
    result = subprocess.run(
        [python_path, "-c", script_code],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(result.stdout)
    
    if result.stderr and "warning" not in result.stderr.lower():
        print("Avertissements/Erreurs :")
        print(result.stderr)
        
except Exception as e:
    print(f"❌ Erreur : {e}")

print()

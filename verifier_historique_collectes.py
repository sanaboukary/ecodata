#!/usr/bin/env python3
"""
Vérification de l'historique complet des collectes BRVM
"""
import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("VÉRIFICATION HISTORIQUE COLLECTES BRVM")
print("="*80)

# 1. Collectes par jour
pipeline = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$ts', 'count': {'$sum': 1}}},
    {'$sort': {'_id': 1}}
]
jours = list(db.curated_observations.aggregate(pipeline))

print(f"\n[1] RÉPARTITION PAR JOUR:")
print(f"    Jours uniques de collecte : {len(jours)}")
if jours:
    print(f"    Première collecte       : {jours[0]['_id']}")
    print(f"    Dernière collecte       : {jours[-1]['_id']}")
    print(f"    Total observations      : {sum(j['count'] for j in jours)}")
    print(f"    Moyenne par jour        : {sum(j['count'] for j in jours)/len(jours):.1f}")

# 2. Afficher les 10 premiers et 10 derniers jours
print(f"\n[2] PREMIERS JOURS DE COLLECTE:")
for j in jours[:10]:
    print(f"    {j['_id']:<15} : {j['count']:>3} observations")

if len(jours) > 20:
    print(f"\n    ... ({len(jours)-20} jours intermédiaires) ...")

print(f"\n[3] DERNIERS JOURS DE COLLECTE:")
for j in jours[-10:]:
    print(f"    {j['_id']:<15} : {j['count']:>3} observations")

# 3. Vérifier les collectes multiples par jour
print(f"\n[4] VÉRIFICATION COLLECTES HORAIRES:")
# Chercher dans tous les champs possibles pour timestamp
sample = db.curated_observations.find_one({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
if sample:
    print(f"    Structure d'une observation:")
    print(f"      - ts (date)      : {sample.get('ts')}")
    print(f"      - timestamp      : {sample.get('timestamp')}")
    print(f"      - attrs.ts       : {sample.get('attrs', {}).get('ts')}")
    
    # Compter combien d'observations ont un timestamp précis
    with_timestamp = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'timestamp': {'$exists': True}
    })
    print(f"\n    Observations avec timestamp : {with_timestamp}")
    
    # Vérifier sur une journée spécifique (aujourd'hui)
    today = datetime.now().strftime("%Y-%m-%d")
    today_obs = list(db.curated_observations.find({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': today
    }).limit(5))
    
    if today_obs:
        print(f"\n    Exemple collectes du {today}:")
        for obs in today_obs:
            ts = obs.get('timestamp', obs.get('ts'))
            symbole = obs.get('key', obs.get('attrs', {}).get('symbole'))
            print(f"      {symbole:<8} : {ts}")

# 5. Actions collectées
actions = db.curated_observations.distinct('key', {
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})
print(f"\n[5] ACTIONS COLLECTÉES:")
print(f"    Total actions : {len(actions)}")
print(f"    Liste : {', '.join(sorted(actions)[:20])}")
if len(actions) > 20:
    print(f"            ... et {len(actions)-20} autres")

print("\n" + "="*80)
print("FIN VÉRIFICATION")
print("="*80 + "\n")

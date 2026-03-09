#!/usr/bin/env python3
"""
Affichage détaillé des données BRVM collectées
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

print("\n" + "="*100)
print(" " * 35 + "DONNÉES BRVM COLLECTÉES")
print("="*100)

# 1. Statistiques globales
total = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
print(f"\n📊 STATISTIQUES GLOBALES:")
print(f"    Total observations BRVM : {total}")

# 2. Actions collectées
actions_list = db.curated_observations.distinct('key', {'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
actions_brvm = [a for a in actions_list if '_' not in a and len(a) <= 10]
print(f"    Actions BRVM           : {len(actions_brvm)}")

# 3. Période de collecte
pipeline_date = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': None, 'min_ts': {'$min': '$ts'}, 'max_ts': {'$max': '$ts'}}}
]
periode = list(db.curated_observations.aggregate(pipeline_date))
if periode:
    print(f"    Période               : {periode[0]['min_ts']} → {periode[0]['max_ts']}")

# 4. Collectes par jour
pipeline_jours = [
    {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$ts', 'count': {'$sum': 1}}},
    {'$sort': {'_id': 1}}
]
jours = list(db.curated_observations.aggregate(pipeline_jours))
print(f"    Jours de collecte     : {len(jours)}")

# 5. Afficher toutes les données par action (dernière collecte)
print(f"\n" + "="*100)
print(f"{'SYM':<8} {'NOM':<30} {'COURS':>10} {'VAR%':>8} {'VOL':>8} {'Ouv':>10} {'Haut':>10} {'Bas':>10} {'Préc':>10}")
print("-"*100)

for action in sorted(actions_brvm):
    obs = db.curated_observations.find_one(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'key': action},
        sort=[('timestamp', -1)]
    )
    
    if obs:
        attrs = obs.get('attrs', {})
        symbole = attrs.get('symbole', action)
        nom = attrs.get('nom', 'N/A')[:30]
        cours = attrs.get('cours', obs.get('value', 0))
        variation = attrs.get('variation_pct', 0)
        volume = attrs.get('volume', 0)
        ouverture = attrs.get('ouverture', 0)
        haut = attrs.get('haut', 0)
        bas = attrs.get('bas', 0)
        precedent = attrs.get('precedent', 0)
        
        print(f"{symbole:<8} {nom:<30} {cours:>10,.2f} {variation:>7.2f}% {volume:>8,} "
              f"{ouverture:>10,.2f} {haut:>10,.2f} {bas:>10,.2f} {precedent:>10,.2f}")

# 6. Historique par jour
print(f"\n" + "="*100)
print(f"📅 HISTORIQUE COLLECTES PAR JOUR:")
print("-"*100)

for jour in jours:
    date = jour['_id']
    count = jour['count']
    
    # Prendre quelques exemples de cette journée
    exemples = list(db.curated_observations.find(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'ts': date}
    ).limit(3))
    
    symboles = [e.get('key', e.get('attrs', {}).get('symbole', 'N/A')) for e in exemples]
    symboles_str = ', '.join(symboles[:3])
    if count > 3:
        symboles_str += f" ... (+{count-3} autres)"
    
    # Vérifier si timestamp existe
    has_timestamp = any(e.get('timestamp') for e in exemples)
    ts_info = " ⏱️ (avec timestamp)" if has_timestamp else ""
    
    print(f"  {date:<25} : {count:>3} observations{ts_info}")
    print(f"    Actions: {symboles_str}")

# 7. Dernière collecte détaillée
print(f"\n" + "="*100)
print(f"🕐 DERNIÈRE COLLECTE COMPLÈTE:")
print("-"*100)

derniere_ts = db.curated_observations.find_one(
    {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
    sort=[('timestamp', -1)]
)

if derniere_ts:
    dernier_timestamp = derniere_ts.get('timestamp', derniere_ts.get('ts'))
    print(f"  Date/Heure : {dernier_timestamp}")
    
    # Toutes les observations de cette collecte
    dernieres = list(db.curated_observations.find(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'timestamp': dernier_timestamp}
    ))
    
    if not dernieres:
        dernier_date = str(dernier_timestamp).split(' ')[0] if ' ' in str(dernier_timestamp) else dernier_timestamp
        dernieres = list(db.curated_observations.find(
            {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'ts': dernier_date}
        ))
    
    print(f"  Actions collectées : {len(dernieres)}")
    print(f"\n  Détails:")
    print(f"  {'SYM':<8} {'COURS':>10} {'VAR%':>8} {'VOLUME':>12} {'TRANSACTIONS':>12}")
    print(f"  {'-'*55}")
    
    for obs in sorted(dernieres, key=lambda x: x.get('key', '')):
        attrs = obs.get('attrs', {})
        symbole = obs.get('key', attrs.get('symbole', 'N/A'))
        cours = attrs.get('cours', obs.get('value', 0))
        var = attrs.get('variation_pct', 0)
        vol = attrs.get('volume', 0)
        nb_trans = attrs.get('nb_transactions', 0)
        
        print(f"  {symbole:<8} {cours:>10,.2f} {var:>7.2f}% {vol:>12,} {nb_trans:>12,}")

print("\n" + "="*100)
print(" " * 40 + "FIN RAPPORT")
print("="*100 + "\n")

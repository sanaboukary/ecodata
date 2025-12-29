"""
Diagnostic approfondi des données BRVM pour analyse IA
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

_, db = get_mongo_db()

print('=' * 80)
print('🔍 DIAGNOSTIC COMPLET DES DONNÉES BRVM')
print('=' * 80)

# 1. Vérifier toutes les données BRVM
total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
print(f'\n📊 Total observations BRVM: {total_brvm}')

# 2. Distribution par date
threshold_60d = datetime.now() - timedelta(days=60)
threshold_30d = datetime.now() - timedelta(days=30)
threshold_7d = datetime.now() - timedelta(days=7)

count_60d = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': threshold_60d.strftime('%Y-%m-%d')}
})
count_30d = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': threshold_30d.strftime('%Y-%m-%d')}
})
count_7d = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': threshold_7d.strftime('%Y-%m-%d')}
})

print(f'\n📅 Distribution temporelle:')
print(f'   Derniers 60 jours: {count_60d} observations')
print(f'   Derniers 30 jours: {count_30d} observations')
print(f'   Derniers 7 jours:  {count_7d} observations')

# 3. Analyser un échantillon
sample_obs = list(db.curated_observations.find({'source': 'BRVM'}).limit(5))

if sample_obs:
    print(f'\n🔍 ÉCHANTILLON D\'OBSERVATIONS:')
    print('-' * 80)
    for i, obs in enumerate(sample_obs, 1):
        print(f'\n{i}. Action: {obs.get("key")}')
        print(f'   Date: {obs.get("ts")} (type: {type(obs.get("ts")).__name__})')
        print(f'   Value: {obs.get("value")}')
        attrs = obs.get('attrs', {})
        print(f'   Attrs: {len(attrs)} champs')
        if attrs:
            print(f'   Champs attrs: {list(attrs.keys())[:10]}...')

# 4. Distribution par action (60 jours)
print(f'\n📊 DISTRIBUTION PAR ACTION (60 derniers jours):')
print('-' * 80)

pipeline = [
    {
        '$match': {
            'source': 'BRVM',
            'ts': {'$gte': threshold_60d.strftime('%Y-%m-%d')}
        }
    },
    {
        '$group': {
            '_id': '$key',
            'count': {'$sum': 1},
            'latest_date': {'$max': '$ts'},
            'earliest_date': {'$min': '$ts'}
        }
    },
    {
        '$sort': {'count': -1}
    }
]

results = list(db.curated_observations.aggregate(pipeline))

if results:
    print(f'\nActions avec données: {len(results)}')
    print(f'\nTOP 10:')
    for i, r in enumerate(results[:10], 1):
        print(f'  {i:2d}. {r["_id"]:10s}: {r["count"]:4d} obs  ({r["earliest_date"]} → {r["latest_date"]})')
    
    # Stats
    counts = [r['count'] for r in results]
    print(f'\n📊 Statistiques:')
    print(f'   Moyenne: {sum(counts)/len(counts):.1f} obs/action')
    print(f'   Min: {min(counts)} obs')
    print(f'   Max: {max(counts)} obs')
else:
    print('❌ AUCUNE ACTION TROUVÉE!')

# 5. Vérifier le format de ts
print(f'\n🔍 VÉRIFICATION FORMAT DES DATES:')
print('-' * 80)

# Différents formats possibles
formats_test = [
    {'ts': {'$type': 'string'}},
    {'ts': {'$type': 'date'}},
    {'ts': {'$exists': True}}
]

for fmt in formats_test:
    query = {'source': 'BRVM', **fmt}
    count = db.curated_observations.count_documents(query)
    print(f'   {fmt}: {count} observations')

# 6. Tester la requête du moteur d'analyse
print(f'\n🔍 TEST REQUÊTE MOTEUR D\'ANALYSE:')
print('-' * 80)

# Récupérer les actions distinctes
actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
print(f'Actions distinctes: {len(actions)}')
print(f'Exemples: {actions[:10]}')

# Tester pour une action spécifique
if actions:
    test_action = actions[0]
    print(f'\n🧪 Test pour action: {test_action}')
    
    # Requête identique au moteur
    observations = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': test_action,
        'ts': {'$gte': threshold_60d.strftime('%Y-%m-%d')}
    }).sort('ts', 1))
    
    print(f'   Observations trouvées: {len(observations)}')
    
    if observations:
        print(f'   Première date: {observations[0].get("ts")}')
        print(f'   Dernière date: {observations[-1].get("ts")}')
        print(f'   Première valeur: {observations[0].get("value")}')
        
        # Vérifier si on peut calculer des indicateurs
        prices = [obs.get('value') for obs in observations if obs.get('value')]
        print(f'   Prix disponibles: {len(prices)}')
        
        if len(prices) >= 14:
            print(f'   ✅ Suffisant pour RSI (>= 14 jours)')
        else:
            print(f'   ❌ Insuffisant pour RSI (< 14 jours)')
    else:
        print(f'   ❌ Aucune observation trouvée avec la requête temporelle!')
        
        # Tester sans filtre temporel
        obs_no_filter = db.curated_observations.count_documents({
            'source': 'BRVM',
            'key': test_action
        })
        print(f'   Sans filtre temps: {obs_no_filter} observations')

print('\n' + '=' * 80)
print('✅ DIAGNOSTIC TERMINÉ')
print('=' * 80)

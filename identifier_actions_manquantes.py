#!/usr/bin/env python3
"""
Identifier les actions BRVM manquantes
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

# Liste officielle des 47 actions BRVM
ACTIONS_BRVM_47 = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS',
    'CBIBF', 'CFAC', 'CIEC', 'FTSC', 'NTLC', 'NSBC', 'ONTBF', 'ORGT', 'PALC',
    'PRSC', 'SAFC', 'SGBC', 'SHEC', 'SIBC', 'SICB', 'SICC', 'SDCC', 'SLBC',
    'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'TTLC', 'TTLS', 'UNXC', 'ETIT',
    'CABC', 'SEMC', 'SDSC', 'TTRC', 'NEIC', 'SVOC', 'EKAC', 'SAFCA', 'UNLC',
    'SIVC', 'BICB'
]

def identifier_manquantes():
    _, db = get_mongo_db()
    
    # Actions en base
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': '$key'}}
    ]
    
    actions_en_base = sorted([doc['_id'] for doc in db.curated_observations.aggregate(pipeline)])
    actions_officielles = sorted(set(ACTIONS_BRVM_47))
    
    print("="*100)
    print("COMPARAISON ACTIONS BRVM")
    print("="*100)
    
    print(f"\nActions en base: {len(actions_en_base)}")
    print(f"Actions officielles: {len(actions_officielles)}")
    
    # Actions manquantes
    manquantes = set(actions_officielles) - set(actions_en_base)
    print(f"\n!  {len(manquantes)} actions MANQUANTES:")
    for action in sorted(manquantes):
        print(f"   - {action}")
    
    # Actions en trop
    en_trop = set(actions_en_base) - set(actions_officielles)
    if en_trop:
        print(f"\n!  {len(en_trop)} actions EN TROP:")
        for action in sorted(en_trop):
            count = db.curated_observations.count_documents({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action
            })
            print(f"   - {action}: {count} observations")
    
    print("\n" + "="*100)
    print("LISTE DES ACTIONS EN BASE:")
    print("="*100)
    for action in actions_en_base:
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': action
        })
        print(f"   {action:<8} : {count:4} observations")
    
    print("="*100)

if __name__ == '__main__':
    identifier_manquantes()

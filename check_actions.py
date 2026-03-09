#!/usr/bin/env python3
"""
Script simple pour lister actions BRVM
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

_, db = get_mongo_db()

# Actions distinctes
actions = db.curated_observations.distinct('key', {'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
actions_sorted = sorted(actions)

print(f"\n{'='*80}")
print(f"ACTIONS BRVM EN BASE: {len(actions_sorted)}")
print(f"{'='*80}\n")

for i, sym in enumerate(actions_sorted, 1):
    print(f"{i:3}. {sym}")

print(f"\n{'='*80}")
print(f"TOTAL: {len(actions_sorted)} actions")
print(f"{'='*80}\n")

# Vérifier les doublons dans la liste du code
ACTIONS_LISTE = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOABK',
    'CBIBF', 'CFAC', 'CIEC', 'FTSC', 'NTLC', 'NSBC', 'ONTBF', 'ORGT', 'PALC',
    'PRSC', 'SAFC', 'SGBC', 'SHEC', 'SIBC', 'SICB', 'SICC', 'SDCC', 'SLBC',
    'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'TTLC', 'TTLS', 'UNXC', 'ETIT',
    'CABC', 'SEMC', 'SDSC', 'TTRC', 'NEIC', 'SVOC', 'EKAC', 'SAFCA', 'CIEC',
    'SAFCA', 'BICC'
]

print(f"LISTE DANS LE CODE: {len(ACTIONS_LISTE)} éléments")
print(f"Actions uniques: {len(set(ACTIONS_LISTE))}")

doublons = [x for x in set(ACTIONS_LISTE) if ACTIONS_LISTE.count(x) > 1]
if doublons:
    print(f"\nDOUBLONS: {doublons}")
    for d in doublons:
        indices = [i for i, x in enumerate(ACTIONS_LISTE) if x == d]
        print(f"  {d}: positions {indices}")

#!/usr/bin/env python3
"""
Lister toutes les actions BRVM en base
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

def lister_actions():
    _, db = get_mongo_db()
    
    # Récupérer toutes les actions distinctes
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': '$key'}},
        {'$sort': {'_id': 1}}
    ]
    
    actions = list(db.curated_observations.aggregate(pipeline))
    symboles = [a['_id'] for a in actions]
    
    print("="*80)
    print(f"ACTIONS BRVM EN BASE: {len(symboles)}")
    print("="*80)
    
    for i, sym in enumerate(symboles, 1):
        print(f"{i:3}. {sym}")
    
    print("="*80)
    print(f"TOTAL: {len(symboles)} actions")
    print("="*80)
    
    # Vérifier doublons dans la liste du collecteur
    from collecter_brvm_complet_maintenant import ACTIONS_BRVM_47
    
    print("\nVERIFICATION LISTE COLLECTEUR:")
    print("-"*80)
    print(f"Taille liste: {len(ACTIONS_BRVM_47)}")
    print(f"Actions uniques: {len(set(ACTIONS_BRVM_47))}")
    
    # Chercher doublons
    doublons = [x for x in set(ACTIONS_BRVM_47) if ACTIONS_BRVM_47.count(x) > 1]
    if doublons:
        print(f"\nDOUBLONS TROUVES: {doublons}")
        for d in doublons:
            print(f"  {d}: apparait {ACTIONS_BRVM_47.count(d)} fois")
    
    # Actions en base mais pas dans la liste
    en_base_pas_liste = set(symboles) - set(ACTIONS_BRVM_47)
    if en_base_pas_liste:
        print(f"\nEN BASE MAIS PAS DANS LISTE: {en_base_pas_liste}")
    
    # Actions dans liste mais pas en base
    en_liste_pas_base = set(ACTIONS_BRVM_47) - set(symboles)
    if en_liste_pas_base:
        print(f"\nEN LISTE MAIS PAS EN BASE: {en_liste_pas_base}")

if __name__ == '__main__':
    lister_actions()

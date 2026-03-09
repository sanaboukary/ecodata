#!/usr/bin/env python3
"""
Nettoyage des données BRVM collectées avec le mauvais ordre de colonnes
Supprime les observations avec des prix suspects (< 500 FCFA pour la plupart des actions)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Actions avec des prix normalement élevés (> 1000 FCFA)
ACTIONS_PRIX_ELEVES = [
    'BICC', 'ECOC', 'CBIBF', 'UNLC', 'NTLC', 'SGBC', 'SICC', 'SNTS', 
    'TTLS', 'SEMC', 'CFAC', 'SDSC', 'STBC', 'ETIT', 'LNBB'
]

def analyser_donnees_suspectes():
    """Analyser les données avec des prix suspects"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("ANALYSE DES DONNEES BRVM SUSPECTES")
    print("="*80)
    
    # Chercher toutes les données BRVM
    total = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    })
    
    print(f"\nTotal observations BRVM: {total}")
    
    # Prix suspects (< 500 pour actions à prix élevés)
    suspectes = []
    
    for action in ACTIONS_PRIX_ELEVES:
        docs = list(db.curated_observations.find({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': action,
            'value': {'$lt': 500}  # Prix < 500 FCFA = suspect
        }).sort('ts', -1))
        
        if docs:
            suspectes.extend(docs)
            print(f"\n!  {action}: {len(docs)} observations avec prix < 500 FCFA")
            for doc in docs[:3]:  # Afficher 3 exemples
                print(f"   - {doc['ts']}: {doc['value']} FCFA")
    
    # Prix suspects généraux (< 50 FCFA = probablement des volumes)
    tres_bas = list(db.curated_observations.find({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'value': {'$lt': 50}
    }).sort('ts', -1))
    
    print(f"\n!  {len(tres_bas)} observations avec prix < 50 FCFA (probablement des volumes)")
    
    total_suspectes = len(set(str(doc['_id']) for doc in suspectes + tres_bas))
    
    print("\n" + "="*80)
    print(f"TOTAL DONNEES SUSPECTES: {total_suspectes}")
    print("="*80)
    
    return suspectes + tres_bas


def nettoyer_donnees_suspectes(dry_run=True):
    """Supprimer les données suspectes"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("NETTOYAGE DES DONNÉES SUSPECTES")
    print("="*80)
    
    if dry_run:
        print("\n!  MODE DRY-RUN - Aucune suppression reelle")
    else:
        print("\n MODE REEL - Suppression en cours...")
    
    # Supprimer prix < 50 (clairement des volumes)
    result1 = db.curated_observations.delete_many({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'value': {'$lt': 50}
    }) if not dry_run else None
    
    count1 = result1.deleted_count if result1 else db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'value': {'$lt': 50}
    })
    
    print(f"\nOK Prix < 50 FCFA: {count1} observations {'supprimees' if not dry_run else 'a supprimer'}")
    
    # Supprimer prix < 500 pour actions à prix élevés
    count2 = 0
    for action in ACTIONS_PRIX_ELEVES:
        result2 = db.curated_observations.delete_many({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': action,
            'value': {'$lt': 500}
        }) if not dry_run else None
        
        c = result2.deleted_count if result2 else db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': action,
            'value': {'$lt': 500}
        })
        
        if c > 0:
            print(f"   - {action}: {c} observations {'supprimees' if not dry_run else 'a supprimer'}")
            count2 += c
    
    total = count1 + count2
    
    print("\n" + "="*80)
    print(f"TOTAL: {total} observations {'supprimees' if not dry_run else 'a supprimer'}")
    print("="*80)
    
    if dry_run:
        print("\n! Pour supprimer reellement, relancer avec --real")
    else:
        print("\nOK Nettoyage termine !")
        
        # Vérifier le résultat
        restantes = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE'
        })
        print(f"Observations BRVM restantes: {restantes}")


def main():
    import sys
    
    print("\n" + "="*80)
    print("NETTOYAGE DONNÉES BRVM ERRONÉES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Analyser
    analyser_donnees_suspectes()
    
    # 2. Nettoyer
    dry_run = '--real' not in sys.argv
    nettoyer_donnees_suspectes(dry_run=dry_run)


if __name__ == '__main__':
    main()

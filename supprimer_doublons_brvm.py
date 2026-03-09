#!/usr/bin/env python3
"""
Supprimer les doublons d'actions BRVM dans curated_observations
"""

import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Liste officielle des 47 actions BRVM (mise à jour janvier 2026)
ACTIONS_BRVM_47 = [
    'SDSC',   # Africa Global Logistics CI
    'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS',  # Bank of Africa (6 pays)
    'BICB',   # Banque Internationale pour l'Industrie et le Commerce du Benin
    'BNBC',   # Bernabe Côte d'Ivoire
    'BICC',   # BICI Côte d'Ivoire
    'CFAC',   # CFAO Motors Côte d'Ivoire
    'CIEC',   # CIE Côte d'Ivoire
    'CBIBF',  # Coris Bank International Burkina Faso
    'SEMC',   # Crown Siem Côte d'Ivoire
    'ECOC',   # Ecobank Côte d'Ivoire
    'ETIT',   # Ecobank Transnational Incorporated (Togo)
    'SIVC',   # Erium CI (ex Air Liquide CI)
    'FTSC',   # Filtisac Côte d'Ivoire
    'LNBB',   # Loterie Nationale du Benin
    'NEIC',   # NEI-CEDA Côte d'Ivoire
    'NSBC',   # NSIA Banque Côte d'Ivoire
    'ORGT',   # Oragroup Togo
    'SAFC',   # SAFCA – Alios Finance – Côte d'Ivoire
    'SGBC',   # SGB Côte d'Ivoire (Société Générale CI)
    'SIBC',   # Société Ivoirienne de Banque Côte d'Ivoire
    'SDCC',   # SODE Côte d'Ivoire
    'ONTBF',  # ONATEL Burkina Faso
    'ORAC',   # Orange Côte d'Ivoire
    'SNTS',   # Sonatel Senegal
    'NTLC',   # Nestlé Côte d'Ivoire
    'PALC',   # Palm Côte d'Ivoire
    'SPHC',   # SAPH Côte d'Ivoire
    'SICC',   # SICOR Côte d'Ivoire
    'STBC',   # SITAB Côte d'Ivoire
    'SOGC',   # SOGB Côte d'Ivoire
    'SLBC',   # Solibra Côte d'Ivoire
    'SCRC',   # Sucrivoire Côte d'Ivoire
    'UNLC',   # Unilever Côte d'Ivoire
    'UNXC',   # Uni-Wax Côte d'Ivoire
    'SMBC',   # SMB Côte d'Ivoire
    'PRSC',   # Tractafric Motors Côte d'Ivoire
    'SHEC',   # Vivo Energy Côte d'Ivoire
    'TTLC',   # Total Côte d'Ivoire
    'TTLS',   # Total Senegal
    'CABC',   # Sicable Côte d'Ivoire
    'BBGCI'   # Bridge Bank Groupe Côte d'Ivoire
]

def supprimer_doublons(dry_run=True):
    """Supprimer les actions en doublon (garder dernière observation)"""
    _, db = get_mongo_db()
    
    print("="*100)
    print("SUPPRESSION DES DOUBLONS BRVM")
    print("="*100)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if dry_run:
        print("\n!  MODE DRY-RUN - Aucune suppression reelle")
    else:
        print("\n MODE REEL - Suppression en cours...")
    
    # Récupérer toutes les actions distinctes
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': '$key'}}
    ]
    
    actions_en_base = [doc['_id'] for doc in db.curated_observations.aggregate(pipeline)]
    
    print(f"\nTotal actions en base: {len(actions_en_base)}")
    print(f"Total actions officielles: {len(set(ACTIONS_BRVM_47))}")
    
    # Identifier les doublons et actions invalides
    doublons = []
    for action in actions_en_base:
        if action not in ACTIONS_BRVM_47:
            doublons.append(action)
    
    print(f"\n!  {len(doublons)} actions a supprimer (doublons ou invalides):")
    for action in sorted(doublons):
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': action
        })
        print(f"   - {action}: {count} observations")
    
    # Supprimer les doublons
    if doublons:
        if not dry_run:
            result = db.curated_observations.delete_many({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': {'$in': doublons}
            })
            print(f"\nOK {result.deleted_count} observations supprimees")
        else:
            total_a_supprimer = sum(
                db.curated_observations.count_documents({
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': action
                })
                for action in doublons
            )
            print(f"\n!  {total_a_supprimer} observations a supprimer")
    
    # Vérifier doublons sur même date
    print("\n" + "="*100)
    print("VERIFICATION DES DOUBLONS PAR DATE:")
    print("="*100)
    
    pipeline_duplicates = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'key': {'$in': ACTIONS_BRVM_47}}},
        {'$group': {
            '_id': {'key': '$key', 'ts': '$ts'},
            'count': {'$sum': 1},
            'ids': {'$push': '$_id'}
        }},
        {'$match': {'count': {'$gt': 1}}}
    ]
    
    duplicates = list(db.curated_observations.aggregate(pipeline_duplicates))
    
    if duplicates:
        print(f"\n!  {len(duplicates)} doublons sur meme date trouves:")
        
        total_supprime = 0
        for dup in duplicates:
            action = dup['_id']['key']
            date = dup['_id']['ts']
            count = dup['count']
            ids = dup['ids']
            
            print(f"   - {action} ({date}): {count} observations")
            
            # Garder la dernière, supprimer les autres
            if not dry_run:
                ids_to_delete = ids[:-1]  # Garder le dernier
                result = db.curated_observations.delete_many({
                    '_id': {'$in': ids_to_delete}
                })
                total_supprime += result.deleted_count
        
        if not dry_run:
            print(f"\nOK {total_supprime} doublons de dates supprimes")
        else:
            print(f"\n!  {sum(d['count']-1 for d in duplicates)} doublons de dates a supprimer")
    else:
        print("\nOK Aucun doublon sur meme date")
    
    # Statistiques finales
    print("\n" + "="*100)
    print("STATISTIQUES FINALES:")
    print("="*100)
    
    if not dry_run:
        actions_restantes = list(db.curated_observations.aggregate(pipeline))
        total_obs = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE'
        })
        
        print(f"\nActions uniques en base: {len(actions_restantes)}")
        print(f"Total observations BRVM: {total_obs}")
    else:
        print("\n!  Pour supprimer reellement, relancer avec --real")
    
    print("="*100)

if __name__ == '__main__':
    import sys
    dry_run = '--real' not in sys.argv
    supprimer_doublons(dry_run=dry_run)

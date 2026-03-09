#!/usr/bin/env python3
"""
NETTOYAGE - Supprimer TOUTES les donnees SIMULEES
Politique ZERO TOLERANCE
"""
from pymongo import MongoClient
from datetime import datetime

print("\n" + "="*80)
print("NETTOYAGE DONNEES SIMULEES - POLITIQUE ZERO TOLERANCE")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    db = client['centralisation_db']
    
    # Vérifier avant suppression
    print("\n[AVANT SUPPRESSION]")
    total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
    reel = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    simule = total_brvm - reel
    
    print(f"  BRVM Total    : {total_brvm}")
    print(f"  BRVM REEL     : {reel}")
    print(f"  BRVM SIMULE   : {simule}")
    
    if simule == 0:
        print("\n✓ Aucune donnée simulée détectée. Base propre!")
        client.close()
        exit(0)
    
    # SUPPRESSION
    print("\n" + "-"*80)
    print(f"⚠️  SUPPRESSION de {simule} observations SIMULEES...")
    print("-"*80)
    
    # Supprimer les observations sans data_quality ou avec valeur autre que REAL_*
    result = db.curated_observations.delete_many({
        'source': 'BRVM',
        '$or': [
            {'attrs.data_quality': {'$exists': False}},
            {'attrs.data_quality': None},
            {'attrs.data_quality': ''},
            {'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}}
        ]
    })
    
    print(f"\n✓ {result.deleted_count} observations supprimées")
    
    # Vérifier après suppression
    print("\n[APRES SUPPRESSION]")
    total_brvm_after = db.curated_observations.count_documents({'source': 'BRVM'})
    reel_after = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    simule_after = total_brvm_after - reel_after
    
    print(f"  BRVM Total    : {total_brvm_after}")
    print(f"  BRVM REEL     : {reel_after}")
    print(f"  BRVM SIMULE   : {simule_after}")
    
    if simule_after == 0:
        print("\n✓✓✓ NETTOYAGE REUSSI - Base 100% REELLE ✓✓✓")
    else:
        print(f"\n⚠️  Attention: {simule_after} observations simulées restantes")
    
    print("\n" + "="*80)
    
    client.close()
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""Rapport complet des donnees REELLES"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*80)
print("RAPPORT DONNEES REELLES - POLITIQUE ZERO TOLERANCE")
print("="*80)

try:
    client, db = get_mongo_db()
    
    # Total
    total = db.curated_observations.count_documents({})
    print(f"\n📊 Total observations: {total:,}")
    
    # Par source
    print("\n" + "-"*80)
    print("OBSERVATIONS PAR SOURCE")
    print("-"*80)
    
    sources = [
        ('BRVM', 'Bourse BRVM'),
        ('WorldBank', 'Banque Mondiale'),
        ('IMF', 'FMI'),
        ('AfDB', 'Banque Africaine Dev'),
        ('UN_SDG', 'ODD Nations Unies')
    ]
    
    total_reel = 0
    
    for source, nom in sources:
        count = db.curated_observations.count_documents({'source': source})
        
        if count > 0:
            if source == 'BRVM':
                # Vérifier data_quality
                reel = db.curated_observations.count_documents({
                    'source': source,
                    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
                })
                simule = count - reel
                total_reel += reel
                
                print(f"\n{nom} ({source})")
                print(f"  Total      : {count:6,}")
                print(f"  REEL       : {reel:6,} ✓")
                if simule > 0:
                    print(f"  SIMULE     : {simule:6,} ⚠️")
            else:
                total_reel += count
                print(f"\n{nom} ({source})")
                print(f"  Total      : {count:6,} ✓")
    
    # Data quality BRVM
    print("\n" + "-"*80)
    print("DATA QUALITY BRVM")
    print("-"*80)
    
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': '$attrs.data_quality', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    for doc in db.curated_observations.aggregate(pipeline):
        quality = doc['_id'] if doc['_id'] else 'NON_SPECIFIE'
        status = "✓" if quality in ['REAL_MANUAL', 'REAL_SCRAPER'] else "⚠️"
        print(f"  {quality:20s}: {doc['count']:6,} {status}")
    
    # Dates récentes BRVM
    print("\n" + "-"*80)
    print("DERNIERES DONNEES BRVM (5 plus récentes)")
    print("-"*80)
    
    recent = db.curated_observations.find(
        {'source': 'BRVM'},
        {'ts': 1, 'key': 1, 'value': 1, 'attrs.data_quality': 1}
    ).sort('ts', -1).limit(5)
    
    for obs in recent:
        quality = obs.get('attrs', {}).get('data_quality', 'NON_SPECIFIE')
        status = "✓" if quality in ['REAL_MANUAL', 'REAL_SCRAPER'] else "⚠️"
        symbol = obs.get('key', 'N/A')
        price = obs.get('value', 0)
        print(f"  {obs['ts']} | {symbol:12s} | {price:8.0f} | {quality:15s} {status}")
    
    # Synthèse finale
    print("\n" + "="*80)
    print("SYNTHESE")
    print("="*80)
    print(f"\n✓ Total observations REELLES: {total_reel:,}")
    
    brvm_simule = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    if brvm_simule == 0:
        print("✓ Aucune donnée simulée - Base 100% REELLE")
        print("\n🎯 POLITIQUE ZERO TOLERANCE RESPECTEE ✓")
    else:
        print(f"\n⚠️  {brvm_simule} observations simulées détectées")
        print("\nACTION: python nettoyer_donnees_simulees.py")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

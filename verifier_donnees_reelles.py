#!/usr/bin/env python3
"""
Verification des donnees REELLES uniquement - Sans Django
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# Connexion MongoDB directe
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_NAME = os.getenv('MONGODB_NAME', 'centralisation_db')

print("\n" + "="*80)
print("AUDIT DONNEES REELLES - POLITIQUE ZERO TOLERANCE")
print("="*80)
print(f"MongoDB: {MONGODB_URI}")
print(f"Database: {MONGODB_NAME}")
print("="*80)

try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_NAME]
    
    # Test connexion
    db.command('ping')
    print("\n✓ Connexion MongoDB OK")
    
    # Total observations
    total = db.curated_observations.count_documents({})
    print(f"\nTotal observations: {total}")
    
    # Par source
    print("\n" + "-"*80)
    print("OBSERVATIONS PAR SOURCE")
    print("-"*80)
    
    sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
    total_reel = 0
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        
        if source == 'BRVM':
            # Pour BRVM, vérifier data_quality
            reel = db.curated_observations.count_documents({
                'source': source,
                'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
            })
            simule = count - reel
            total_reel += reel
            
            print(f"\n{source}:")
            print(f"  Total      : {count:6d}")
            print(f"  REEL       : {reel:6d} ✓")
            if simule > 0:
                print(f"  SIMULE     : {simule:6d} ⚠️  A SUPPRIMER!")
        else:
            total_reel += count
            print(f"\n{source}:")
            print(f"  Total      : {count:6d}")
    
    print("\n" + "-"*80)
    print(f"TOTAL OBSERVATIONS REELLES: {total_reel}")
    print("-"*80)
    
    # Vérifier data_quality pour BRVM
    print("\n" + "-"*80)
    print("DATA QUALITY BRVM (obligatoire)")
    print("-"*80)
    
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': '$attrs.data_quality', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    for doc in db.curated_observations.aggregate(pipeline):
        quality = doc['_id'] if doc['_id'] else 'NON_SPECIFIE'
        status = "✓" if quality in ['REAL_MANUAL', 'REAL_SCRAPER'] else "⚠️"
        print(f"  {quality:20s}: {doc['count']:6d} {status}")
    
    # Dates BRVM
    print("\n" + "-"*80)
    print("DATES BRVM (dernières données)")
    print("-"*80)
    
    brvm_dates = db.curated_observations.find(
        {'source': 'BRVM'},
        {'ts': 1, 'attrs.data_quality': 1}
    ).sort('ts', -1).limit(5)
    
    for obs in brvm_dates:
        quality = obs.get('attrs', {}).get('data_quality', 'NON_SPECIFIE')
        status = "✓" if quality in ['REAL_MANUAL', 'REAL_SCRAPER'] else "⚠️"
        print(f"  {obs['ts']:12s} - {quality:15s} {status}")
    
    print("\n" + "="*80)
    print("ACTIONS REQUISES")
    print("="*80)
    
    simule_count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    if simule_count > 0:
        print(f"\n⚠️  ALERTE: {simule_count} observations BRVM avec données SIMULEES detectees!")
        print("\nCommandes de nettoyage:")
        print("  # Supprimer toutes les données simulées BRVM")
        print("  python nettoyer_donnees_simulees.py")
        print("\n  # Ou MongoDB direct:")
        print("  db.curated_observations.deleteMany({")
        print("    source: 'BRVM',")
        print("    'attrs.data_quality': {$nin: ['REAL_MANUAL', 'REAL_SCRAPER']}")
        print("  })")
    else:
        print("\n✓ Aucune donnée simulée détectée pour BRVM")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    if 'client' in locals():
        client.close()

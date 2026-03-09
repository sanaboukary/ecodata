#!/usr/bin/env python3
"""Verification MongoDB simple"""
from pymongo import MongoClient

try:
    print("Connexion a MongoDB...")
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    
    # Test connexion
    client.admin.command('ping')
    print("✓ MongoDB OK")
    
    db = client['centralisation_db']
    
    # Compter
    total = db.curated_observations.count_documents({})
    brvm = db.curated_observations.count_documents({'source': 'BRVM'})
    wb = db.curated_observations.count_documents({'source': 'WorldBank'})
    
    print(f"\nTotal: {total}")
    print(f"BRVM: {brvm}")
    print(f"WorldBank: {wb}")
    
    # Vérifier data_quality BRVM
    if brvm > 0:
        reel = db.curated_observations.count_documents({
            'source': 'BRVM',
            'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
        })
        simule = brvm - reel
        
        print(f"\nBRVM REEL: {reel}")
        print(f"BRVM SIMULE: {simule}")
        
        if simule > 0:
            print(f"\n⚠️  ALERTE: {simule} observations SIMULEES à supprimer!")
        else:
            print("\n✓ Toutes les données BRVM sont REELLES")
    
    client.close()
    
except Exception as e:
    print(f"❌ ERREUR: {e}")

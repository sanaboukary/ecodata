#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérification rapide de la collecte du jour
"""

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def verifier_collecte_aujourdhui():
    client, db = get_mongo_db()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"📅 VÉRIFICATION COLLECTE DU {today}")
    print(f"{'='*60}\n")
    
    # Compter observations du jour
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': today
    })
    
    print(f"📊 Observations collectées aujourd'hui: {count}")
    
    if count > 0:
        # Actions distinctes
        actions = db.curated_observations.distinct('key', {
            'source': 'BRVM',
            'ts': today
        })
        print(f"📈 Actions distinctes: {len(actions)}")
        
        # Vérifier qualité des données
        quality_check = db.curated_observations.find({
            'source': 'BRVM',
            'ts': today
        }).limit(5)
        
        print(f"\n✅ COLLECTE RÉUSSIE - Échantillon:")
        for i, obs in enumerate(quality_check, 1):
            quality = obs.get('attrs', {}).get('data_quality', 'UNKNOWN')
            value = obs.get('value', 0)
            print(f"   {i}. {obs['key']}: {value} FCFA ({quality})")
        
        # Statistiques globales
        total = db.curated_observations.count_documents({'source': 'BRVM'})
        print(f"\n📈 Total historique BRVM: {total} observations")
        
    else:
        print("\n⚠️ AUCUNE DONNÉE COLLECTÉE AUJOURD'HUI")
        print("\n💡 Solutions:")
        print("   1. Lancer: python mettre_a_jour_cours_brvm.py (saisie manuelle)")
        print("   2. Vérifier Airflow: http://localhost:8080")
        print("   3. Scraper: python scripts/connectors/brvm_scraper_production.py")
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    verifier_collecte_aujourdhui()

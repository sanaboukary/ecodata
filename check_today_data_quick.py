#!/usr/bin/env python3
"""Vérification rapide des données du jour"""
import os
import sys
from datetime import datetime

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def check():
    client, db = get_mongo_db()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n🔍 VÉRIFICATION RAPIDE - {today}")
    print("=" * 60)
    
    # Compter données BRVM aujourd'hui
    brvm_count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': today
    })
    
    print(f"\n📊 BRVM - Cours: {brvm_count} observations pour {today}")
    
    if brvm_count == 0:
        print("\n⚠️  AUCUNE DONNÉE COLLECTÉE AUJOURD'HUI")
        print("\n💡 Pour collecter les données maintenant:")
        print("   python collecter_brvm_horaire_auto.py")
    else:
        # Afficher échantillon
        print(f"\n✅ {brvm_count} actions collectées")
        print("\nDernières données:")
        sample = list(db.curated_observations.find({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'ts': today
        }).sort('key', 1).limit(10))
        
        for obs in sample:
            symbol = obs['key']
            price = obs['value']
            volume = obs.get('attrs', {}).get('volume', 0)
            var = obs.get('attrs', {}).get('variation', 0)
            print(f"   {symbol:8s} | {price:10,.0f} FCFA | Vol: {volume:8,} | Var: {var:+6.2f}%")
        
        if brvm_count > 10:
            print(f"\n   ... et {brvm_count - 10} autres actions")
    
    client.close()

if __name__ == '__main__':
    check()

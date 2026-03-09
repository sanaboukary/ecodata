#!/usr/bin/env python3
"""
Vérifier les attributs disponibles dans curated_observations BRVM
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
from datetime import datetime

def verifier_attributs():
    _, db = get_mongo_db()
    
    print("="*100)
    print("VÉRIFICATION DES ATTRIBUTS BRVM")
    print("="*100)
    
    # Récupérer une observation récente
    dernier = db.curated_observations.find_one({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    }, sort=[('ts', -1)])
    
    if dernier:
        print(f"\nAction: {dernier.get('key')}")
        print(f"Date: {dernier.get('ts')}")
        print(f"Prix: {dernier.get('value')}")
        print(f"\nAttributs disponibles:")
        print("-"*100)
        
        attrs = dernier.get('attrs', {})
        for key, value in sorted(attrs.items()):
            print(f"  {key:25} = {value}")
        
        # Vérifier attributs manquants pour le dashboard
        print(f"\n{'='*100}")
        print("ATTRIBUTS REQUIS PAR LE DASHBOARD:")
        print("="*100)
        
        requis = {
            'market_cap': 'Capitalisation boursière',
            'pe_ratio': 'Price/Earnings ratio',
            'sector': 'Secteur d\'activité',
            'day_change_pct': 'Variation journalière %',
            'consensus_score': 'Score consensus analystes',
            'recommendation': 'Recommandation (BUY/HOLD/SELL)',
            'target_price': 'Prix cible',
            'dividend_yield': 'Rendement dividende',
            'shares_outstanding': 'Nombre d\'actions'
        }
        
        for attr, description in requis.items():
            present = "✅ OUI" if attr in attrs else "❌ NON"
            valeur = attrs.get(attr, "N/A")
            print(f"  {present}  {attr:25} ({description:40}) = {valeur}")
    
    # Compter les actions avec/sans attributs
    print(f"\n{'='*100}")
    print("STATISTIQUES PAR ATTRIBUT:")
    print("="*100)
    
    pipeline_latest = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$sort': {'ts': -1}},
        {'$group': {
            '_id': '$key',
            'last_doc': {'$first': '$$ROOT'}
        }}
    ]
    
    latest_stocks = list(db.curated_observations.aggregate(pipeline_latest))
    total = len(latest_stocks)
    
    print(f"\nTotal actions: {total}\n")
    
    for attr, description in requis.items():
        count = sum(1 for s in latest_stocks if attr in s.get('last_doc', {}).get('attrs', {}))
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {attr:25}: {count:3}/{total} ({pct:5.1f}%) - {description}")
    
    print("="*100)

if __name__ == '__main__':
    verifier_attributs()

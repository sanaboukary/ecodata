#!/usr/bin/env python3
"""
Restaurer les données BRVM supprimées depuis raw_events ou re-scraper
"""

import pymongo
from datetime import datetime, timedelta
import json

def analyser_sources_disponibles():
    """Analyser sources de données BRVM disponibles"""
    
    print(f"[ANALYSE SOURCES DONNÉES BRVM]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    # 1. Vérifier curated_observations
    print("[1/3] Vérification curated_observations...")
    
    # Compter par dataset
    pipeline = [
        {'$group': {
            '_id': '$dataset',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    datasets = list(db.curated_observations.aggregate(pipeline))
    
    print(f"  Datasets trouvés:")
    for ds in datasets:
        print(f"    {ds['_id']}: {ds['count']} observations")
    
    # Vérifier STOCK_PRICE
    stock_price_count = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    print(f"\n  STOCK_PRICE: {stock_price_count} observations")
    
    if stock_price_count > 0:
        # Vérifier combien ont symbole None
        none_symbole = db.curated_observations.count_documents({
            'dataset': 'STOCK_PRICE',
            'ticker': None
        })
        print(f"    Avec ticker=None: {none_symbole}")
        
        # Avec ticker valide
        valid_ticker = stock_price_count - none_symbole
        print(f"    Avec ticker valide: {valid_ticker}")
        
        if valid_ticker > 0:
            # Lister tickers valides
            tickers = db.curated_observations.distinct('ticker', {
                'dataset': 'STOCK_PRICE',
                'ticker': {'$ne': None}
            })
            print(f"    Tickers: {tickers}")
    
    # 2. Vérifier raw_events pour données BRVM
    print(f"\n[2/3] Vérification raw_events...")
    
    raw_count = db.raw_events.count_documents({})
    print(f"  Total raw_events: {raw_count}")
    
    # Chercher événements BRVM récents
    sources_brvm = db.raw_events.distinct('source')
    print(f"  Sources: {sources_brvm[:20]}")
    
    # Compter par source
    pipeline_sources = [
        {'$group': {
            '_id': '$source',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 20}
    ]
    sources = list(db.raw_events.aggregate(pipeline_sources))
    
    print(f"\n  Top sources:")
    for src in sources:
        print(f"    {src['_id']}: {src['count']} événements")
        
        # Si c'est BRVM, vérifier payload
        if any(keyword in str(src['_id']).lower() for keyword in ['brvm', 'stock', 'bourse']):
            sample = db.raw_events.find_one({'source': src['_id']})
            if sample and 'payload' in sample:
                print(f"      Payload exemple: {str(sample['payload'])[:200]}")
    
    # 3. Chercher données BRVM dans raw_events
    print(f"\n[3/3] Recherche données BRVM dans raw_events...")
    
    # Essayer différents patterns
    brvm_patterns = [
        {'source': {'$regex': 'brvm', '$options': 'i'}},
        {'source': {'$regex': 'stock', '$options': 'i'}},
        {'source': {'$regex': 'bourse', '$options': 'i'}},
    ]
    
    for pattern in brvm_patterns:
        count = db.raw_events.count_documents(pattern)
        if count > 0:
            print(f"  Pattern {pattern}: {count} événements")
            
            # Échantillon
            sample = db.raw_events.find_one(pattern)
            if sample:
                print(f"    Source: {sample.get('source')}")
                print(f"    Date: {sample.get('fetched_at')}")
                if 'payload' in sample:
                    payload = sample['payload']
                    if isinstance(payload, dict):
                        print(f"    Payload keys: {list(payload.keys())[:10]}")
                    elif isinstance(payload, str):
                        print(f"    Payload: {payload[:200]}")
    
    # Proposition de restauration
    print(f"\n[PROPOSITION RESTAURATION]")
    
    if stock_price_count > 0:
        none_count = db.curated_observations.count_documents({
            'dataset': 'STOCK_PRICE',
            'ticker': None
        })
        valid_count = stock_price_count - none_count
        
        if none_count > 0:
            print(f"\n  Option 1: TRAITER les {none_count} observations ticker=None")
            print(f"    - Analyser les patterns de prix pour identifier l'action")
            print(f"    - Utiliser timestamp + prix pour mapper au ticker BRVM")
            print(f"    - Compléter le champ ticker au lieu de supprimer")
        
        if valid_count > 0:
            print(f"\n  Option 2: UTILISER les {valid_count} observations avec ticker valide")
            print(f"    - Ignorer les observations None")
            print(f"    - Générer analyses depuis données valides uniquement")
    
    # Vérifier si on peut re-scraper
    print(f"\n  Option 3: RE-SCRAPER depuis brvm.org")
    print(f"    - Collecter données fraîches avec symboles")
    print(f"    - Script: brvm_scraper_47_actions.py")
    
    client.close()

if __name__ == "__main__":
    try:
        analyser_sources_disponibles()
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

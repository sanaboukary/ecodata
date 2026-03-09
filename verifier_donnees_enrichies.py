#!/usr/bin/env python3
"""
Vérifier les données enrichies collectées dans MongoDB
"""

import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['centralisation_db']
    
    print("=" * 80)
    print("📊 VÉRIFICATION DES DONNÉES ENRICHIES BRVM")
    print("=" * 80)
    
    # Compter observations
    total = db.curated_observations.count_documents({'source': 'BRVM'})
    print(f"\n📈 Total observations BRVM: {total}")
    
    # Actions uniques
    actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
    print(f"🎯 Actions uniques: {len(actions)}")
    
    # Dernière collecte
    derniere = db.curated_observations.find_one(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
        sort=[('attrs.collected_at', -1)]
    )
    
    if derniere:
        print(f"\n⏰ Dernière collecte: {derniere['attrs'].get('collected_at', 'N/A')}")
        print(f"📅 Date (ts): {derniere.get('ts', 'N/A')}")
    
    # Échantillon de données enrichies
    print("\n" + "=" * 80)
    print("📋 ÉCHANTILLON DE DONNÉES ENRICHIES (3 actions)")
    print("=" * 80)
    
    for symbol in actions[:3]:
        obs = db.curated_observations.find_one({
            'source': 'BRVM',
            'key': symbol
        })
        
        if obs:
            print(f"\n🔹 {symbol}")
            print(f"   Prix Close: {obs.get('value', 'N/A'):,.0f} FCFA")
            
            attrs = obs.get('attrs', {})
            
            # Prix OHLC
            if attrs.get('open'):
                print(f"   Open: {attrs['open']:,.0f} | High: {attrs.get('high', 'N/A'):,.0f} | Low: {attrs.get('low', 'N/A'):,.0f}")
            
            # Variation
            if attrs.get('variation_pct') is not None:
                print(f"   Variation: {attrs['variation_pct']:+.2f}%")
            
            # Volume et liquidité
            if attrs.get('volume'):
                print(f"   Volume: {attrs['volume']:,}")
                print(f"   Liquidité: {attrs.get('liquidity_score', 'N/A')}")
            
            if attrs.get('value_traded_millions'):
                print(f"   Valeur échangée: {attrs['value_traded_millions']:.2f}M FCFA")
            
            # Volatilité
            if attrs.get('volatility_daily'):
                print(f"   Volatilité: {attrs['volatility_daily']:.2f}% (quotidienne)")
            
            if attrs.get('daily_range_pct'):
                print(f"   Range: {attrs['daily_range_pct']:.2f}%")
            
            # Data quality
            print(f"   Qualité: {attrs.get('data_quality', 'N/A')}")
            print(f"   Méthode: {attrs.get('scraper_method', 'N/A')}")
    
    # Statistiques par attribut
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES DES ATTRIBUTS COLLECTÉS")
    print("=" * 80)
    
    attributs_cles = [
        'open', 'high', 'low', 'close', 'previous',
        'variation_pct', 'variation_abs',
        'volume', 'value_traded', 'liquidity_score',
        'volatility_daily', 'volatility_category',
        'daily_range', 'daily_range_pct',
        'market_cap'
    ]
    
    for attr in attributs_cles:
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            f'attrs.{attr}': {'$exists': True, '$ne': None}
        })
        pct = (count / total * 100) if total > 0 else 0
        print(f"   {attr:20s}: {count:3d}/{total} ({pct:5.1f}%)")
    
    # Qualité des données
    print("\n" + "=" * 80)
    print("🔍 QUALITÉ DES DONNÉES")
    print("=" * 80)
    
    quality_counts = db.curated_observations.aggregate([
        {'$match': {'source': 'BRVM'}},
        {'$group': {
            '_id': '$attrs.data_quality',
            'count': {'$sum': 1}
        }}
    ])
    
    for item in quality_counts:
        quality = item['_id'] or 'Non défini'
        count = item['count']
        print(f"   {quality}: {count} observations")
    
    # Méthodes de collecte
    print("\n📡 Méthodes de scraping utilisées:")
    
    method_counts = db.curated_observations.aggregate([
        {'$match': {'source': 'BRVM'}},
        {'$group': {
            '_id': '$attrs.scraper_method',
            'count': {'$sum': 1}
        }}
    ])
    
    for item in method_counts:
        method = item['_id'] or 'Non défini'
        count = item['count']
        print(f"   {method}: {count} observations")
    
    print("\n" + "=" * 80)
    print("✅ Vérification terminée")
    print("=" * 80)


if __name__ == '__main__':
    main()

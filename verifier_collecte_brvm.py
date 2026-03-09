#!/usr/bin/env python
"""
Vérification des données BRVM collectées
Affiche les cours, variations, volatilité, liquidité, etc.
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    print("=" * 80)
    print("📊 VÉRIFICATION COLLECTE BRVM")
    print("=" * 80)
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    # Compter observations BRVM
    total_brvm = collection.count_documents({'source': 'BRVM'})
    print(f"\n📈 Total observations BRVM : {total_brvm}")
    
    # Données d'aujourd'hui
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = collection.count_documents({
        'source': 'BRVM',
        'ts': today
    })
    print(f"📅 Observations aujourd'hui ({today}) : {today_count}")
    
    # Dernières données
    print("\n" + "=" * 80)
    print("📋 ÉCHANTILLON DES DONNÉES COLLECTÉES (5 plus récentes)")
    print("=" * 80)
    
    recent = list(collection.find({
        'source': 'BRVM'
    }).sort('ts', -1).limit(5))
    
    for i, obs in enumerate(recent, 1):
        print(f"\n{i}. {obs.get('key', 'N/A')} - {obs.get('ts', 'N/A')}")
        print(f"   💰 Prix (Close): {obs.get('value', 'N/A')} FCFA")
        
        attrs = obs.get('attrs', {})
        print(f"   📊 Attributs disponibles:")
        
        # Prix OHLC
        if 'open' in attrs:
            print(f"      • Open: {attrs['open']}")
        if 'high' in attrs:
            print(f"      • High: {attrs['high']}")
        if 'low' in attrs:
            print(f"      • Low: {attrs['low']}")
        if 'previous' in attrs:
            print(f"      • Previous: {attrs['previous']}")
            
        # Variations
        if 'variation_pct' in attrs:
            print(f"      • Variation %: {attrs['variation_pct']}%")
        if 'variation_abs' in attrs:
            print(f"      • Variation absolue: {attrs['variation_abs']}")
        if 'variation_1d' in attrs:
            print(f"      • Variation 1J: {attrs['variation_1d']}%")
        if 'variation_1w' in attrs:
            print(f"      • Variation 1S: {attrs['variation_1w']}%")
        if 'variation_1m' in attrs:
            print(f"      • Variation 1M: {attrs['variation_1m']}%")
        if 'variation_ytd' in attrs:
            print(f"      • Variation YTD: {attrs['variation_ytd']}%")
            
        # Volume et liquidité
        if 'volume' in attrs:
            print(f"      • Volume: {attrs['volume']}")
        if 'value_traded' in attrs:
            print(f"      • Valeur échangée: {attrs['value_traded']} FCFA")
        if 'trades_count' in attrs:
            print(f"      • Nombre transactions: {attrs['trades_count']}")
        if 'avg_volume' in attrs:
            print(f"      • Volume moyen: {attrs['avg_volume']}")
        if 'liquidity_score' in attrs:
            print(f"      • Score liquidité: {attrs['liquidity_score']}")
            
        # Volatilité
        if 'volatility' in attrs:
            print(f"      • Volatilité: {attrs['volatility']}%")
        if 'volatility_20d' in attrs:
            print(f"      • Volatilité 20J: {attrs['volatility_20d']}%")
        if 'beta' in attrs:
            print(f"      • Beta: {attrs['beta']}")
            
        # Market Cap
        if 'market_cap' in attrs:
            print(f"      • Market Cap: {attrs['market_cap']} FCFA")
            
        # Indicateurs techniques
        if 'rsi' in attrs:
            print(f"      • RSI: {attrs['rsi']}")
        if 'sma_20' in attrs:
            print(f"      • SMA 20: {attrs['sma_20']}")
        if 'sma_50' in attrs:
            print(f"      • SMA 50: {attrs['sma_50']}")
            
        # Qualité des données
        if 'data_quality' in attrs:
            print(f"      • Qualité: {attrs['data_quality']}")
        if 'collection_method' in attrs:
            print(f"      • Méthode: {attrs['collection_method']}")
    
    # Actions uniques collectées
    print("\n" + "=" * 80)
    print("🏢 ACTIONS COLLECTÉES")
    print("=" * 80)
    
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': '$key'}},
        {'$sort': {'_id': 1}}
    ]
    
    actions = list(collection.aggregate(pipeline))
    print(f"\nNombre d'actions uniques: {len(actions)}")
    
    if len(actions) > 0:
        print("\nListe des actions:")
        for i, action in enumerate(actions, 1):
            symbol = action['_id']
            # Compter observations par action
            count = collection.count_documents({'source': 'BRVM', 'key': symbol})
            print(f"  {i:2d}. {symbol:10s} - {count:4d} observations")
    
    # Résumé des métriques disponibles
    print("\n" + "=" * 80)
    print("📈 MÉTRIQUES DISPONIBLES (par action)")
    print("=" * 80)
    
    # Analyser un échantillon pour voir quels attributs sont disponibles
    sample = collection.find_one({'source': 'BRVM'})
    if sample and 'attrs' in sample:
        attrs = sample['attrs']
        print("\n✅ Attributs trouvés dans les données:")
        
        metrics = {
            'Prix': ['open', 'high', 'low', 'close', 'previous'],
            'Variation': ['variation_pct', 'variation_abs', 'variation_1d', 'variation_1w', 'variation_1m', 'variation_ytd'],
            'Volume/Liquidité': ['volume', 'value_traded', 'trades_count', 'avg_volume', 'liquidity_score'],
            'Volatilité': ['volatility', 'volatility_20d', 'beta'],
            'Valorisation': ['market_cap', 'pe_ratio', 'pb_ratio'],
            'Technique': ['rsi', 'sma_20', 'sma_50', 'support', 'resistance']
        }
        
        for category, keys in metrics.items():
            found = [k for k in keys if k in attrs]
            if found:
                print(f"\n  {category}:")
                for key in found:
                    print(f"    ✓ {key}: {attrs[key]}")
    
    print("\n" + "=" * 80)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 80)

if __name__ == '__main__':
    main()

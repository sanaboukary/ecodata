#!/usr/bin/env python
"""
Sauvegarder les recommandations IA dans MongoDB
"""
import os
import json
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def sauvegarder_recommandations():
    print("=" * 80)
    print("💾 SAUVEGARDE RECOMMANDATIONS IA DANS MONGODB")
    print("=" * 80)
    
    # Charger recommandations
    with open('recommandations_ia_latest.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    print(f"\n📊 Chargement des recommandations...")
    print(f"   • Date: {data['generated_at']}")
    print(f"   • Actions analysées: {data['total_actions_analyzed']}")
    
    # Sauvegarder chaque recommandation BUY
    buy_signals = data.get('buy_signals', [])
    saved_count = 0
    
    for signal in buy_signals:
        obs = {
            'source': 'AI_ANALYSIS',
            'dataset': 'RECOMMENDATION',
            'key': signal['symbol'],
            'ts': datetime.now().strftime('%Y-%m-%d'),
            'value': signal['signal_score'],
            'attrs': {
                'signal': signal['signal'],
                'confidence': signal['confidence'],
                'current_price': signal['current_price'],
                'target_price': signal['target_price'],
                'stop_loss': signal['stop_loss'],
                'potential_gain': signal['potential_gain'],
                'volatility': signal['volatility'],
                'volume_ratio': signal['volume_ratio'],
                'trend': signal['trend'],
                'reasons': signal.get('reasons', []),
                'sector': signal.get('macro_context', {}).get('sector'),
                'data_quality': 'AI_GENERATED',
                'generated_at': data['generated_at']
            }
        }
        
        # Upsert (update or insert)
        collection.update_one(
            {
                'source': 'AI_ANALYSIS',
                'dataset': 'RECOMMENDATION',
                'key': signal['symbol'],
                'ts': obs['ts']
            },
            {'$set': obs},
            upsert=True
        )
        saved_count += 1
    
    print(f"\n✅ {saved_count} recommandations BUY sauvegardées")
    
    # Sauvegarder HOLD et SELL aussi
    hold_signals = data.get('hold_signals', [])
    for signal in hold_signals[:10]:  # Limiter à 10 pour ne pas surcharger
        obs = {
            'source': 'AI_ANALYSIS',
            'dataset': 'RECOMMENDATION',
            'key': signal['symbol'],
            'ts': datetime.now().strftime('%Y-%m-%d'),
            'value': signal['signal_score'],
            'attrs': {
                'signal': 'HOLD',
                'confidence': signal.get('confidence', 50),
                'current_price': signal.get('current_price'),
                'data_quality': 'AI_GENERATED'
            }
        }
        collection.update_one(
            {
                'source': 'AI_ANALYSIS',
                'dataset': 'RECOMMENDATION',
                'key': signal['symbol'],
                'ts': obs['ts']
            },
            {'$set': obs},
            upsert=True
        )
    
    print(f"✅ {min(len(hold_signals), 10)} recommandations HOLD sauvegardées")
    
    # Vérifier sauvegarde
    total_reco = collection.count_documents({
        'source': 'AI_ANALYSIS',
        'dataset': 'RECOMMENDATION'
    })
    
    print(f"\n📊 Total recommandations en base: {total_reco}")
    print("\n" + "=" * 80)
    print("✅ SAUVEGARDE TERMINÉE")
    print("=" * 80)

if __name__ == '__main__':
    sauvegarder_recommandations()

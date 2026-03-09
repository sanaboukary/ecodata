#!/usr/bin/env python3
"""Diagnostic rapide des données WEEKLY pour TOP5"""
from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    week = '2026-W02'
    print(f"\n🔍 DIAGNOSTIC WEEKLY - {week}\n")
    
    # Total actions
    total = db.prices_weekly.count_documents({'week': week})
    print(f"📊 Total actions: {total}")
    
    # Avec indicateurs
    with_ind = db.prices_weekly.count_documents({
        'week': week,
        'indicators_computed': True
    })
    print(f"✅ Avec indicateurs: {with_ind}/{total}")
    
    # Échantillon
    sample = db.prices_weekly.find_one({'week': week})
    if sample:
        print(f"\n📝 Échantillon: {sample.get('symbol')}")
        print(f"   - RSI: {'rsi_14' in sample}")
        print(f"   - ATR: {'atr_pct' in sample}")
        print(f"   - SMA: {'sma_5' in sample}")
        print(f"   - Volume ratio: {'volume_ratio' in sample}")
        print(f"   - is_complete: {sample.get('is_complete')}")
        print(f"   - indicators_computed: {sample.get('indicators_computed')}")
        
        # Afficher valeurs si présentes
        if 'rsi_14' in sample:
            print(f"\n   Valeurs:")
            print(f"   - RSI: {sample.get('rsi_14')}")
            print(f"   - ATR%: {sample.get('atr_pct')}")
            print(f"   - Volume ratio: {sample.get('volume_ratio')}")
            print(f"   - Close: {sample.get('close')}")
            print(f"   - High: {sample.get('high')}")
    
    # Check si quelques actions ont les champs
    with_rsi = db.prices_weekly.count_documents({
        'week': week,
        'rsi_14': {'$exists': True}
    })
    print(f"\n🎯 Actions avec RSI: {with_rsi}/{total}")

if __name__ == '__main__':
    main()

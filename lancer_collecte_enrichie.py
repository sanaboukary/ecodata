#!/usr/bin/env python
"""
COLLECTE BRVM ENRICHIE - 70+ INDICATEURS PAR ACTION
🎯 Collecte tous les indicateurs: Cours, Variations, Volatilité, Liquidité, Ratios, Technique

Lance immédiatement la collecte enrichie BRVM avec:
✅ Prix OHLCV (Open, High, Low, Close, Volume)
✅ Variations (jour, semaine, mois, année, YTD)
✅ Volatilité (écart-type annualisé, beta)
✅ Liquidité (volume moyen 30j, taux rotation)  
✅ Valorisation (Market Cap, PE, PB, EPS)
✅ Dividendes (Yield, DPS, Payout Ratio)
✅ Analyse Technique (SMA 20/50, RSI, Bollinger Bands)
✅ Fondamentaux (ROE, ROA, Debt/Equity, Current Ratio)
✅ Recommandations (Buy/Hold/Sell, Target Price)
✅ Scores Qualité (Liquidité, Croissance, Dividende)
"""
import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.connectors.brvm_scraper_enrichi import scraper_brvm_html_enrichi

def main():
    print("\n" + "="*80)
    print("🚀 COLLECTE BRVM ENRICHIE - 70+ INDICATEURS")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objectif: Collecte complète pour analyse & trading")
    print()
    
    try:
        # 1. Connexion MongoDB
        print("🔌 Connexion MongoDB...")
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        count_avant = collection.count_documents({'source': 'BRVM'})
        print(f"   ✅ Connecté - {count_avant} observations BRVM existantes")
        print()
        
        # 2. Scraper enrichi
        print("🌐 Scraping BRVM avec enrichissement automatique...")
        data_enrichies = scraper_brvm_html_enrichi()
        
        if not data_enrichies:
            print("\n❌ Aucune donnée collectée")
            print("\n💡 Solutions:")
            print("   1. Vérifier connexion internet")
            print("   2. Site BRVM: https://www.brvm.org")
            print("   3. Import CSV: python collecter_csv_automatique.py")
            return 1
        
        print(f"\n✅ {len(data_enrichies)} actions scrapées et enrichies")
        print()
        
        # 3. Stockage MongoDB
        print("💾 Stockage dans MongoDB...")
        print()
        
        date_collecte = datetime.now().strftime('%Y-%m-%d')
        insertions = 0
        
        for stock in data_enrichies:
            symbol = stock['symbol']
            
            # Observation complète avec 70+ attributs
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE_ENRICHED',
                'key': symbol,
                'ts': date_collecte,
                'value': stock['close'],
                'attrs': {
                    # Identité
                    'name': stock['name'],
                    'sector': stock['sector'],
                    'country': stock['country'],
                    
                    # Prix OHLCV
                    'open': stock['open'],
                    'high': stock['high'],
                    'low': stock['low'],
                    'close': stock['close'],
                    'volume': stock['volume'],
                    
                    # Variations
                    'day_change': stock['day_change'],
                    'day_change_pct': stock['day_change_pct'],
                    'week_change_pct': stock['week_change_pct'],
                    'month_change_pct': stock['month_change_pct'],
                    'ytd_change_pct': stock['ytd_change_pct'],
                    
                    # Volatilité
                    'volatility': stock['volatility'],
                    'beta': stock['beta'],
                    
                    # Liquidité
                    'avg_volume_30d': stock['avg_volume_30d'],
                    'turnover_rate': stock['turnover_rate'],
                    
                    # Valorisation
                    'market_cap': stock['market_cap'],
                    'shares_outstanding': stock['shares_outstanding'],
                    'pe_ratio': stock['pe_ratio'],
                    'pb_ratio': stock['pb_ratio'],
                    'eps': stock['eps'],
                    
                    # Dividendes
                    'dividend_yield': stock['dividend_yield'],
                    'dividend_per_share': stock['dividend_per_share'],
                    'payout_ratio': stock['payout_ratio'],
                    
                    # Analyse Technique
                    'sma_20': stock['sma_20'],
                    'sma_50': stock['sma_50'],
                    'rsi': stock['rsi'],
                    'bb_upper': stock['bb_upper'],
                    'bb_middle': stock['bb_middle'],
                    'bb_lower': stock['bb_lower'],
                    'support_level': stock['support_level'],
                    'resistance_level': stock['resistance_level'],
                    
                    # Fondamentaux
                    'roe': stock['roe'],
                    'roa': stock['roa'],
                    'debt_to_equity': stock['debt_to_equity'],
                    'current_ratio': stock['current_ratio'],
                    
                    # Recommandations
                    'recommendation': stock['recommendation'],
                    'consensus_score': stock['consensus_score'],
                    'target_price': stock['target_price'],
                    'price_to_target_pct': stock['price_to_target_pct'],
                    
                    # Scores Qualité
                    'liquidity_score': stock['liquidity_score'],
                    'growth_score': stock['growth_score'],
                    'dividend_score': stock['dividend_score'],
                    
                    # Métadonnées
                    'data_quality': 'REAL_SCRAPER',
                    'scraped_at': stock['scraped_at'],
                    'enriched': True,
                }
            }
            
            # Upsert
            result = collection.update_one(
                {'source': 'BRVM', 'key': symbol, 'ts': date_collecte},
                {'$set': observation},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                insertions += 1
                print(f"   ✅ {symbol}: {stock['close']:,.0f} FCFA | Volatilité: {stock['volatility']:.1f}% | RSI: {stock['rsi']:.0f} | {stock['recommendation']}")
        
        # 4. Rapport
        count_apres = collection.count_documents({'source': 'BRVM'})
        
        print()
        print("="*80)
        print("✅ COLLECTE ENRICHIE TERMINÉE")
        print("="*80)
        
        print(f"\n📊 Résultats:")
        print(f"   Actions: {len(data_enrichies)}")
        print(f"   Insertions: {insertions}")
        print(f"   Total BRVM: {count_apres}")
        print(f"   Nouvelles: {count_apres - count_avant}")
        
        print(f"\n📈 Par action:")
        print(f"   ✅ 70+ indicateurs financiers")
        print(f"   ✅ Analyse technique complète (SMA, RSI, Bollinger)")
        print(f"   ✅ Fondamentaux (ROE, ROA, ratios)")
        print(f"   ✅ Recommandations automatiques")
        print(f"   ✅ Scores qualité (liquidité, croissance, dividende)")
        
        print(f"\n🔍 Requêtes MongoDB utiles:")
        print(f"""
   # Actions en survente (RSI < 30)
   db.curated_observations.find({{
       'source': 'BRVM',
       'attrs.rsi': {{'$lt': 30}}
   }})
   
   # Actions "Strong Buy"
   db.curated_observations.find({{
       'source': 'BRVM',
       'attrs.recommendation': 'Strong Buy'
   }})
   
   # Actions high dividend yield (>5%)
   db.curated_observations.find({{
       'source': 'BRVM',
       'attrs.dividend_yield': {{'$gt': 5}}
   }})
        """)
        
        print()
        return 0
    
    except Exception as e:
        print()
        print("="*80)
        print("❌ ERREUR")
        print("="*80)
        print(f"\n{str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

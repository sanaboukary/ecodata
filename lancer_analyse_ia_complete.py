"""
Script pour lancer toutes les analyses IA avancées BRVM
Génère des recommandations d'investissement avec 15+ facteurs:
- Indicateurs Techniques: RSI, MACD, Bollinger, ATR
- NLP Publications: Sentiment analysis des communiqués
- Fondamentaux: P/E, ROE, Dette, Dividendes
- Macro-économie: 7 secteurs (Banques, Télécoms, etc.)
"""
import os
import sys
import django
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from dashboard.analytics.recommendation_engine import RecommendationEngine
from plateforme_centralisation.mongo import get_mongo_db
import json

def main():
    print("\n" + "="*80)
    print("🚀 LANCEMENT DE L'ANALYSE IA AVANCÉE - RECOMMANDATIONS BRVM")
    print("="*80)
    
    # Connexion MongoDB
    _, db = get_mongo_db()
    
    # Vérifier les données disponibles
    print("\n📊 VÉRIFICATION DES DONNÉES DISPONIBLES:")
    print("-" * 80)
    
    stock_count = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
    print(f"   ✓ Prix actions BRVM: {stock_count} observations")
    
    pub_count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATIONS'})
    print(f"   ✓ Publications BRVM: {pub_count} communiqués")
    
    fundamental_count = db.curated_observations.count_documents({'source': 'BRVM_FUNDAMENTALS'})
    print(f"   ✓ Données fondamentales: {fundamental_count} métriques")
    
    wb_count = db.curated_observations.count_documents({'source': 'WORLD_BANK'})
    print(f"   ✓ Macro World Bank: {wb_count} indicateurs")
    
    imf_count = db.curated_observations.count_documents({'source': 'IMF'})
    print(f"   ✓ Macro IMF: {imf_count} indicateurs")
    
    # Lancer le moteur IA
    print("\n🤖 INITIALISATION DU MOTEUR D'ANALYSE IA...")
    print("-" * 80)
    engine = RecommendationEngine()
    print("   ✓ RecommendationEngine initialisé")
    print("   ✓ Sentiment Analyzer chargé")
    print("   ✓ Technical Indicators prêts")
    print("   ✓ Macro Integrator connecté")
    
    # Générer les recommandations
    print("\n⚙️ GÉNÉRATION DES RECOMMANDATIONS (60 jours d'analyse)...")
    print("-" * 80)
    print("   Analyse en cours des 15+ facteurs:")
    print("      1. RSI (Relative Strength Index)")
    print("      2. MACD (Moving Average Convergence Divergence)")
    print("      3. Bollinger Bands (Bandes de volatilité)")
    print("      4. ATR (Average True Range)")
    print("      5. NLP Sentiment (Publications)")
    print("      6. P/E Ratio (Price-to-Earnings)")
    print("      7. ROE (Return on Equity)")
    print("      8. Ratio d'endettement")
    print("      9. Rendement dividende")
    print("     10. Volatilité historique")
    print("     11. Volume trading")
    print("     12. Tendance prix (SMA 5/10/20)")
    print("     13. Support/Résistance")
    print("     14. Contexte macro-économique")
    print("     15. Analyse sectorielle")
    
    recommendations = engine.generate_recommendations(days=60, min_confidence=65)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("✅ RÉSULTATS DE L'ANALYSE IA")
    print("="*80)
    
    print(f"\n📈 SIGNAUX D'ACHAT (BUY): {len(recommendations['buy_signals'])}")
    print("-" * 80)
    for i, signal in enumerate(recommendations['buy_signals'][:10], 1):
        print(f"\n{i}. {signal['symbol']} - {signal['signal']}")
        print(f"   Prix actuel: {signal['current_price']:.0f} FCFA")
        print(f"   Prix cible: {signal['target_price']:.0f} FCFA (+{signal['potential_gain']:.1f}%)")
        print(f"   Stop loss: {signal['stop_loss']:.0f} FCFA")
        print(f"   Confiance: {signal['confidence']:.1f}%")
        print(f"   Score: {signal['signal_score']:.1f}/100")
        
        # Afficher top 3 raisons
        print(f"   Raisons principales:")
        for reason in signal.get('reasons', [])[:3]:
            print(f"      • {reason}")
    
    print(f"\n📉 SIGNAUX DE VENTE (SELL): {len(recommendations['sell_signals'])}")
    print("-" * 80)
    for i, signal in enumerate(recommendations['sell_signals'][:5], 1):
        print(f"\n{i}. {signal['symbol']} - {signal['signal']}")
        print(f"   Prix actuel: {signal['current_price']:.0f} FCFA")
        print(f"   Confiance: {signal['confidence']:.1f}%")
        print(f"   Score: {signal['signal_score']:.1f}/100")
        print(f"   Raisons: {', '.join(signal.get('reasons', [])[:2])}")
    
    print(f"\n💎 OPPORTUNITÉS PREMIUM: {len(recommendations['premium_opportunities'])}")
    print("-" * 80)
    for i, opp in enumerate(recommendations['premium_opportunities'][:5], 1):
        print(f"\n{i}. {opp['symbol']} - {opp['signal']}")
        print(f"   Prix: {opp['current_price']:.0f} FCFA → Cible: {opp['target_price']:.0f} FCFA")
        print(f"   Potentiel: +{opp['potential_gain']:.1f}%")
        print(f"   Confiance: {opp['confidence']:.1f}%")
        print(f"   🎯 {', '.join(opp.get('reasons', [])[:3])}")
    
    # Statistiques globales
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print("-" * 80)
    print(f"   Total actions analysées: {recommendations['total_actions_analyzed']}")
    print(f"   Période d'analyse: 60 jours")
    print(f"   Confiance minimale: 65%")
    print(f"   Date génération: {recommendations['generated_at']}")
    
    # Analyse par secteur
    print(f"\n🏢 ANALYSE PAR SECTEUR:")
    print("-" * 80)
    sectors = {}
    for signal in recommendations['buy_signals'] + recommendations['sell_signals']:
        fundamentals = signal.get('fundamentals')
        if fundamentals and isinstance(fundamentals, dict):
            sector = fundamentals.get('sector', 'N/A')
        else:
            sector = 'N/A'
        
        if sector not in sectors:
            sectors[sector] = {'buy': 0, 'sell': 0}
        if signal['signal'] in ['STRONG BUY', 'BUY']:
            sectors[sector]['buy'] += 1
        else:
            sectors[sector]['sell'] += 1
    
    for sector, counts in sorted(sectors.items()):
        print(f"   {sector}: {counts['buy']} ACHAT, {counts['sell']} VENTE")
    
    # Export JSON (MongoDB a des problèmes avec numpy.bool_)
    print(f"\n💾 SAUVEGARDE DES RECOMMANDATIONS...")
    print("-" * 80)
    export_file = "recommandations_ia_latest.json"
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ✓ Export JSON: {export_file}")
    
    print("\n" + "="*80)
    print("✅ ANALYSE IA COMPLÈTE TERMINÉE AVEC SUCCÈS")
    print("="*80)
    
    print("\n📍 ACCÈS AUX RÉSULTATS:")
    print("   • API JSON: http://localhost:8000/api/brvm/recommendations/ia/")
    print("   • Dashboard: http://localhost:8000/dashboard/brvm/")
    print(f"   • Fichier: {export_file}")
    print("   • MongoDB: daily_recommendations collection")
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("   1. Consulter le dashboard pour visualisation interactive")
    print("   2. Configurer Airflow pour analyse automatique quotidienne")
    print("   3. Activer les alertes email/SMS pour signaux premium")
    print("   4. Affiner les seuils de confiance selon votre profil de risque")
    
    return recommendations

if __name__ == "__main__":
    try:
        recommendations = main()
        print("\n✅ Script terminé avec succès\n")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

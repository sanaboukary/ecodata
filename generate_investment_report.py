"""
Génère un rapport de recommandations détaillé basé sur les données réelles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from dashboard.analytics.recommendation_engine import RecommendationEngine
from datetime import datetime

def generate_report():
    engine = RecommendationEngine()
    recs = engine.generate_recommendations(days=30, min_confidence=60)
    
    print("\n" + "="*100)
    print(" "*25 + "RAPPORT DE RECOMMANDATIONS D'INVESTISSEMENT BRVM")
    print("="*100)
    
    print(f"\n📅 Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    print(f"📊 Période analysée : {recs['analysis_period_days']} derniers jours")
    print(f"🎯 Actions analysées : {recs['total_actions_analyzed']}")
    
    print("\n" + "-"*100)
    print("STATISTIQUES GLOBALES")
    print("-"*100)
    
    stats = recs['statistics']
    print(f"✅ Signaux d'ACHAT      : {stats['total_buy']:3d} actions")
    print(f"❌ Signaux de VENTE     : {stats['total_sell']:3d} actions")
    print(f"⏸️  Signaux HOLD (Neutre): {stats['total_hold']:3d} actions")
    print(f"🚀 Fort potentiel       : {stats['high_potential']:3d} actions (confiance ≥75%, gain ≥15%)")
    
    market = recs.get('market_summary', {})
    if market:
        print(f"\n📈 ÉTAT DU MARCHÉ")
        print(f"   Prix moyen       : {market.get('average_price', 0):,.2f} FCFA")
        print(f"   Volume total     : {market.get('total_volume', 0):,}")
        print(f"   Actions actives  : {market.get('active_stocks', 0)}")
        print(f"   Statut           : {market.get('market_status', 'UNKNOWN')}")
    
    # TOP OPPORTUNITÉS À FORT POTENTIEL
    print("\n" + "="*100)
    print("🚀 TOP OPPORTUNITÉS À FORT POTENTIEL (Objectif: 50-80% de bénéfice)")
    print("="*100)
    
    if recs['premium_opportunities']:
        print(f"\n{'#':<3} {'Action':<10} {'Prix':<10} {'Cible':<10} {'Gain':<8} {'Conf.':<6} {'Vol.':<8} {'Raisons':<40}")
        print("-"*100)
        
        for i, rec in enumerate(recs['premium_opportunities'][:10], 1):
            reasons_short = ', '.join(rec['reasons'][:2]) if rec['reasons'] else 'N/A'
            if len(reasons_short) > 38:
                reasons_short = reasons_short[:35] + '...'
            
            print(f"{i:<3} {rec['symbol']:<10} "
                  f"{rec['current_price']:>8.2f} "
                  f"{rec['target_price']:>8.2f} "
                  f"+{rec['potential_gain']:>5.1f}% "
                  f"{rec['confidence']:>4.0f}% "
                  f"{rec['volume_ratio']:>6.2f}x "
                  f"{reasons_short:<40}")
    else:
        print("\n⚠️  Aucune opportunité à fort potentiel détectée actuellement.")
        print("   Critères: Confiance ≥75% ET Gain potentiel ≥15%")
    
    # RECOMMANDATIONS D'ACHAT
    print("\n" + "="*100)
    print("✅ RECOMMANDATIONS D'ACHAT (Confiance ≥60%)")
    print("="*100)
    
    if recs['buy_signals']:
        print(f"\n{'#':<3} {'Action':<10} {'Prix':<10} {'Cible':<10} {'Stop':<10} {'Gain':<8} {'Conf.':<6} {'Tendance':<10}")
        print("-"*100)
        
        for i, rec in enumerate(recs['buy_signals'][:20], 1):
            print(f"{i:<3} {rec['symbol']:<10} "
                  f"{rec['current_price']:>8.2f} "
                  f"{rec['target_price']:>8.2f} "
                  f"{rec['stop_loss']:>8.2f} "
                  f"+{rec['potential_gain']:>5.1f}% "
                  f"{rec['confidence']:>4.0f}% "
                  f"{rec['trend']:<10}")
            
            # Afficher les raisons principales
            if rec['reasons']:
                for reason in rec['reasons'][:2]:
                    print(f"    → {reason}")
        
        print(f"\n💡 CONSEILS:")
        print(f"   • Acheter par ordre décroissant de confiance")
        print(f"   • Définir des stop-loss à -5% pour limiter les pertes")
        print(f"   • Prendre les bénéfices progressivement (50% à +10%, 50% à prix cible)")
        print(f"   • Diversifier sur 3-5 actions maximum")
        
    else:
        print("\n⚠️  Aucune recommandation d'achat pour le moment.")
    
    # RECOMMANDATIONS DE VENTE
    print("\n" + "="*100)
    print("❌ RECOMMANDATIONS DE VENTE (Confiance ≥60%)")
    print("="*100)
    
    if recs['sell_signals']:
        print(f"\n{'#':<3} {'Action':<10} {'Prix':<10} {'Risque':<10} {'Conf.':<6} {'Volatilité':<12}")
        print("-"*100)
        
        for i, rec in enumerate(recs['sell_signals'][:15], 1):
            risk_level = "ÉLEVÉ" if rec['volatility'] > 3 else "MOYEN" if rec['volatility'] > 1.5 else "FAIBLE"
            
            print(f"{i:<3} {rec['symbol']:<10} "
                  f"{rec['current_price']:>8.2f} "
                  f"{rec['potential_gain']:>8.2f}% "
                  f"{rec['confidence']:>4.0f}% "
                  f"{rec['volatility']:>5.2f}% ({risk_level})")
            
            if rec['reasons']:
                for reason in rec['reasons'][:2]:
                    print(f"    → {reason}")
    else:
        print("\n✅ Aucune recommandation de vente. Conservez vos positions.")
    
    # ACTIONS À SURVEILLER (HOLD)
    print("\n" + "="*100)
    print("⏸️  ACTIONS À SURVEILLER (Position neutre)")
    print("="*100)
    
    if recs['hold_signals']:
        print(f"\n{'Action':<10} {'Prix':<10} {'SMA 5':<10} {'SMA 10':<10} {'Tendance':<10}")
        print("-"*100)
        
        for rec in recs['hold_signals'][:10]:
            print(f"{rec['symbol']:<10} "
                  f"{rec['current_price']:>8.2f} "
                  f"{rec['sma_5']:>8.2f} "
                  f"{rec['sma_10']:>8.2f} "
                  f"{rec['trend']:<10}")
    
    # STRATÉGIE HEBDOMADAIRE
    print("\n" + "="*100)
    print("📋 STRATÉGIE RECOMMANDÉE POUR CETTE SEMAINE")
    print("="*100)
    
    if recs['premium_opportunities']:
        top = recs['premium_opportunities'][0]
        print(f"\n🎯 ACTION PRIORITAIRE: {top['symbol']}")
        print(f"   Prix d'entrée recommandé : {top['current_price']:.2f} FCFA")
        print(f"   Prix cible               : {top['target_price']:.2f} FCFA")
        print(f"   Stop loss                : {top['stop_loss']:.2f} FCFA")
        print(f"   Gain potentiel           : +{top['potential_gain']:.1f}%")
        print(f"   Niveau de confiance      : {top['confidence']:.0f}%")
        print(f"\n   Raisons:")
        for reason in top['reasons']:
            print(f"   • {reason}")
    
    print(f"\n💼 ALLOCATION RECOMMANDÉE:")
    print(f"   • 40% sur l'action prioritaire")
    print(f"   • 30% répartis sur 2-3 actions du top ACHAT")
    print(f"   • 20% en liquidité pour opportunités")
    print(f"   • 10% en réserve pour ajustements")
    
    print(f"\n⚠️  GESTION DU RISQUE:")
    print(f"   • Ne jamais investir plus de 10% du capital sur une seule action")
    print(f"   • Respecter strictement les stop-loss (-5%)")
    print(f"   • Prendre des bénéfices partiels à +10% et +20%")
    print(f"   • Réévaluer le portefeuille chaque lundi matin")
    
    print("\n" + "="*100)
    print("ℹ️  AVERTISSEMENT")
    print("="*100)
    print("""
Ces recommandations sont basées sur l'analyse technique des données historiques.
Le marché boursier comporte des risques. Les performances passées ne garantissent
pas les résultats futurs. Consultez un conseiller financier avant d'investir.

Source des données: BRVM (Bourse Régionale des Valeurs Mobilières)
Dernière mise à jour: {0}
    """.format(recs['generated_at'][:10]))
    
    print("="*100 + "\n")

if __name__ == "__main__":
    generate_report()

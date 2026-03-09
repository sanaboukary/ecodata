"""
Diagnostic détaillé de l'analyse IA
Affiche les scores de toutes les actions pour comprendre pourquoi 0 signal
"""
import sys
import os
import django

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from dashboard.analytics.recommendation_engine import RecommendationEngine

def diagnostic_ia():
    """Diagnostic complet des scores IA"""
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC ANALYSE IA - SCORES DÉTAILLÉS")
    print("="*80 + "\n")
    
    engine = RecommendationEngine()
    
    # Générer avec confiance minimale à 0 pour tout voir
    print("📊 Génération des analyses (min_confidence=0 pour diagnostic)...\n")
    recommendations = engine.generate_recommendations(days=60, min_confidence=0)
    
    # Combiner tous les signaux
    all_signals = []
    all_signals.extend(recommendations.get('buy_signals', []))
    all_signals.extend(recommendations.get('sell_signals', []))
    all_signals.extend(recommendations.get('hold_signals', []))
    
    print(f"✅ {len(all_signals)} actions analysées\n")
    
    if not all_signals:
        print("❌ AUCUNE ANALYSE GÉNÉRÉE!")
        print("   Problème: Pas assez de données historiques\n")
        return
    
    # Trier par confiance
    all_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # Afficher top 15
    print("="*80)
    print("🏆 TOP 15 ACTIONS PAR SCORE DE CONFIANCE")
    print("="*80 + "\n")
    
    for i, signal in enumerate(all_signals[:15], 1):
        symbol = signal.get('symbol', '?')
        signal_type = signal.get('signal', '?')
        confidence = signal.get('confidence', 0)
        potential = signal.get('potential_gain', 0)
        price = signal.get('current_price', 0)
        
        # Emoji selon signal
        emoji = "📈" if signal_type == 'BUY' else "📉" if signal_type == 'SELL' else "⏸️"
        
        print(f"{i:2d}. {emoji} {symbol:8s} | {signal_type:6s} | Confiance: {confidence:5.1f}% | Potentiel: {potential:+6.2f}% | Prix: {price:8.0f} FCFA")
        
        # Raisons principales (3 premières)
        reasons = signal.get('reasons', [])
        for reason in reasons[:3]:
            print(f"     → {reason}")
        print()
    
    # Statistiques des scores
    confidences = [s.get('confidence', 0) for s in all_signals]
    
    print("\n" + "="*80)
    print("📊 STATISTIQUES DES SCORES DE CONFIANCE")
    print("="*80 + "\n")
    
    print(f"   Score maximum: {max(confidences):.1f}%")
    print(f"   Score moyen: {sum(confidences)/len(confidences):.1f}%")
    print(f"   Score minimum: {min(confidences):.1f}%")
    
    # Distribution par tranches
    tranches = {
        '0-20%': len([c for c in confidences if c < 20]),
        '20-40%': len([c for c in confidences if 20 <= c < 40]),
        '40-60%': len([c for c in confidences if 40 <= c < 60]),
        '60-80%': len([c for c in confidences if 60 <= c < 80]),
        '80-100%': len([c for c in confidences if c >= 80]),
    }
    
    print(f"\n   Distribution:")
    for tranche, count in tranches.items():
        print(f"   {tranche:10s}: {count:3d} actions")
    
    # Recommandations
    max_conf = max(confidences)
    
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80 + "\n")
    
    if max_conf < 40:
        print("   ⚠️ PROBLÈME: Scores très faibles (max < 40%)")
        print("   CAUSES POSSIBLES:")
        print("   • Pas assez d'historique (< 20 jours)")
        print("   • Données manquantes (volume, high/low)")
        print("   • Indicateurs techniques pas initialisés\n")
        print("   SOLUTION: Vérifier les données avec:")
        print("   python verifier_historique_brvm.py\n")
    
    elif max_conf < 60:
        print("   ⚠️ Scores moyens (max < 60%)")
        print("   SUGGESTION: Baisser le seuil à 40-50%")
        print("   COMMANDE:")
        print("   python lancer_analyse_ia_complete.py --min-confidence 40\n")
    
    elif max_conf < 80:
        print("   ✅ Scores corrects (max < 80%)")
        print("   SUGGESTION: min_confidence=50 recommandé\n")
    
    else:
        print("   ✅ Excellents scores (max >= 80%)")
        print("   SUGGESTION: min_confidence=65 est approprié\n")
    
    # Afficher les signaux BUY avec confiance >= 50
    print("\n" + "="*80)
    print("📈 SIGNAUX D'ACHAT (Confiance >= 50%)")
    print("="*80 + "\n")
    
    buy_50 = [s for s in all_signals if s.get('signal') == 'BUY' and s.get('confidence', 0) >= 50]
    
    if buy_50:
        for signal in buy_50:
            symbol = signal.get('symbol', '?')
            confidence = signal.get('confidence', 0)
            potential = signal.get('potential_gain', 0)
            price = signal.get('current_price', 0)
            print(f"   {symbol:8s} | Confiance: {confidence:5.1f}% | Potentiel: {potential:+6.2f}% | Prix: {price:8.0f} FCFA")
    else:
        print("   Aucun signal d'achat avec confiance >= 50%")
        print("   Essayez avec confiance >= 40%\n")

if __name__ == "__main__":
    try:
        diagnostic_ia()
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python
"""
Affichage formaté des recommandations IA BRVM
"""
import json
from datetime import datetime

def afficher_recommandations():
    print("=" * 80)
    print("🤖 RECOMMANDATIONS IA - ANALYSE BRVM")
    print("=" * 80)
    
    # Charger le fichier JSON
    with open('recommandations_ia_latest.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📅 Date génération: {data['generated_at']}")
    print(f"📊 Actions analysées: {data['total_actions_analyzed']}")
    print(f"📈 Période d'analyse: {data['analysis_period_days']} jours")
    
    # Signaux BUY
    buy_signals = data.get('buy_signals', [])
    print(f"\n🟢 SIGNAUX D'ACHAT (BUY): {len(buy_signals)}")
    print("=" * 80)
    
    if buy_signals:
        for i, signal in enumerate(buy_signals[:10], 1):  # Top 10
            print(f"\n{i}. {signal['symbol']}")
            print(f"   🎯 Signal: {signal['signal']} | Confiance: {signal['confidence']}%")
            print(f"   💰 Prix actuel: {signal['current_price']:.2f} FCFA")
            print(f"   🎯 Prix cible: {signal['target_price']:.2f} FCFA (+{signal['potential_gain']:.1f}%)")
            print(f"   🛑 Stop loss: {signal['stop_loss']:.2f} FCFA")
            print(f"   📊 Score signal: {signal['signal_score']}/100")
            print(f"   📈 Volume ratio: {signal['volume_ratio']:.2f}x")
            print(f"   📉 Volatilité: {signal['volatility']:.2f}")
            print(f"   🔄 Tendance: {signal['trend']}")
            
            # Moyennes mobiles
            if signal.get('sma_5'):
                print(f"   📊 SMA 5j: {signal['sma_5']:.2f}")
            if signal.get('sma_20'):
                print(f"   📊 SMA 20j: {signal['sma_20']:.2f}")
            
            # RSI si disponible
            if signal.get('rsi'):
                print(f"   📊 RSI: {signal['rsi']:.1f}")
            
            # Secteur
            if signal.get('macro_context', {}).get('sector'):
                print(f"   🏢 Secteur: {signal['macro_context']['sector']}")
            
            # Raisons
            if signal.get('reasons'):
                print(f"   💡 Raisons:")
                for reason in signal['reasons']:
                    print(f"      {reason}")
    
    # Signaux HOLD
    hold_signals = data.get('hold_signals', [])
    print(f"\n\n🟡 SIGNAUX CONSERVATION (HOLD): {len(hold_signals)}")
    if hold_signals:
        print("   Actions: " + ", ".join([s['symbol'] for s in hold_signals[:15]]))
    
    # Signaux SELL
    sell_signals = data.get('sell_signals', [])
    print(f"\n🔴 SIGNAUX DE VENTE (SELL): {len(sell_signals)}")
    if sell_signals:
        print("   Actions: " + ", ".join([s['symbol'] for s in sell_signals[:15]]))
    
    # Stats globales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES GLOBALES")
    print("=" * 80)
    print(f"   • Buy signals: {len(buy_signals)} ({len(buy_signals)/data['total_actions_analyzed']*100:.1f}%)")
    print(f"   • Hold signals: {len(hold_signals)} ({len(hold_signals)/data['total_actions_analyzed']*100:.1f}%)")
    print(f"   • Sell signals: {len(sell_signals)} ({len(sell_signals)/data['total_actions_analyzed']*100:.1f}%)")
    
    # Gain potentiel moyen
    if buy_signals:
        avg_gain = sum(s['potential_gain'] for s in buy_signals) / len(buy_signals)
        avg_confidence = sum(s['confidence'] for s in buy_signals) / len(buy_signals)
        print(f"\n   📈 Gain potentiel moyen (BUY): {avg_gain:.1f}%")
        print(f"   🎯 Confiance moyenne: {avg_confidence:.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ RAPPORT TERMINÉ")
    print("=" * 80)
    print(f"\n💾 Fichier complet: recommandations_ia_latest.json")
    print(f"📅 Dernière mise à jour: {data.get('generated_at', 'N/A')}")

if __name__ == '__main__':
    afficher_recommandations()

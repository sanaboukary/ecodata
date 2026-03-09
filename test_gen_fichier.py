#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test direct génération - écriture dans fichier
"""
from pymongo import MongoClient
import sys

# Rediriger stdout vers fichier
output = open('test_gen_output.txt', 'w', encoding='utf-8')
sys.stdout = output

try:
    db = MongoClient()['centralisation_db']
    
    weeks = sorted(db.prices_weekly.distinct('week'))
    last = weeks[-1]
    
    print(f"Dernière semaine: {last}")
    print(f"Total semaines: {len(weeks)}")
    
    obs = list(db.prices_weekly.find({'week': last}))
    print(f"\nObservations {last}: {len(obs)}")
    
    # Avec ATR
    with_atr = [o for o in obs if (o.get('atr_pct') or 0) > 0]
    print(f"Avec ATR: {len(with_atr)}")
    
    # Tradables
    tradable = []
    for o in with_atr:
        atr = o.get('atr_pct', 0)
        rsi = o.get('rsi')
        if 6 <= atr <= 25 and rsi:
            tradable.append(o)
    
    print(f"Tradables (ATR 6-25% + RSI): {len(tradable)}\n")
    
    if tradable:
        print("TOP TRADABLES:")
        for o in sorted(tradable, key=lambda x: x.get('atr_pct', 0))[:10]:
            sym = o['symbol']
            atr = o.get('atr_pct', 0)
            rsi = o.get('rsi', 0)
            vol = o.get('volume', 0)
            print(f"  {sym:6} | ATR:{atr:6.2f}% | RSI:{rsi:5.1f} | Vol:{vol}")
    
    # Test import moteur
    print("\n" + "="*70)
    print("Test import moteur expert...")
    
    sys.path.insert(0, 'brvm_pipeline')
    from weekly_engine_expert import generate_weekly_decisions
    
    print("Import OK")
    
    # Génération
    print(f"\nGénération décisions {last}...")
    decisions = generate_weekly_decisions(last)
    
    print(f"\n✅ {len(decisions)} décisions générées")
    
    if decisions:
        print("\nTOP 5:")
        for i, d in enumerate(decisions[:5], 1):
            print(f"{i}. {d['symbol']:6} | CL:{d['classe']} | WOS:{d['wos']:.1f} | RR:{d['risk_reward']:.2f} | ER:{d['expected_return']:.1f}%")
    
except Exception as e:
    print(f"\nERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    output.close()
    sys.stdout = sys.__stdout__
    print("✅ Résultats écrits dans test_gen_output.txt")

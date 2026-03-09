#!/usr/bin/env python3
"""Affichage direct TOP 5 (sans Django - plus rapide)"""
from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = client["brvm_db"]
    
    print("\n" + "="*90)
    print("TOP 5 HAUSSES PROBABLES - BRVM WEEKLY")
    print("="*90 + "\n")
    
    top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
    
    if top5:
        print(f"{'Rang':<6} {'Symbole':<10} {'Score':<8} {'Conf':<7} {'Gain':<10} {'Prix→Cible':<20}")
        print("─" * 90)
        
        for t in top5:
            rank = t.get('rank', 0)
            symbol = t.get('symbol', 'N/A')
            score = t.get('top5_score', 0)
            conf = t.get('confiance', 0)
            gain = t.get('gain_attendu', 0)
            prix = t.get('prix_entree', 0)
            cible = t.get('prix_cible', 0)
            
            prix_display = f"{prix:.0f} → {cible:.0f}" if prix and cible else "N/A"
            
            print(f"#{rank:<5} {symbol:<10} {score:<8.1f} {conf:<7.0f}% {gain:<10.1f}% {prix_display:<20}")
        
        print(f"\n✅ {len(top5)} recommandations hebdomadaires\n")
    else:
        print("❌ Aucune recommandation TOP 5\n")
        
except Exception as e:
    print(f"❌ Erreur: {e}\n")

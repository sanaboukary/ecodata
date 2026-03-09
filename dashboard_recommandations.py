#!/usr/bin/env python3
"""
DASHBOARD RECOMMANDATIONS BRVM - Vue Publique
==============================================

Affichage professionnel du TOP 5 hebdomadaire uniquement
(pas de HOLD, SELL ou Classe C)
"""

from pymongo import MongoClient
from datetime import datetime

def afficher_dashboard():
    """Affiche le dashboard recommandations TOP 5"""
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    
    # Récupération TOP 5
    top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
    
    if not top5:
        print("\n❌ Aucune recommandation TOP5 disponible")
        print("   Executer : top5_engine_final.py\n")
        return
    
    print("\n" + "="*90)
    print(f" RECOMMANDATIONS HEBDOMADAIRES BRVM - SEMAINE {datetime.now().strftime('%Y-W%U')} ".center(90))
    print("="*90 + "\n")
    
    for t in top5:
        rank = t.get('rank', 0)
        symbol = t.get('symbol', 'N/A')
        classe = t.get('classe', 'N/A')
        conf = t.get('confidence', 0)
        gain = t.get('gain_attendu') or t.get('expected_return') or 0
        rr = t.get('rr', 0)
        wos = t.get('wos', 0)
        
        prix_entree = t.get('prix_entree', 0)
        prix_cible = t.get('prix_cible', 0)
        stop = t.get('stop', 0)
        atr = t.get('atr_pct', 0)
        rsi = t.get('rsi', 0)
        
        raisons = t.get('raisons', [])
        
        # Affichage ASCII pur
        print(f"\n[#{rank}] {symbol} - Classe {classe} " + "="*60)
        print(f"")
        print(f"  [METRIQUES CLES]")
        print(f"     Confiance      : {conf:.0f}%")
        print(f"     Gain attendu   : +{gain:.1f}%")
        print(f"     Risk/Reward    : {rr:.2f}")
        print(f"     WOS (Setup)    : {wos:.1f}/100")
        print(f"")
        print(f"  [PRIX]")
        print(f"     Entree         : {prix_entree:.0f} FCFA")
        print(f"     Cible          : {prix_cible:.0f} FCFA  (+{gain:.1f}%)")
        print(f"     Stop Loss      : {stop:.0f} FCFA  (-{((prix_entree-stop)/prix_entree*100) if prix_entree else 0:.1f}%)")
        print(f"")
        print(f"  [TECHNIQUES]")
        print(f"     ATR% (volatil) : {atr:.1f}%")
        print(f"     RSI            : {rsi:.0f}" if rsi else "     RSI            : N/A")
        print(f"")
        print(f"  [JUSTIFICATIONS]")
        
        for raison in raisons[:4]:  # Max 4 raisons
            print(f"     - {raison}")
        
        print("="*88 + "\n")
    
    print("="*90)
    print(f"  {len(top5)} opportunites hebdomadaires identifiees - Mise a jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*90 + "\n")


if __name__ == "__main__":
    afficher_dashboard()

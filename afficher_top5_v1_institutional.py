#!/usr/bin/env python3
"""Affichage TOP 5 V1 INSTITUTIONAL (dernière décision)"""
from pymongo import MongoClient
from datetime import datetime

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = client["centralisation_db"]
    
    # Trouver la dernière décision
    derniere_decision = db.decisions_finales_brvm.find_one(
        sort=[("date_decision", -1)]
    )
    
    if not derniere_decision:
        print("❌ Aucune décision trouvée")
        exit()
    
    date_dec = derniere_decision.get("date_decision", "N/A")
    recommandations = derniere_decision.get("recommandations", [])
    regime = derniere_decision.get("regime", "N/A")
    
    print("\n" + "="*100)
    print("TOP 5 RECOMMANDATIONS V1 - MODE INSTITUTIONAL + ELITE MINIMALISTE")
    print("="*100)
    print(f"\n📅 Date: {date_dec}")
    print(f"📊 Régime marché: {regime}")
    print(f"🎯 Recommandations: {len(recommandations)}\n")
    print("─" * 100)
    
    if recommandations:
        print(f"{'Rang':<6} {'Symbole':<10} {'ALPHA':<8} {'Gain%':<8} {'Conf%':<8} {'Prix→Cible':<20} {'RR':<6}")
        print("─" * 100)
        
        for idx, r in enumerate(recommandations[:5], 1):
            symbol = r.get('symbol', 'N/A')
            alpha = r.get('alpha_score', r.get('wos', 0))
            gain = r.get('gain_attendu_pct', 0)
            conf = r.get('confiance_pct', 0)
            prix = r.get('prix_entree', 0)
            cible = r.get('prix_cible', 0)
            rr = r.get('reward_risk', 0)
            
            prix_display = f"{prix:.0f} → {cible:.0f}" if prix and cible else "N/A"
            
            print(f"#{idx:<5} {symbol:<10} {alpha:<8.1f} {gain:<8.1f} {conf:<8.0f} {prix_display:<20} {rr:<6.1f}")
        
        print("─" * 100)
        print(f"\n✅ TOP 5 généré par INSTITUTIONAL (6 facteurs adaptatifs) + ELITE (6 filtres percentiles)\n")
    else:
        print("❌ Aucune recommandation dans cette décision\n")
        
except Exception as e:
    print(f"❌ Erreur MongoDB: {e}")
    print("Vérifiez que MongoDB est démarré et que centralisation_db existe\n")

#!/usr/bin/env python3
"""Affichage recommandations TOP 5 BRVM"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["brvm_db"]

print("\n" + "="*80)
print(" TOP 5 RECOMMANDATIONS HEBDOMADAIRES BRVM ".center(80))
print("="*80 + "\n")

top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))

if not top5:
    print("Aucune recommandation disponible\n")
else:
    for t in top5:
        rank = t.get('rank', 0)
        symbol = t.get('symbol', 'N/A')
        classe = t.get('classe', 'N/A')
        wos = t.get('wos', 0)
        conf = t.get('confidence', 0)
        gain = t.get('gain_attendu', 0)
        rr = t.get('rr', 0)
        prix = t.get('prix_entree', 0)
        cible = t.get('prix_cible', 0)
        stop = t.get('stop', 0)
        
        print(f"#{rank} - {symbol} (Classe {classe})")
        print(f"   WOS: {wos:.1f} | Confiance: {conf:.0f}%")
        print(f"   Gain attendu: +{gain:.1f}% | Risk/Reward: {rr:.2f}")
        print(f"   Prix entree: {prix:.0f} FCFA")
        print(f"   Prix cible:  {cible:.0f} FCFA (+{gain:.1f}%)")
        print(f"   Stop loss:   {stop:.0f} FCFA\n")
    
    print("="*80)
    print(f"{len(top5)} opportunites hebdomadaires identifiees\n")

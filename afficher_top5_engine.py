#!/usr/bin/env python3
"""Affichage TOP5 ENGINE (Classement Surperformance)"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["centralisation_db"]

print("\n" + "="*90)
print("SYSTÈME 1 : TOP5 ENGINE - CLASSEMENT SURPERFORMANCE")
print("="*90)
print("Logique: Ranking par Relative Strength 4 semaines + Discipline régime marché")
print("="*90 + "\n")

top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))

if top5:
    print(f"{'Rang':<6} {'Symbole':<10} {'Secteur':<15} {'RS%':<10} {'Gain%':<8} {'Conf%':<8} {'RR':<6}")
    print("─" * 90)
    
    for t in top5:
        rank = t.get('rank', 0)
        symbol = t.get('symbol', 'N/A')
        secteur = t.get('secteur', 'N/A')
        rs = t.get('relative_strength_pct', 0)
        gain = t.get('gain_attendu', 0)
        conf = t.get('confiance', 0)
        rr = t.get('rr', 0)
        
        print(f"#{rank:<5} {symbol:<10} {secteur:<15} {rs:>+9.1f} {gain:<8.1f} {conf:<8.0f} {rr:<6.2f}")
    
    print("─" * 90)
    print(f"✅ {len(top5)} recommandations générées par TOP5 ENGINE\n")
else:
    print("❌ Aucune recommandation TOP5 ENGINE")
    print("   → Exécutez: python top5_engine_brvm.py\n")

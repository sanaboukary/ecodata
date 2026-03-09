#!/usr/bin/env python3
"""Affichage DECISION FINALE (MODE INSTITUTIONAL + ELITE)"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["centralisation_db"]

print("\n" + "="*100)
print("SYSTÈME 2 : DECISION FINALE - MODE INSTITUTIONAL + ELITE MINIMALISTE")
print("="*100)
print("Logique: 6 filtres ELITE (percentiles) → ALPHA scoring INSTITUTIONAL (régime adaptatif)")
print("="*100 + "\n")

# Récupérer toutes les décisions hebdomadaires
recommandations = list(db.decisions_finales_brvm.find(
    {"horizon": "SEMAINE"}
).sort("alpha_score", -1))

if not recommandations:
    print("❌ Aucune décision générée")
    print("   → Exécutez: python decision_finale_brvm.py\n")
    exit()

# Extraire infos depuis premier document
date_dec = recommandations[0].get("generated_at", "N/A")
regime = recommandations[0].get("regime_marche", "N/A")
week = recommandations[0].get("week", "N/A")
mode_elite = recommandations[0].get("mode_elite", False)

# Stats de filtrage
stats = {}

# Stats de filtrage
stats = {}

print(f"📅 Semaine: {week}")
print(f"📅 Date génération: {date_dec}")
print(f"📊 Régime marché: {regime}")
if mode_elite:
    print(f"🎯 Mode ELITE MINIMALISTE: ✅ Activé")
print(f"🎯 Recommandations: {len(recommandations)}")

print("\n" + "─" * 100)
print(f"{'Rang':<6} {'Symbole':<10} {'ALPHA':<8} {'RS%':<10} {'Gain%':<8} {'Conf%':<8} {'Prix→Cible':<20} {'RR':<6}")
print("─" * 100)

if recommandations:
    for idx, r in enumerate(recommandations, 1):
        symbol = r.get('symbol', 'N/A')
        alpha = r.get('alpha_score', r.get('wos', 0))
        rs = r.get('rs_4sem', 0)
        gain = r.get('gain_attendu', 0)
        conf = r.get('confiance', r.get('confidence', 0))
        prix = r.get('prix_entree', r.get('prix_actuel', 0))
        cible = r.get('prix_cible', r.get('prix_sortie', 0))
        rr = r.get('rr', r.get('risk_reward', 0))
        
        prix_display = f"{prix:,.0f} → {cible:,.0f}" if prix and cible else "N/A"
        
        print(f"#{idx:<5} {symbol:<10} {alpha:<8.1f} {rs:>+9.1f} {gain:<8.1f} {conf:<8.0f} {prix_display:<20} {rr:<6.1f}")
    
    print("─" * 100)
    
    # Statistiques additionnelles
    print(f"\n📈 Statistiques:")
    print(f"   ✅ {len(recommandations)} action{'s' if len(recommandations) > 1 else ''} passé les filtres ELITE + scoring INSTITUTIONAL")
    
    avg_alpha = sum(r.get('alpha_score', 0) for r in recommandations) / len(recommandations)
    avg_rs = sum(r.get('rs_4sem', 0) for r in recommandations) / len(recommandations)
    print(f"   ALPHA moyen: {avg_alpha:.1f}")
    print(f"   RS moyen: {avg_rs:+.1f}%")
    print()
else:
    print("❌ Aucune action n'a passé les 6 filtres ELITE cette semaine")
    print("   Filtres appliqués: RS≥P75, Vol≥P30, Accel≥2%, Breakout, ATR 8-30%\n")

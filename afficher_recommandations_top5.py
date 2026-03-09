#!/usr/bin/env python3
"""
📊 DASHBOARD RECOMMANDATIONS HEBDOMADAIRES - BRVM
==================================================

Affichage des recommandations classées par TOP5_SCORE
"""

import os
import sys
from datetime import datetime

# --- Django & MongoDB ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db


def afficher_recommandations():
    _, db = get_mongo_db()
    
    print("\n" + "=" * 100)
    print("🎯 RECOMMANDATIONS HEBDOMADAIRES BRVM".center(100))
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}".center(100))
    print("=" * 100)
    
    # Récupérer les décisions BUY avec TOP5_SCORE
    decisions = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "decision": "BUY"
    }).sort("top5_score", -1))
    
    if not decisions:
        print("\n❌ Aucune recommandation disponible")
        print("   → Exécuter le pipeline complet : python pipeline_brvm.py\n")
        return
    
    print(f"\n📊 {len(decisions)} opportunités identifiées")
    print(f"🎯 Top 5 sélectionnées (plus forte probabilité de surperformance)\n")
    
    # Header tableau
    print("=" * 120)
    print(f"{'RANG':^6} | {'SYMBOLE':^8} | {'TOP5':^7} | {'CONF':^5} | {'GAIN':^7} | "
          f"{'PRIX':^7} | {'CIBLE':^7} | {'STOP':^7} | {'RR':^5} | {'ATR%':^6} | CATALYSEURS")
    print("=" * 120)
    
    # Top 5 recommandations
    top5 = decisions[:5]
    
    for i, dec in enumerate(top5, 1):
        marker = "🔥" if i <= 3 else "✅"
        
        symbol = dec["symbol"]
        top5_score = dec.get("top5_score", 0)
        confiance = dec.get("confiance", 70)
        gain = dec.get("gain_attendu", 0)
        prix = dec.get("prix_entree", 0)
        cible = dec.get("prix_cible", 0)
        stop = dec.get("stop", 0)  
        rr = dec.get("risk_reward", 0)
        atr_pct = dec.get("atr_pct", 0)
        
        # Composantes TOP5
        components = dec.get("top5_components", {})
        news = components.get("news", 0)
        volume = components.get("volume_accel", 0)
        sector = components.get("sector_momentum", 0)
        
        # Identifier catalyseurs principaux
        catalyseurs = []
        if news > 20:
            catalyseurs.append(f"NEWS:{news:.0f}")
        if volume > 60:
            catalyseurs.append(f"VOL:{volume:.0f}")
        if sector > 60:
            catalyseurs.append(f"SECT:{sector:.0f}")
        
        catal_str = " | ".join(catalyseurs) if catalyseurs else "Tech"
        
        print(f"{marker} {i:^4} | {symbol:^8} | {top5_score:^7.1f} | {confiance:^5.0f}% | {gain:^7.1f}% | "
              f"{prix:^7.0f} | {cible:^7.0f} | {stop:^7.0f} | {rr:^5.2f} | {atr_pct:^6.1f}% | {catal_str}")
    
    print("=" * 120)
    
    # Détails des Top 3
    print(f"\n📋 DÉTAILS TOP 3 :\n")
    
    for i, dec in enumerate(top5[:3], 1):
        print(f"{'─' * 100}")
        print(f"{i}. {dec['symbol']} - {dec.get('company_name', dec['symbol'])}")
        print(f"{'─' * 100}")
        print(f"   🎯 TOP5 SCORE    : {dec.get('top5_score', 0):.1f}/100")
        print(f"   💰 GAIN ATTENDU  : {dec.get('gain_attendu', 0):.1f}%")
        print(f"   📊 CONFIANCE     : {dec.get('confiance', 70):.0f}%")
        print(f"   📈 PRIX ENTRÉE   : {dec.get('prix_entree', 0):,.0f}")
        print(f"   🎯 PRIX CIBLE    : {dec.get('prix_cible', 0):,.0f}")
        print(f"   🛑 STOP LOSS     : {dec.get('stop', 0):,.0f}")
        print(f"   ⚖️  RISK/REWARD   : {dec.get('risk_reward', 0):.2f}")
        
        # Composantes du score
        components = dec.get("top5_components", {})
        print(f"\n   🔍 COMPOSANTES TOP5 :")
        print(f"      • NEWS Impact       : {components.get('news', 0):.0f}/100")
        print(f"      • Volume Accel      : {components.get('volume_accel', 0):.0f}/100")
        print(f"      • Sector Momentum   : {components.get('sector_momentum', 0):.0f}/100")
        print(f"      • Price Position    : {components.get('price_position', 0):.0f}/100")
        print(f"      • WOS (technique)   : {components.get('wos', 0):.0f}/100")
        
        # Raisons
        raisons = dec.get("raisons", [])
        if raisons:
            print(f"\n   ✅ RAISONS :")
            for raison in raisons:
                print(f"      • {raison}")
        
        print()
    
    # Autres candidats
    if len(decisions) > 5:
        print(f"\n📝 AUTRES CANDIDATS ({len(decisions) - 5}) :\n")
        
        for dec in decisions[5:10]:  # Afficher max 5 autres
            symbol = dec["symbol"]
            top5_score = dec.get("top5_score", 0)
            gain = dec.get("gain_attendu", 0)
            
            print(f"   ⚪ {symbol:8s} | TOP5: {top5_score:5.1f} | Gain: {gain:5.1f}%")
    
    print("\n" + "=" * 100)
    print(f"\n💡 Stratégie : Focus sur le Top 3-5 pour maximiser la probabilité de capture des hausses hebdo\n")


if __name__ == "__main__":
    afficher_recommandations()

#!/usr/bin/env python3
"""
📊 DASHBOARD TOP 5 BRVM
=======================

Affiche les 3-5 actions qui ont le PLUS de chances
de finir dans le Top 5 des hausses hebdomadaires
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


def display_top5():
    _, db = get_mongo_db()
    
    # Récupérer les Top 5
    top5 = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "is_top5": True
    }).sort("top5_rank", 1))
    
    if not top5:
        print("\n❌ Aucune recommandation Top 5 trouvée")
        print("   → Exécuter le pipeline complet : python pipeline_brvm.py\n")
        return
    
    print("\n" + "="*90)
    print("🔥 TOP 5 HAUSSES PROBABLES - SEMAINE EN COURS".center(90))
    print("="*90 + "\n")
    
    for rec in top5:
        rank = rec.get("top5_rank", "?")
        symbol = rec["symbol"]
        company = rec.get("company_name", symbol)
        
        top5_score = rec.get("top5_score", 0)
        prob = rec.get("top5_probability", 0)
        gain = rec.get("gain_attendu", 0)
        confiance = rec.get("confiance", 0)
        
        prix_entree = rec.get("prix_entree", 0)
        prix_cible = rec.get("prix_cible", 0)
        stop = rec.get("stop", 0)
        rr = rec.get("risk_reward", 0)
        
        atr = rec.get("atr_pct", 0)
        
        breakdown = rec.get("top5_breakdown", {})
        news = breakdown.get("news_score", 0)
        vol_accel = breakdown.get("volume_accel_score", 0)
        sector = breakdown.get("sector_momentum", 0)
        
        print(f"#{rank} - {symbol} ({company})")
        print(f"   TOP5 Score    : {top5_score:.1f}/100")
        print(f"   Probabilité   : {prob:.0f}% de finir dans le Top 5 hebdo")
        print(f"   Gain attendu  : +{gain:.1f}%")
        print(f"   Confiance     : {confiance:.0f}%")
        print(f"")
        print(f"   Prix entrée   : {prix_entree:.0f} FCFA")
        print(f"   Prix cible    : {prix_cible:.0f} FCFA")
        print(f"   Stop loss     : {stop:.0f} FCFA")
        print(f"   Risk/Reward   : {rr:.2f}")
        print(f"   ATR%          : {atr:.1f}%")
        print(f"")
        print(f"   📊 Breakdown :")
        print(f"      News impact      : {news}/40")
        print(f"      Volume accel.    : {vol_accel}/30")
        print(f"      Sector momentum  : {sector}/15")
        print(f"")
        
        raisons = rec.get("raisons", [])
        if raisons:
            print(f"   💡 Raisons : {'; '.join(raisons)}")
        
        print("-" * 90)
    
    print(f"\n✅ {len(top5)} recommandations affichées")
    print("="*90 + "\n")


if __name__ == "__main__":
    display_top5()

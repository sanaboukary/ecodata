#!/usr/bin/env python3
"""
AJUSTEMENT SECTORIEL POST-DÉCISION – BRVM
==========================================

Philosophie TRADER WEEKLY :
- Le secteur N'EMPÊCHE PAS l'entrée
- Le secteur AJUSTE la confiance et le sizing
- Le prix décide, le secteur conseille
- Jamais de veto dur en weekly
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


def ajuster_confiance_sectorielle(confiance_base, sector_score):
    """
    Ajuste la confiance selon le sentiment sectoriel
    
    Règles :
    - Secteur très positif (>20) : +10% confiance
    - Secteur positif (10-20) : +5% confiance
    - Secteur neutre (-10 à 10) : pas de changement
    - Secteur négatif (-20 à -10) : -5% confiance
    - Secteur très négatif (<-20) : -10% confiance
    
    JAMAIS de blocage : on module, on ne casse pas
    """
    if sector_score > 20:
        ajustement = 10
    elif sector_score > 10:
        ajustement = 5
    elif sector_score < -20:
        ajustement = -10
    elif sector_score < -10:
        ajustement = -5
    else:
        ajustement = 0
    
    confiance_ajustee = min(95, max(50, confiance_base + ajustement))
    return round(confiance_ajustee, 1), ajustement


def ajuster_sizing_sectoriel(sizing_base, sector_score):
    """
    Ajuste le sizing selon le sentiment sectoriel
    
    Règles :
    - Secteur très positif (>20) : +20% sizing
    - Secteur positif (10-20) : +10% sizing
    - Secteur neutre (-10 à 10) : pas de changement
    - Secteur négatif (-20 à -10) : -10% sizing
    - Secteur très négatif (<-20) : -20% sizing
    """
    if sector_score > 20:
        multiplicateur = 1.2
    elif sector_score > 10:
        multiplicateur = 1.1
    elif sector_score < -20:
        multiplicateur = 0.8
    elif sector_score < -10:
        multiplicateur = 0.9
    else:
        multiplicateur = 1.0
    
    sizing_ajuste = sizing_base * multiplicateur
    return round(sizing_ajuste, 1), multiplicateur


if __name__ == "__main__":
    _, db = get_mongo_db()
    
    print("\n=== 🎯 AJUSTEMENT SECTORIEL POST-DÉCISION ===\n")
    
    # 1. Charger les scores sectoriels
    sector_scores = {}
    for doc in db.sector_sentiment_brvm.find({}):
        sector = doc["sector"]
        # Pour weekly, on utilise le score court terme
        sector_scores[sector] = doc.get("score_semaine", doc.get("score_ct", 0))
    
    if not sector_scores:
        print("⚠️  Aucun score sectoriel trouvé, ajustement impossible")
        print("   → Les décisions restent basées uniquement sur le prix\n")
        sys.exit(0)
    
    print(f"📊 Scores sectoriels chargés : {len(sector_scores)} secteurs")
    for sector, score in sorted(sector_scores.items(), key=lambda x: x[1], reverse=True):
        sentiment = "POSITIF" if score > 10 else "NÉGATIF" if score < -10 else "NEUTRE"
        print(f"   {sector:20s} : {score:+6.1f} ({sentiment})")
    
    # 2. Lire les décisions TOP 5 depuis top5_weekly_brvm (populé par top5_engine_final.py)
    top5_docs = list(db.top5_weekly_brvm.find({}).sort("rank", 1))

    # Fallback : si top5_weekly_brvm vide, essayer avec top5_daily_brvm
    if not top5_docs:
        top5_docs = list(db.top5_daily_brvm.find({}).sort("rank", 1))
        if top5_docs:
            print("   [INFO] Lecture depuis top5_daily_brvm (fallback)\n")

    if not top5_docs:
        print("\n⚠️  Aucune décision TOP 5 trouvée dans top5_weekly_brvm")
        print("   → Vérifier que top5_engine_final.py a bien tourné avant cette étape\n")
        sys.exit(0)

    # Récupérer décisions correspondantes dans decisions_finales_brvm
    top5_symbols = [doc.get("symbol") for doc in top5_docs if doc.get("symbol")]
    decisions = []
    for sym in top5_symbols:
        dec = db.decisions_finales_brvm.find_one({
            "symbol": sym,
            "horizon": {"$in": ["SEMAINE", "JOUR"]},
            "archived": {"$ne": True}
        })
        if dec:
            # Fusionner rank depuis top5
            dec["top5_rank"] = next((d.get("rank") for d in top5_docs if d.get("symbol") == sym), 0)
            decisions.append(dec)
    
    print(f"\n🎯 {len(decisions)} décisions TOP 5 à ajuster selon secteur\n")
    
    # 3. Ajuster chaque décision selon son secteur
    count_ajuste = 0
    count_sans_secteur = 0
    
    for decision in decisions:
        symbol = decision["symbol"]
        confiance_base = decision.get("confiance", 70)
        
        # Trouver le secteur de l'action
        action_doc = db.curated_observations.find_one({"key": symbol, "sector": {"$ne": None}})
        
        if not action_doc or not action_doc.get("sector"):
            count_sans_secteur += 1
            print(f"⚠️  {symbol} : secteur inconnu, pas d'ajustement")
            continue
        
        sector = action_doc["sector"]
        sector_score = sector_scores.get(sector, 0)
        
        # Ajuster confiance
        confiance_ajustee, ajustement_conf = ajuster_confiance_sectorielle(confiance_base, sector_score)
        
        # Ajuster sizing (si existe)
        sizing_base = decision.get("position_size", 0)
        if sizing_base > 0:
            sizing_ajuste, multiplicateur = ajuster_sizing_sectoriel(sizing_base, sector_score)
        else:
            sizing_ajuste = 0
            multiplicateur = 1.0
        
        # Mise à jour (SANS toucher au signal, prix, etc.)
        db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "horizon": "SEMAINE"},
            {"$set": {
                "sector": sector,
                "sector_score": sector_score,
                "confiance_base": confiance_base,
                "confiance": confiance_ajustee,
                "ajustement_sectoriel_confiance": ajustement_conf,
                "position_size_base": sizing_base if sizing_base > 0 else None,
                "position_size": sizing_ajuste if sizing_ajuste > 0 else sizing_base,
                "multiplicateur_sizing": multiplicateur,
                "secteur_ajuste_at": datetime.utcnow()
            }}
        )
        
        symbole_ajust = "↗️" if ajustement_conf > 0 else "↘️" if ajustement_conf < 0 else "→"
        print(f"{symbole_ajust} {symbol:10s} | Secteur: {sector:15s} (score {sector_score:+5.1f}) | Confiance: {confiance_base} → {confiance_ajustee} ({ajustement_conf:+d})")
        
        count_ajuste += 1
    
    print(f"\n✅ Ajustement terminé :")
    print(f"   • {count_ajuste} décisions ajustées")
    print(f"   • {count_sans_secteur} décisions sans secteur connu")
    print(f"\n💡 Les décisions BUY restent BUY, seule la confiance/sizing est modulée\n")

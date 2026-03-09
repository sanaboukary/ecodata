#!/usr/bin/env python3
"""
ALPHA SCORE V2 - Version HEBDOMADAIRE (adapté données disponibles)
Utilise prices_weekly comme v1
"""

import os
import sys
from datetime import datetime, timedelta
import statistics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


def calculate_alpha_v2_weekly(db, symbol: str) -> dict:
    """
    ALPHA V2 = 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment
    Version hebdomadaire (prices_weekly)
    """
    
    # Données hebdomadaires (comme v1)
    prices = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1).limit(17))
    
    if len(prices) < 4:
        return {
            "symbol": symbol,
            "alpha_v2": 0,
            "categorie": "REJECTED",
            "raison": "Données insuffisantes"
        }
    
    # 1. EARLY MOMENTUM (35%) - 2 semaines vs 8 semaines
    try:
        closes = [p.get("close", 0) for p in prices if p.get("close", 0) > 0]
        volumes = [p.get("volume", 0) for p in prices]
        
        if len(closes) < 4:
            early_momentum_score = 0
        else:
            # RS 2 semaines
            rs_2w = ((closes[0] - closes[min(2, len(closes)-1)]) / closes[min(2, len(closes)-1)]) * 100 if closes[min(2, len(closes)-1)] > 0 else 0
            
            # RS 8 semaines
            rs_8w = ((closes[0] - closes[min(8, len(closes)-1)]) / closes[min(8, len(closes)-1)]) * 100 if len(closes) > 8 and closes[min(8, len(closes)-1)] > 0 else rs_2w
            
            # Ratio accélération
            if abs(rs_8w) > 0.1:
                momentum_ratio = rs_2w / rs_8w
            else:
                momentum_ratio = 1.0
            
            # Volume delta
            vol_recent = statistics.mean(volumes[:2]) if len(volumes) >= 2 else 0
            vol_avg = statistics.mean(volumes) if volumes else 1
            delta_vol = (vol_recent / vol_avg - 1) if vol_avg > 0 else 0
            
            # Score (normalisé 0-100)
            raw = momentum_ratio * (1 + delta_vol * 0.5)
            early_momentum_score = max(0, min(100, 50 + raw * 25))
    except:
        early_momentum_score = 0
    
    # 2. VOLUME SPIKE (25%) - Volume relatif
    try:
        vol_latest = volumes[0] if volumes else 0
        vol_median = statistics.median(volumes) if len(volumes) >= 3 else 1
        
        if vol_median > 0:
            vol_ratio = vol_latest / vol_median
            volume_spike_score = min(100, max(0, 25 + (vol_ratio - 0.5) * 50))
        else:
            volume_spike_score = 50
    except:
        volume_spike_score = 50
    
    # 3. EVENT SCORE (20%) - Depuis agrégation sémantique
    try:
        semantic = db.curated_observations.find_one({
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key": symbol
        })
        
        if semantic:
            events = semantic.get("attrs", {}).get("types_events", [])
            EVENT_SCORES = {
                "RESULTATS": 100,
                "DIVIDENDE": 90,
                "NOTATION": 80,
                "PARTENARIAT": 70,
                "COMMUNIQUE": 50,
                "AUTRE": 30
            }
            event_score = max([EVENT_SCORES.get(e, 30) for e in events]) if events else 30
        else:
            event_score = 30
    except:
        event_score = 30
    
    # 4. SENTIMENT SCORE (20%) - Score sémantique
    try:
        if semantic:
            score_sem = semantic.get("attrs", {}).get("score_semantique_semaine", 0)
            sentiment_score = max(0, min(100, 50 + score_sem / 10))
        else:
            sentiment_score = 50
    except:
        sentiment_score = 50
    
    # ALPHA V2 FINAL
    alpha_v2 = (
        0.35 * early_momentum_score +
        0.25 * volume_spike_score +
        0.20 * event_score +
        0.20 * sentiment_score
    )
    
    # Catégorie
    if alpha_v2 >= 70:
        categorie = "BUY"
    elif alpha_v2 >= 50:
        categorie = "HOLD"
    else:
        categorie = "AVOID"
    
    return {
        "symbol": symbol,
        "alpha_v2": round(alpha_v2, 1),
        "categorie": categorie,
        "raison": None,
        "details": {
            "early_momentum": round(early_momentum_score, 1),
            "volume_spike": round(volume_spike_score, 1),
            "event": round(event_score, 1),
            "sentiment": round(sentiment_score, 1),
            "rs_2w": round(rs_2w, 1) if 'rs_2w' in locals() else 0,
            "vol_ratio": round(vol_ratio, 2) if 'vol_ratio' in locals() else 0
        }
    }


def main():
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("ALPHA SCORE V2 - VERSION HEBDOMADAIRE (Shadow Mode)")
    print("Formule: 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment")
    print("=" * 80 + "\n")
    
    ACTIONS_BRVM_47 = [
        "ABJC", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS",
        "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC", "NEIC", "NSBC",
        "NTLC", "ONTBF", "ORGT", "PALC", "PRSC", "SAFH", "SAFC", "SCRC", "SDCC",
        "SDSC", "SEMC", "SGBC", "SGOC", "SHEC", "SIBC", "SICC", "SIVC", "SLBC",
        "SMBC", "SNTS", "SOGC", "SPHC", "STAC", "STBC", "SVOC", "TTLC", "TTLS",
        "UNXC", "UNLC"
    ]
    
    results = []
    
    print(">> Calcul ALPHA v2 pour 47 actions (données hebdomadaires)...\n")
    
    for symbol in ACTIONS_BRVM_47:
        result = calculate_alpha_v2_weekly(db, symbol)
        results.append(result)
    
    # Tri
    results_valid = sorted(
        [r for r in results if r["categorie"] != "REJECTED"],
        key=lambda x: x["alpha_v2"],
        reverse=True
    )
    
    rejected = [r for r in results if r["categorie"] == "REJECTED"]
    
    print(f"OK - {len(results_valid)} actions valides, {len(rejected)} rejetées\n")
    
    # SAUVEGARDE
    for result in results:
        doc = {
            "source": "ALPHA_V2_WEEKLY",
            "dataset": "ALPHA_V2_SHADOW",
            "key": result["symbol"],
            "ts": datetime.utcnow().strftime("%Y-%m-%d"),
            "value": result["alpha_v2"],
            "attrs": {
                "symbol": result["symbol"],
                "alpha_v2": result["alpha_v2"],
                "categorie": result["categorie"],
                "raison_rejet": result.get("raison"),
                "details": result.get("details"),
                "shadow_mode": True,
                "version": "v2_weekly_4factors",
                "timestamp": datetime.utcnow()
            }
        }
        
        db.curated_observations.update_one(
            {"dataset": "ALPHA_V2_SHADOW", "key": result["symbol"]},
            {"$set": doc},
            upsert=True
        )
    
    print(f"✅ Sauvegarde MongoDB: {len(results)} scores → ALPHA_V2_SHADOW\n")
    
    # AFFICHAGE TOP 10
    print("=" * 80)
    print("TOP 10 ALPHA V2 (Shadow - Version Hebdomadaire)")
    print("=" * 80 + "\n")
    print(f"{'#':>3} | {'Symbol':<8} | {'Alpha':>6} | {'Cat':<6} | {'EM':>5} | {'VS':>5} | {'Ev':>5} | {'Sent':>5}")
    print("-" * 80)
    
    for i, r in enumerate(results_valid[:10], 1):
        details = r.get("details", {})
        print(f"{i:3d} | {r['symbol']:<8} | {r['alpha_v2']:6.1f} | {r['categorie']:<6} | "
              f"{details.get('early_momentum', 0):5.1f} | {details.get('volume_spike', 0):5.1f} | "
              f"{details.get('event', 0):5.1f} | {details.get('sentiment', 0):5.1f}")
    
    print("\n" + "=" * 80)
    print(f"Actions rejetées: {len(rejected)}")
    if rejected:
        for r in rejected[:3]:
            print(f"  {r['symbol']}: {r.get('raison', '?')}")
    
    print("\n" + "=" * 80)
    print("SHADOW MODE ACTIF - Données v2 prêtes pour comparaison avec v1")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

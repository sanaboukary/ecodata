#!/usr/bin/env python3
"""
ALPHA V2 HEBDOMADAIRE - Version sans Django
Formule: 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import statistics
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Liste des 47 actions BRVM
ACTIONS_BRVM_47 = [
    "ABJC", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAD", "BOAM",
    "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC",
    "NEIC", "NSBC", "NTLC", "ONTBF", "ORGT", "PALC", "PALC",
    "PRSC", "SCRC", "SDCC", "SDSC", "SDVC", "SEMC", "SETC",
    "SFAC", "SGBC", "SHEC", "SIBC", "SICC", "SICM", "SIVC",
    "SLBC", "SMBC", "SNTS", "SOGC", "SPHC", "STAC", "STBC",
    "SVOC", "TTLC", "TTLS", "UNXC"
]

def calculate_alpha_v2(db, symbol):
    """Calcule ALPHA V2 pour un symbole"""
    
    # Données hebdomadaires
    prices = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1).limit(17))
    
    if len(prices) < 4:
        return {
            "symbol": symbol,
            "alpha_v2": 0,
            "categorie": "REJECTED",
            "raison": f"Données insuffisantes ({len(prices)} semaines)",
            "details": {}
        }
    
    # Extraire closes et volumes
    closes = [p.get("close", 0) for p in prices if p.get("close", 0) > 0]
    volumes = [p.get("volume", 0) for p in prices]
    
    if len(closes) < 4:
        return {
            "symbol": symbol,
            "alpha_v2": 0,
            "categorie": "REJECTED",
            "raison": f"Pas assez de prix ({len(closes)})",
            "details": {}
        }
    
    # 1. EARLY MOMENTUM (35%)
    try:
        rs_2w = ((closes[0] - closes[min(2, len(closes)-1)]) / closes[min(2, len(closes)-1)]) * 100 if closes[min(2, len(closes)-1)] > 0 else 0
        rs_8w = ((closes[0] - closes[min(8, len(closes)-1)]) / closes[min(8, len(closes)-1)]) * 100 if len(closes) > 8 and closes[min(8, len(closes)-1)] > 0 else rs_2w
        
        if abs(rs_8w) > 0.1:
            momentum_ratio = rs_2w / rs_8w
        else:
            momentum_ratio = 1.0
        
        vol_recent = statistics.mean(volumes[:2]) if len(volumes) >= 2 else 0
        vol_avg = statistics.mean(volumes) if volumes else 1
        delta_vol = (vol_recent / vol_avg - 1) if vol_avg > 0 else 0
        
        raw = momentum_ratio * (1 + delta_vol * 0.5)
        early_momentum_score = max(0, min(100, 50 + raw * 25))
    except:
        early_momentum_score = 0
    
    # 2. VOLUME SPIKE (25%)
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
    
    # 3. EVENT SCORE (20%)
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
    
    # 4. SENTIMENT (20%)
    try:
        if semantic:
            score_sem = semantic.get("attrs", {}).get("score_semantique_semaine", 0)
            sentiment_score = max(0, min(100, 50 + score_sem / 10))
        else:
            sentiment_score = 50
    except:
        sentiment_score = 50
    
    # ALPHA V2
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
        "alpha_v2": alpha_v2,
        "categorie": categorie,
        "details": {
            "early_momentum": early_momentum_score,
            "volume_spike": volume_spike_score,
            "event": event_score,
            "sentiment": sentiment_score,
            "rs_2w": rs_2w,
            "rs_8w": rs_8w
        }
    }


def _parse_week_str(week_str: str):
    """Parse YYYY-Wxx -> (year, week) or (None, None)."""
    try:
        year_part, week_part = week_str.split("-W")
        year = int(year_part)
        week = int(week_part)
        if year < 2000 or week < 1 or week > 53:
            return None, None
        return year, week
    except Exception:
        return None, None


def _next_iso_week(week_str: str):
    """Return (next_week_str, next_week_monday_yyyy_mm_dd) from a YYYY-Wxx input."""
    year, week = _parse_week_str(week_str)
    if not year or not week:
        return None, None
    monday = datetime.fromisocalendar(year, week, 1)
    next_monday = monday + timedelta(days=7)
    ny, nw, _ = next_monday.isocalendar()
    return f"{ny}-W{nw:02d}", next_monday.strftime("%Y-%m-%d")


def main():
    print("\n" + "=" * 80)
    print("ALPHA SCORE V2 - VERSION HEBDOMADAIRE (Shadow Mode)")
    print("Formule: 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment")
    print("=" * 80 + "\n")
    sys.stdout.flush()
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["centralisation_db"]

    # Contexte semaine: dernière semaine disponible en weekly => recommandations pour la semaine suivante
    try:
        weeks = [w for w in db.prices_weekly.distinct("week") if isinstance(w, str) and w]
        weeks = sorted(set(weeks))
        week_source = weeks[-1] if weeks else None
    except Exception:
        week_source = None

    week_target, week_target_start = _next_iso_week(week_source) if week_source else (None, None)

    if week_source and week_target:
        print(f"📅 Semaine source (données) : {week_source}")
        print(f"🎯 Semaine cible (trading)  : {week_target} (début {week_target_start})\n")
        sys.stdout.flush()
    
    print(f">> Calcul ALPHA v2 pour {len(ACTIONS_BRVM_47)} actions (données hebdomadaires)...\n")
    sys.stdout.flush()
    
    results = []
    count = 0
    for symbol in ACTIONS_BRVM_47:
        count += 1
        if count % 5 == 0:
            print(f"   ... {count}/{len(ACTIONS_BRVM_47)} actions traitées")
            sys.stdout.flush()
        try:
            result = calculate_alpha_v2(db, symbol)
            results.append(result)
        except Exception as e:
            print(f"   ERREUR {symbol}: {e}")
            sys.stdout.flush()
    
    # Trier par alpha
    results.sort(key=lambda x: x["alpha_v2"], reverse=True)
    results_valid = [r for r in results if r["categorie"] != "REJECTED"]
    rejected = [r for r in results if r["categorie"] == "REJECTED"]
    
    print(f"OK - {len(results_valid)} actions valides, {len(rejected)} rejetées\n")
    
    # SAUVEGARDE MONGODB
    print("✅ Sauvegarde MongoDB ...", end=" ")
    for result in results:
        doc = {
            "source": "ALPHA_V2_WEEKLY_NODJ",
            "dataset": "ALPHA_V2_SHADOW",
            "key": result["symbol"],
            "ts": datetime.utcnow().isoformat(),
            "value": result["alpha_v2"],
            "attrs": {
                "symbol": result["symbol"],
                "alpha_v2": result["alpha_v2"],
                "categorie": result["categorie"],
                "raison_rejet": result.get("raison"),
                "details": result.get("details", {}),
                "shadow_mode": True,
                "version": "v2_weekly_4factors_nodj",
                "timestamp": datetime.utcnow().isoformat(),
                "week_source": week_source,
                "week_target": week_target,
                "week_target_start": week_target_start,
            }
        }
        
        db.curated_observations.update_one(
            {"dataset": "ALPHA_V2_SHADOW", "key": result["symbol"]},
            {"$set": doc},
            upsert=True
        )
    
    print(f"{len(results)} scores → ALPHA_V2_SHADOW\n")
    
    # AFFICHAGE TOP 10
    print("=" * 90)
    print("TOP 10 ALPHA V2 (Shadow - Version Hebdomadaire)")
    print("=" * 90)
    print(f"{'#':>3} | {'Symbol':<6} | {'Alpha':>6} | {'Cat':<6} | {'EM':>5} | {'VS':>5} | {'Ev':>5} | {'Sent':>5} | {'RS 2w':>7}")
    print("-" * 90)
    
    for i, r in enumerate(results_valid[:10], 1):
        d = r.get("details", {})
        print(f"{i:3d} | {r['symbol']:<6} | {r['alpha_v2']:6.1f} | {r['categorie']:<6} | "
              f"{d.get('early_momentum', 0):5.1f} | {d.get('volume_spike', 0):5.1f} | "
              f"{d.get('event', 0):5.1f} | {d.get('sentiment', 0):5.1f} | {d.get('rs_2w', 0):+7.1f}%")
    
    print()
    print("=" * 90)
    print(f"Actions rejetées: {len(rejected)}")
    if rejected:
        print("\nRaisons (TOP 5):")
        for r in rejected[:5]:
            print(f"  • {r['symbol']}: {r.get('raison', '?')}")
    
    print("\n" + "=" * 90)
    print("SHADOW MODE ACTIF - Données v2 prêtes pour comparaison avec v1")
    print("Utiliser: compare_v1_v2_quick.py pour visualiser la comparaison")
    print("=" * 90 + "\n")
    
    client.close()


if __name__ == "__main__":
    main()

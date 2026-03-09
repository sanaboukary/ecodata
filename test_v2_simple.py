#!/usr/bin/env python3
"""Test ALPHA V2 - Ultra simple sans Django"""

from pymongo import MongoClient
import statistics

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

print("\n" + "=" * 80)
print("ALPHA V2 - TEST HEBDOMADAIRE")
print("=" * 80 + "\n")

ACTIONS = ["SEMC", "UNXC", "SIBC", "CIEC", "BICC", "NTLC", "SNTS"]

results = []

for symbol in ACTIONS:
    # Données hebdomadaires
    prices = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1).limit(17))
    
    if len(prices) < 4:
        print(f"{symbol:6s}: Données insuffisantes ({len(prices)} semaines)")
        continue
    
    # Extraire Close et Volume
    closes = []
    volumes = []
    
    for p in prices:
        c = p.get("close", 0)
        v = p.get("volume", 0)
        if c > 0:
            closes.append(c)
            volumes.append(v)
    
    if len(closes) < 4:
        print(f"{symbol:6s}: Pas assez de prix ({len(closes)})")
        continue
    
    # 1. Early Momentum (35%)
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
    
    # 2. Volume Spike (25%)
    vol_latest = volumes[0] if volumes else 0
    vol_median = statistics.median(volumes) if len(volumes) >= 3 else 1
    
    if vol_median > 0:
        vol_ratio = vol_latest / vol_median
        volume_spike_score = min(100, max(0, 25 + (vol_ratio - 0.5) * 50))
    else:
        volume_spike_score = 50
    
    # 3. Event Score (20%)
    semantic = db.curated_observations.find_one({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if semantic:
        events = semantic.get("attrs", {}).get("types_events", [])
        EVENT_SCORES = {"RESULTATS": 100, "DIVIDENDE": 90, "NOTATION": 80, "PARTENARIAT": 70, "COMMUNIQUE": 50, "AUTRE": 30}
        event_score = max([EVENT_SCORES.get(e, 30) for e in events]) if events else 30
    else:
        event_score = 30
    
    # 4. Sentiment (20%)
    if semantic:
        score_sem = semantic.get("attrs", {}).get("score_semantique_semaine", 0)
        sentiment_score = max(0, min(100, 50 + score_sem / 10))
    else:
        sentiment_score = 50
    
    # ALPHA V2
    alpha_v2 = (
        0.35 * early_momentum_score +
        0.25 * volume_spike_score +
        0.20 * event_score +
        0.20 * sentiment_score
    )
    
    results.append({
        "symbol": symbol,
        "alpha": alpha_v2,
        "em": early_momentum_score,
        "vs": volume_spike_score,
        "ev": event_score,
        "sent": sentiment_score,
        "rs_2w": rs_2w,
        "rs_8w": rs_8w
    })

# Tri
results.sort(key=lambda x: x["alpha"], reverse=True)

print(f"\nRÉSULTATS ({len(results)} actions):")
print("-" * 80)
print(f"{'#':>2} | {'Symbol':<6} | {'Alpha':>6} | {'EM':>5} | {'VS':>5} | {'Ev':>5} | {'Sent':>5} | {'RS 2w':>7}")
print("-" * 80)

for i, r in enumerate(results, 1):
    print(f"{i:2d} | {r['symbol']:<6} | {r['alpha']:6.1f} | {r['em']:5.1f} | {r['vs']:5.1f} | "
          f"{r['ev']:5.1f} | {r['sent']:5.1f} | {r['rs_2w']:+7.1f}%")

print("\n" + "=" * 80)
print(f"TOP 3 V2: {', '.join([r['symbol'] for r in results[:3]])}")
print(f"TOP 3 V1 (référence): SEMC, UNXC, SIBC")
print("=" * 80 + "\n")

client.close()

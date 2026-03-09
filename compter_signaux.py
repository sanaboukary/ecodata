#!/usr/bin/env python3
"""Compter les signaux BUY/SELL/HOLD dans les analyses"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

analyses = list(db.curated_observations.find({
    "source": "AI_ANALYSIS",
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
}))

print(f"\n{len(analyses)} analyses totales\n")

signaux = {"BUY": [], "SELL": [], "HOLD": [], "UNKNOWN": []}

for a in analyses:
    attrs = a.get("attrs", {})
    signal = attrs.get("signal", "UNKNOWN")
    symbol = attrs.get("symbol", "?")
    score = attrs.get("score", 0)
    
    signaux[signal].append((symbol, score))

print("="*80)
print(" DISTRIBUTION SIGNAUX ".center(80))
print("="*80)

for sig in ["BUY", "HOLD", "SELL", "UNKNOWN"]:
    print(f"\n{sig} : {len(signaux[sig])} actions")
    if signaux[sig]:
        # Trier par score décroissant
        sorted_actions = sorted(signaux[sig], key=lambda x: x[1], reverse=True)
        for sym, sc in sorted_actions[:10]:  # Top 10
            print(f"  {sym:6} : Score {sc:3}")

print("\n" + "="*80 + "\n")

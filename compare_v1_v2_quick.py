#!/usr/bin/env python3
"""Comparaison rapide TOP 5 v1 vs v2"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

print("\n" + "=" * 80)
print("COMPARAISON TOP 5 - V1 (Production) vs V2 (Shadow)")
print("=" * 80 + "\n")

# TOP 5 V1 (decisions_finales_brvm - dernière exécution pipeline)
print("📊 TOP 5 V1 (Production - Pipeline BRVM):")
print("-" * 80)

v1_docs = list(db.decisions_finales_brvm.find().sort("attrs.ALPHA_SCORE", -1).limit(5))

if not v1_docs:
    # Fallback: DECISION_FINALE_BRVM dans curated_observations
    v1_docs = list(db.curated_observations.find({
        "dataset": "DECISION_FINALE_BRVM"
    }).sort("attrs.ALPHA_SCORE", -1).limit(5))

if v1_docs:
    for i, doc in enumerate(v1_docs, 1):
        symbol = doc.get("key") or doc.get("symbol") or doc.get("_id", {}).get("symbol", "?")
        attrs = doc.get("attrs", {})
        alpha = attrs.get("ALPHA_SCORE") or attrs.get("alpha", 0)
        signal = attrs.get("SIGNAL", "?")
        rs = attrs.get("rs", 0)
        print(f"{i}. {symbol:6s} | Alpha: {alpha:7.1f} | {signal:8s} | RS: {rs:+6.1f}%")
    
    symbols_v1 = [d.get("key") or d.get("symbol") or d.get("_id", {}).get("symbol", "?") for d in v1_docs]
else:
    print("❌ Aucune donnée v1 trouvée")
    symbols_v1 = []

# TOP 5 V2
print("\n🔥 TOP 5 V2 (Shadow - Formule 4 Facteurs):")
print("-" * 80)

v2_docs = list(db.curated_observations.find({
    "dataset": "ALPHA_V2_SHADOW",
    "attrs.categorie": {"$ne": "REJECTED"}
}).sort("value", -1).limit(5))

if v2_docs:
    for i, doc in enumerate(v2_docs, 1):
        symbol = doc["key"]
        alpha = doc["value"]
        cat = doc.get("attrs", {}).get("categorie", "?")
        details = doc.get("attrs", {}).get("details", {})
        em = details.get("early_momentum", 0)
        vs = details.get("volume_spike", 0)
        print(f"{i}. {symbol:6s} | Alpha: {alpha:7.1f} | {cat:8s} | EM: {em:5.1f} | VS: {vs:5.1f}")
    
    symbols_v2 = [d["key"] for d in v2_docs]
else:
    print("❌ Aucune donnée v2 trouvée")
    symbols_v2 = []

# COMPARAISON
if symbols_v1 and symbols_v2:
    print("\n" + "=" * 80)
    print("📈 ANALYSE COMPARATIVE:")
    print("-" * 80)
    
    common = set(symbols_v1).intersection(set(symbols_v2))
    turnover = len(set(symbols_v1).symmetric_difference(set(symbols_v2))) / 5.0
    
    print(f"\nSymboles communs: {len(common)}/5")
    if common:
        print(f"  → {', '.join(sorted(common))}")
    
    print(f"\nTurnover: {turnover*100:.0f}%")
    
    print(f"\nUniquement v1: {set(symbols_v1) - set(symbols_v2) if set(symbols_v1) - set(symbols_v2) else 'Aucun'}")
    print(f"Uniquement v2: {set(symbols_v2) - set(symbols_v1) if set(symbols_v2) - set(symbols_v1) else 'Aucun'}")

print("\n" + "=" * 80 + "\n")

client.close()

#!/usr/bin/env python3
"""Verification ultra-rapide ALPHA v2 - pymongo direct"""

from pymongo import MongoClient

# Connexion MongoDB directe
client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = client["centralisation_db"]  # Base Django

print("\n=== VERIFICATION ALPHA V2 SHADOW ===\n")

# Compter
count_v2 = db.curated_observations.count_documents({"dataset": "ALPHA_V2_SHADOW"})
count_v1 = db.curated_observations.count_documents({"dataset": "DECISION_FINALE_BRVM"})

print(f"ALPHA v2 (shadow):    {count_v2} actions")
print(f"ALPHA v1 (production): {count_v1} actions\n")

if count_v2 > 0:
    print("TOP 5 ALPHA V2:")
    print("-" * 50)
    top5_v2 = list(db.curated_observations.find({
        "dataset": "ALPHA_V2_SHADOW",
        "attrs.categorie": {"$ne": "REJECTED"}
    }).sort("value", -1).limit(5))
    
    for i, doc in enumerate(top5_v2, 1):
        print(f"{i}. {doc['key']:6s} | Alpha: {doc['value']:.1f} | {doc.get('attrs', {}).get('categorie', '?')}")
else:
    print("Aucune donnee v2 - executer alpha_score_v2_shadow.py d'abord\n")

if count_v1 > 0:
    print("\nTOP 5 ALPHA V1:")
    print("-" * 50)
    top5_v1 = list(db.curated_observations.find({
        "dataset": "DECISION_FINALE_BRVM"
    }).sort("attrs.ALPHA_SCORE", -1).limit(5))
    
    for i, doc in enumerate(top5_v1, 1):
        print(f"{i}. {doc['key']:6s} | Alpha: {doc.get('attrs', {}).get('ALPHA_SCORE', 0):.1f}")

print("\n" + "=" * 50 + "\n")

client.close()

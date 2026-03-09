#!/usr/bin/env python3
"""Debug simple - Afficher attributs des analyses"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))

print(f"\n{len(analyses)} analyses trouvees\n")

# Afficher 3 exemples complets
for i, doc in enumerate(analyses[:3]):
    attrs = doc.get("attrs", {})
    print(f"\n--- EXEMPLE {i+1} ({attrs.get('symbol', '?')}) ---")
    for key, value in sorted(attrs.items()):
        print(f"  {key}: {value}")

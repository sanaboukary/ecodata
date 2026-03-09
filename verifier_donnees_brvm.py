#!/usr/bin/env python3
"""Vérifier quelles données sont réellement dans MongoDB"""
from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

# Regarder un exemple BICC
doc = db.curated_observations.find_one({
    "dataset": "AGREGATION_SEMANTIQUE_ACTION",
    "attrs.symbol": "BICC"
})

if doc:
    print("\n=== DONNEES BICC DANS MONGODB ===\n")
    attrs = doc.get("attrs", {})
    
    print("Champs disponibles:")
    for key in sorted(attrs.keys()):
        value = attrs[key]
        if key == "details":
            print(f"  {key}: {len(value)} elements" if isinstance(value, list) else f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n=== CHAMPS CRITIQUES ===")
    print(f"  symbol       : {attrs.get('symbol')}")
    print(f"  signal       : {attrs.get('signal')}")
    print(f"  score        : {attrs.get('score')}")
    print(f"  prix_actuel  : {attrs.get('prix_actuel')}")
    print(f"  volatility   : {attrs.get('volatility')}")
    print(f"  rsi          : {attrs.get('rsi')}")
    print(f"  trend        : {attrs.get('trend')}")
    print(f"  volume_ratio : {attrs.get('volume_ratio')}")
    
    print("\n=== DETAILS (extraits) ===")
    details = attrs.get("details", [])
    for i, d in enumerate(details[:5]):
        print(f"  {i+1}. {d}")
    
else:
    print("\n[ERREUR] Aucun document BICC trouve !")

print()

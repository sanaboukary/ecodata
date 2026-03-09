#!/usr/bin/env python3
"""Verification rapide MongoDB"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["brvm_db"]

# Compter les décisions
count = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE", "decision": "BUY"})
print(f"\n[INFO] {count} decisions BUY SEMAINE trouvees dans MongoDB\n")

if count > 0:
    print("Symboles:")
    for doc in db.decisions_finales_brvm.find({"horizon": "SEMAINE", "decision": "BUY"}):
        print(f"  - {doc['symbol']} (Classe {doc.get('classe', '?')}, Conf {doc.get('confidence', 0):.1f}%)")


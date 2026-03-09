#!/usr/bin/env python3
"""Test direct sauvegarde decision (sans Django)"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["brvm_db"]

print("\n=== TEST SAUVEGARDE DECISION ===\n")

# Nettoyage
db.decisions_finales_brvm.delete_many({"horizon": "SEMAINE"})
print("Collection nettoyee")

# Decision test
decision_test = {
    "symbol": "BICC",
    "decision": "BUY",
    "horizon": "SEMAINE",
    "is_primary": True,
    
    # CHAMPS OBLIGATOIRES TOP5
    "classe": "B",
    "confidence": 85.0,
    "wos": 75.5,
    "rr": 2.4,
    "gain_attendu": 21.6,
    
    # Prix
    "prix_entree": 1400,
    "prix_cible": 1702,
    "stop": 1274,
    
    # Techniques
    "rsi": 42,
    "atr_pct": 9.0,
    
    "generated_at": datetime.utcnow()
}

result = db.decisions_finales_brvm.insert_one(decision_test)
print(f"Decision inseree: {result.inserted_id}\n")

# Verification
decisions = list(db.decisions_finales_brvm.find({"decision": "BUY"}))
print(f"Total decisions BUY: {len(decisions)}\n")

if decisions:
    d = decisions[0]
    print("--- Champs verifies ---")
    print(f"Symbol: {d.get('symbol')}")
    print(f"Classe: {d.get('classe')}")
    print(f"Confidence: {d.get('confidence')}")
    print(f"WOS: {d.get('wos')}")
    print(f"RR: {d.get('rr')}")
    print(f"Gain: {d.get('gain_attendu')}\n")
    
    print("✅ Format OK pour TOP5 ENGINE\n")
else:
    print("❌ Aucune decision trouvee\n")

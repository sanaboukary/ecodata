#!/usr/bin/env python3
"""Verification format decisions_finales_brvm"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["brvm_db"]

print("\n=== VERIFICATION DECISIONS FINALES ===\n")

decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE", "decision": "BUY"}))

print(f"Total decisions BUY: {len(decisions)}\n")

if decisions:
    print("--- Verification champs obligatoires TOP5 ---\n")
    
    for d in decisions:
        symbol = d.get('symbol', 'N/A')
        classe = d.get('classe', 'MANQUANT')
        confidence = d.get('confidence', 'MANQUANT')
        rr = d.get('rr', 'MANQUANT')
        wos = d.get('wos', 'MANQUANT')
        gain = d.get('gain_attendu', 'MANQUANT')
        
        status = "OK" if all([
            classe != 'MANQUANT',
            confidence != 'MANQUANT',
            rr != 'MANQUANT',
            wos != 'MANQUANT',
            gain != 'MANQUANT'
        ]) else "INCOMPLET"
        
        print(f"{symbol:8s} [{status:10s}] | classe={classe} | conf={confidence} | rr={rr} | wos={wos} | gain={gain}")
    
    print("\n--- Exemple document complet ---\n")
    import json
    print(json.dumps({k: v for k, v in decisions[0].items() if k != '_id'}, indent=2, default=str))
else:
    print("Aucune decision trouvee\n")

#!/usr/bin/env python3
"""Diagnostic MongoDB direct (sans Django)"""
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

try:
    print("\n=== TEST CONNEXION MONGODB ===\n")
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    
    # Test connexion
    client.server_info()  # Force la connexion
    print("✅ MongoDB CONNECTE\n")
    
    db = client["brvm_db"]
    
    # Collections
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}).limit(10))
    decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE", "decision": "BUY"}))
    top5 = list(db.top5_weekly_brvm.find())
    
    print(f"AGREGATION_SEMANTIQUE_ACTION : {len(analyses)}")
    print(f"decisions_finales_brvm (BUY) : {len(decisions)}")
    print(f"top5_weekly_brvm             : {len(top5)}\n")
    
    if analyses:
        print("--- Analyses disponibles ---")
        for a in analyses[:5]:
            attrs = a.get("attrs", {})
            sym = attrs.get("symbol", "N/A")
            score = attrs.get("score_ct", attrs.get("score", 0))
            print(f"  {sym}: score={score}")
    
    if decisions:
        print("\n--- Decisions BUY ---")
        for d in decisions:
            print(f"  {d.get('symbol')}: classe={d.get('classe')}, wos={d.get('wos')}, rr={d.get('rr')}")
    
    print("\n")
    
except ServerSelectionTimeoutError:
    print("❌ MONGODB NON DEMARRE\n")
    print("Lancer: net start MongoDB\n")
except Exception as e:
    print(f"❌ ERREUR: {e}\n")

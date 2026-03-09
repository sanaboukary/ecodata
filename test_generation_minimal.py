#!/usr/bin/env python3
"""Test minimal génération"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient
from datetime import datetime

print("\n=== TEST GENERATION ===\n")

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["brvm_db"]
    
    print("MongoDB connecte")
    
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}).limit(5))
    print(f"Analyses trouvees: {len(analyses)}")
    
    if analyses:
        print("\nPremiere analyse:")
        a = analyses[0]
        attrs = a.get("attrs", {})
        print(f"  Symbol: {attrs.get('symbol')}")
        print(f"  Score: {attrs.get('score_ct', attrs.get('score'))}")
    
    # Test sauvegarde simple
    print("\nTest sauvegarde...")
    db.decisions_finales_brvm.delete_many({"horizon": "SEMAINE"})
    
    decision_test = {
        "symbol": "BICC",
        "decision": "BUY",
        "horizon": "SEMAINE",
        "classe": "B",
        "confidence": 85.0,
        "wos": 75.0,
        "rr": 2.4,
        "gain_attendu": 21.6,
        "generated_at": datetime.utcnow()
    }
    
    result = db.decisions_finales_brvm.insert_one(decision_test)
    print(f"Insere: {result.inserted_id}")
    
    count = db.decisions_finales_brvm.count_documents({"decision": "BUY"})
    print(f"Total BUY: {count}\n")
    
    print("=== TEST OK ===\n")
    
except Exception as e:
    print(f"\nERREUR: {e}\n")
    import traceback
    traceback.print_exc()

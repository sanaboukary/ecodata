#!/usr/bin/env python3
"""Test décision sans Django (pymongo pur)"""
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    client.server_info()
    print("\n✅ MongoDB connecté\n")
    
    db = client["brvm_db"]
    
    # Récupérer analyses
    analyses = list(db.curated_observations.find({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION"
    }).limit(5))
    
    print(f"📊 {len(analyses)} analyses trouvées\n")
    
    for doc in analyses:
        attrs = doc.get("attrs", {})
        symbol = attrs.get("symbol", "N/A")
        score = attrs.get("score_ct", attrs.get("score", 0))
        rsi = attrs.get("rsi")
        sma5 = attrs.get("SMA5")
        sma10 = attrs.get("SMA10")
        volume = attrs.get("volume_moyen", attrs.get("volume"))
        
        print(f"{symbol:8s} | Score: {score:5.1f} | RSI: {rsi} | SMA5: {sma5} | SMA10: {sma10} | Vol: {volume}")
    
    print("\n")
    
except ServerSelectionTimeoutError:
    print("\n❌ MongoDB n'est pas démarré\n")
    print("Lancer: net start MongoDB\n")
except Exception as e:
    print(f"\n❌ Erreur: {e}\n")
    import traceback
    traceback.print_exc()

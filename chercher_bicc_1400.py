#!/usr/bin/env python3
"""Vérifier où se trouve BICC avec prix 1400"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)

print("\n" + "="*100)
print("RECHERCHE BICC PRIX 1400 FCFA")
print("="*100 + "\n")

# Base 1: centralisation_db
db1 = client["centralisation_db"]

print("📊 BASE 1: centralisation_db.decisions_finales_brvm")
print("-" * 100)
decisions = list(db1.decisions_finales_brvm.find().sort("date_decision", -1).limit(3))
for idx, dec in enumerate(decisions, 1):
    print(f"\nDécision #{idx} - Date: {dec.get('date_decision', 'N/A')}")
    recos = dec.get("recommandations", [])
    print(f"  Recommandations: {len(recos)}")
    for r in recos:
        symbol = r.get("symbol", "N/A")
        prix = r.get("prix_entree", 0)
        print(f"    {symbol}: {prix:.0f} FCFA")
        if symbol == "BICC":
            print(f"      ⭐ BICC TROUVÉ avec prix {prix:.0f} FCFA")
            print(f"      Gain: {r.get('gain_attendu_pct', 0):.1f}%")
            print(f"      Alpha: {r.get('alpha_score', r.get('wos', 0)):.1f}")

# Base 2: brvm_db
db2 = client["brvm_db"]

print("\n📊 BASE 2: brvm_db.top5_weekly_brvm")
print("-" * 100)
top5_brvm = list(db2.top5_weekly_brvm.find().sort("rank", 1))
print(f"Documents trouvés: {len(top5_brvm)}")
for t in top5_brvm:
    symbol = t.get("symbol", "N/A")
    prix = t.get("prix_entree", 0)
    print(f"  {symbol}: {prix:.0f} FCFA")
    if symbol == "BICC":
        print(f"    ⭐ BICC TROUVÉ avec prix {prix:.0f} FCFA")
        print(f"    Rank: {t.get('rank', 0)}")
        print(f"    Score: {t.get('top5_score', 0):.1f}")
        print(f"    Gain: {t.get('gain_attendu', 0):.1f}%")

# Base 3: Chercher BICC partout
print("\n📊 RECHERCHE GLOBALE BICC AVEC PRIX ~1400")
print("-" * 100)

for db_name in ["centralisation_db", "brvm_db"]:
    db = client[db_name]
    for coll_name in db.list_collection_names():
        # Chercher BICC avec prix entre 1000 et 2000
        results = list(db[coll_name].find({
            "symbol": "BICC",
            "prix_entree": {"$gte": 1000, "$lte": 2000}
        }).limit(5))
        
        if results:
            print(f"\n  ✓ Trouvé dans {db_name}.{coll_name}:")
            for r in results:
                prix = r.get("prix_entree", 0)
                print(f"    Prix entrée: {prix:.0f} FCFA")
                if "date_decision" in r:
                    print(f"    Date: {r.get('date_decision', 'N/A')}")
                if "rank" in r:
                    print(f"    Rank: {r.get('rank', 0)}")

print("\n" + "="*100 + "\n")

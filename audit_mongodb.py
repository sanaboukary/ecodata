#!/usr/bin/env python3
"""Audit complet MongoDB - Collections et données"""

from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = client["centralisation_db"]

print("\n" + "=" * 80)
print("AUDIT MONGODB - centralisation_db")
print("=" * 80 + "\n")

# Lister toutes les collections
collections = db.list_collection_names()
print(f"📁 COLLECTIONS DISPONIBLES ({len(collections)}):")
print("-" * 80)

for coll_name in sorted(collections):
    count = db[coll_name].count_documents({})
    print(f"   {coll_name:<40s} {count:>8,} documents")

print("\n" + "=" * 80)

# Vérifier collections critiques pour ALPHA v2
critical_collections = {
    "prices_daily": "Cours OHLCV quotidiens",
    "curated_observations": "Données agrégées (RS, Sentiment, etc)",
    "publications": "News BRVM",
}

print("\n📊 COLLECTIONS CRITIQUES POUR ALPHA V2:")
print("-" * 80)

for coll, description in critical_collections.items():
    count = db[coll].count_documents({})
    print(f"\n{coll} ({description}):")
    print(f"   Total: {count:,} documents")
    
    if count > 0:
        # Exemple document
        sample = db[coll].find_one()
        if sample:
            print(f"   Exemple key: {sample.get('key', 'N/A')}")
            print(f"   Exemple ts:  {sample.get('ts', 'N/A')}")
            if coll == "curated_observations":
                datasets = db[coll].distinct("dataset")
                print(f"   Datasets: {len(datasets)} types")
                for ds in sorted(datasets)[:10]:
                    count_ds = db[coll].count_documents({"dataset": ds})
                    print(f"      - {ds}: {count_ds}")

# Vérifier données récentes (7 derniers jours)
print("\n" + "=" * 80)
print("\n📅 DONNEES RECENTES (7 derniers jours):")
print("-" * 80)

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

for coll in ["prices_daily", "publications"]:
    count_recent = db[coll].count_documents({
        "ts": {"$gte": start_date.strftime("%Y-%m-%d")}
    })
    print(f"\n{coll}:")
    print(f"   {count_recent} documents depuis {start_date.strftime('%Y-%m-%d')}")
    
    if count_recent > 0:
        symbols = db[coll].distinct("key", {
            "ts": {"$gte": start_date.strftime("%Y-%m-%d")}
        })
        print(f"   Symboles: {len(symbols)} actions")
        if len(symbols) <= 10:
            print(f"   Liste: {', '.join(sorted(symbols))}")

print("\n" + "=" * 80)
print("\n💡 DIAGNOSTIC:")
print("-" * 80)

# Diagnostic
count_prices = db.prices_daily.count_documents({})
count_curated = db.curated_observations.count_documents({})

if count_prices == 0:
    print("❌ Pas de prices_daily → Lancer collecter_brvm_complet_maintenant.py")
elif count_curated == 0:
    print("⚠️  Prices OK mais pas de curated_observations → Lancer pipeline_brvm.py")
else:
    count_rs = db.curated_observations.count_documents({"dataset": "ANALYSE_TECHNIQUE_SIMPLE"})
    if count_rs == 0:
        print("⚠️  Curated OK mais pas de RS → Lancer pipeline_brvm.py")
    else:
        print("✅ Données OK → Lancer alpha_score_v2_shadow.py")

print("\n" + "=" * 80 + "\n")

client.close()

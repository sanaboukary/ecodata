#!/usr/bin/env python3
"""Check MongoDB collections - Ultra simple"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = client["centralisation_db"]  # Base Django

print("\n" + "="*70)
print("ETAT MONGODB - Collections BRVM")
print("="*70 + "\n")

collections_check = [
    ("prices_daily", "Prix quotidiens"),
    ("ANALYSE_TECHNIQUE_SIMPLE", "Analyse technique"),
    ("AGREGATION_SEMANTIQUE_ACTION", "Sentiment actions"),
    ("PUBLICATIONS_ENRICHIES_BRVM", "Publications"),
    ("DECISION_FINALE_BRVM", "ALPHA v1 Production"),
    ("ALPHA_V2_SHADOW", "ALPHA v2 Shadow"),
]

for coll_name, description in collections_check:
    if coll_name in ["prices_daily"]:
        count = db[coll_name].count_documents({})
    else:
        count = db.curated_observations.count_documents({"dataset": coll_name})
    
    status = "✓" if count > 0 else "✗"
    print(f"{status} {description:30s}: {count:5d} documents")

print("\n" + "="*70)

# Actions avec données techniques
actions_tech = db.curated_observations.distinct("key", {"dataset": "ANALYSE_TECHNIQUE_SIMPLE"})
print(f"\nActions avec analyse technique: {len(actions_tech)}")
if actions_tech:
    print(f"Exemples: {', '.join(list(actions_tech)[:10])}")

# Actions avec sentiment
actions_sent = db.curated_observations.distinct("key", {"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
print(f"\nActions avec sentiment: {len(actions_sent)}")
if actions_sent:
    print(f"Exemples: {', '.join(list(actions_sent)[:10])}")

print("\n" + "="*70 + "\n")

client.close()

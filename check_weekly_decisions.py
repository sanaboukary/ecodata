from pymongo import MongoClient
import json

db = MongoClient()['centralisation_db']

# Get weekly decisions
weekly = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))

print(f"=== Documents avec horizon='SEMAINE': {len(weekly)} ===\n")

if weekly:
    doc = weekly[0]
    print("Structure du premier document:\n")
    print(json.dumps(doc, indent=2, default=str))
else:
    print("❌ Aucun document avec horizon='SEMAINE'")
    print("\nDocuments par horizon:")
    horizons = db.decisions_finales_brvm.aggregate([
        {"$group": {"_id": "$horizon", "count": {"$sum": 1}}}
    ])
    for h in horizons:
        print(f"  {h['_id']}: {h['count']} documents")

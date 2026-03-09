"""Afficher structure TOP5"""
from pymongo import MongoClient
import json

db = MongoClient('mongodb://localhost:27017/')['centralisation_db']

print("=== STRUCTURE TOP5 ===\n")
top5 = list(db.top5_weekly_brvm.find({}, {'_id': 0}).sort([('rank', 1)]))

if top5:
    print(f"Total: {len(top5)} recommendations\n")
    print("Premier element:")
    print(json.dumps(top5[0], indent=2, default=str))
    print("\n\nChamps disponibles:")
    for key in sorted(top5[0].keys()):
        print(f"  - {key}: {type(top5[0][key]).__name__}")
else:
    print("Aucune donnee TOP5")

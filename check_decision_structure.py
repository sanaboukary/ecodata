from pymongo import MongoClient
import json

db = MongoClient()['centralisation_db']

# Get one document from decisions_finales_brvm
doc = db.decisions_finales_brvm.find_one()

print("=== Structure d'un document decisions_finales_brvm ===\n")
print(json.dumps(doc, indent=2, default=str))

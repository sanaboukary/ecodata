from pymongo import MongoClient
import json

db = MongoClient()['centralisation_db']

# Get one full document
doc = db.prices_weekly.find_one()
print("Structure d'un document prices_weekly:")
print(json.dumps(doc, indent=2, default=str))

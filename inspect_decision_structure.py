# Script to inspect a sample document from the decisions_finales_brvm collection
# Usage: python inspect_decision_structure.py

from pymongo import MongoClient
import json

# Update with your MongoDB connection string if needed
client = MongoClient('mongodb://localhost:27017/')
db = client['brvm']  # Update with your DB name if different
collection = db['decisions_finales_brvm']

doc = collection.find_one()
if doc:
    print(json.dumps(doc, indent=2, default=str))
else:
    print('No document found in decisions_finales_brvm')

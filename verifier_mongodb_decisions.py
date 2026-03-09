from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017/")
db = client["brvm"]

print("--- Décisions BRVM enregistrées ---")
for doc in db.curated_observations.find({"source": "BRVM_DECISION_ENGINE"}):
    pprint(doc)

from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017/")
db = client["brvm"]

print("--- Contenu de brvm_ai_analysis ---")
for doc in db.brvm_ai_analysis.find({}):
    pprint(doc)

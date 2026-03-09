#!/usr/bin/env python3
from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

doc = db.curated_observations.find_one({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})

if doc:
    attrs = doc.get("attrs", {})
    print(json.dumps(attrs, indent=2, ensure_ascii=False))
else:
    print("Aucune analyse")

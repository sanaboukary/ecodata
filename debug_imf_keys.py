#!/usr/bin/env python3
"""Debug IMF keys format"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client.centralisation_db

# Récupérer 10 exemples de clés IMF
samples = list(db.curated_observations.find({'source': 'IMF'}).limit(10))

print("\n=== EXEMPLES DE CLÉS IMF ===\n")
for i, doc in enumerate(samples, 1):
    key = doc.get('key', '')
    ts = doc.get('ts', '')
    value = doc.get('value', '')
    print(f"{i}. Key: {key}")
    print(f"   Date: {ts}, Value: {value}")
    print()

client.close()

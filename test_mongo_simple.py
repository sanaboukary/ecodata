#!/usr/bin/env python3
"""Requête directe MongoDB"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Compter BRVM
brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
print(f"BRVM documents: {brvm_count}")

# Prendre 5 exemples
docs = list(db.curated_observations.find({'source': 'BRVM'}).limit(5))
print(f"\nTrouvé {len(docs)} documents\n")

for i, doc in enumerate(docs, 1):
    print(f"Document {i}:")
    print(f"  key: {doc.get('key')}")
    print(f"  ts: {doc.get('ts')}")
    print(f"  value: {doc.get('value')}")
    print()

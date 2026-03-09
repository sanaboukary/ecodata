#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Chercher les donnees curated"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

print("\n" + "="*80)
print("RECHERCHE DES DONNEES")
print("="*80 + "\n")

# Lister toutes les bases
print("BASES DE DONNEES disponibles:")
for db_name in client.list_database_names():
    if db_name not in ['admin', 'local', 'config']:
        print(f"\n  {db_name}:")
        db = client[db_name]
        for coll_name in db.list_collection_names():
            count = db[coll_name].count_documents({})
            if count > 0:
                print(f"    - {coll_name:<35} : {count:>8,} docs")

# Chercher specifiquement curated dans toutes les bases
print("\n\n" + "="*80)
print("RECHERCHE 'curated_observations' dans toutes les bases:")
print("="*80)

for db_name in client.list_database_names():
    db = client[db_name]
    if 'curated_observations' in db.list_collection_names():
        count = db.curated_observations.count_documents({})
        print(f"\n  {db_name}.curated_observations : {count:,} docs")
        if count > 0:
            sample = db.curated_observations.find_one()
            if sample:
                print(f"    Exemple: {list(sample.keys())[:5]}")

print("\n" + "="*80 + "\n")

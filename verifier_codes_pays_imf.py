#!/usr/bin/env python3
"""Vérifier les codes pays utilisés dans les données IMF"""
from pymongo import MongoClient
from collections import Counter

client = MongoClient('mongodb://localhost:27017')
db = client.centralisation_db

# Récupérer toutes les clés IMF
imf_obs = db.curated_observations.find({'source': 'IMF'}, {'key': 1})

# Extraire les codes pays (dernière partie de la clé après _)
pays_codes = []
for obs in imf_obs:
    key = obs.get('key', '')
    # Format: INDICATEUR_PAYS (ex: NGDP_RPCH_BJ)
    parts = key.split('_')
    if len(parts) >= 2:
        code_pays = parts[-1]  # Dernier élément
        pays_codes.append(code_pays)

# Compter occurrences
counter = Counter(pays_codes)

print("\n=== CODES PAYS DANS LES DONNÉES IMF ===\n")
for code, count in sorted(counter.items()):
    print(f"{code}: {count:,} observations")

print(f"\nTotal pays uniques: {len(counter)}")
print(f"Total observations IMF: {db.curated_observations.count_documents({'source': 'IMF'})}")

client.close()

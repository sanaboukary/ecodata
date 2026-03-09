#!/usr/bin/env python3
"""Check rapide de l'état des collectes"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client.centralisation_db

print("\n" + "="*60)
print("ETAT ACTUEL DES COLLECTES")
print("="*60 + "\n")

sources = {
    'WorldBank': 35000,
    'IMF': 9000,
    'AfDB': 4000,
    'UN_SDG': 1000,
    'BRVM': 2000
}

total_actuel = 0
total_objectif = sum(sources.values())

for source, objectif in sources.items():
    count = db.curated_observations.count_documents({'source': source})
    total_actuel += count
    pct = (count / objectif * 100) if objectif > 0 else 0
    
    if pct >= 90:
        statut = "✅ EXCELLENT"
    elif pct >= 75:
        statut = "🟢 BON"
    elif pct >= 50:
        statut = "🟡 MOYEN"
    else:
        statut = "🔴 FAIBLE"
    
    print(f"{source:15} : {count:6,} / {objectif:6,} ({pct:5.1f}%) {statut}")

print("\n" + "="*60)
pct_total = (total_actuel / total_objectif * 100)
print(f"{'TOTAL':15} : {total_actuel:6,} / {total_objectif:6,} ({pct_total:5.1f}%)")
print("="*60 + "\n")

client.close()

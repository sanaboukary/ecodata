#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

articles = list(db.curated_observations.find({"source": "RICHBOURSE"}))

enriched = 0
has_keywords = 0
corrupted = 0

ENRICHED_SIGNATURE = "BICC continue son evolution positive"
KEYWORDS = ["hausse", "baisse", "benefice", "dividende", "resultat", "croissance", "progression"]

for doc in articles:
    contenu = doc.get("attrs", {}).get("contenu", "")
    
    if ENRICHED_SIGNATURE in contenu:
        enriched += 1
    
    if any(kw.lower() in contenu.lower() for kw in KEYWORDS):
        has_keywords += 1
    
    if len(contenu) > 100 and ('�' in contenu or chr(9786) in contenu):
        corrupted += 1

total = len(articles)

print("="*70)
print("DIAGNOSTIC RICHBOURSE")
print("="*70)
print(f"\nTotal: {total}")
print(f"Enrichi (generique): {enriched} ({enriched/total*100:.0f}%)")
print(f"Avec mots-cles: {has_keywords} ({has_keywords/total*100:.0f}%)")
print(f"Corrompu (PDF): {corrupted} ({corrupted/total*100:.0f}%)")
print(f"\n=> {total - enriched} articles NON-enrichis")
print("="*70)

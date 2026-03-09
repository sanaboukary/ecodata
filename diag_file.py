#!/usr/bin/env python3

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

articles = list(db.curated_observations.find({"source": "RICHBOURSE"}))

enriched = 0
has_keywords = 0

ENRICHED_SIG = "BICC continue son evolution positive"
KEYWORDS = ["hausse", "baisse", "benefice", "dividende", "resultat", "croissance"]

for doc in articles:
    contenu = doc.get("attrs", {}).get("contenu", "")
    if ENRICHED_SIG in contenu:
        enriched += 1
    if any(kw in contenu.lower() for kw in KEYWORDS):
        has_keywords += 1

total = len(articles)

with open("diagnostic_resultat.txt", "w") as f:
    f.write("DIAGNOSTIC RICHBOURSE\n")
    f.write("="*60 + "\n")
    f.write(f"Total: {total}\n")
    f.write(f"Enrichi: {enriched} ({enriched/total*100:.0f}%)\n")
    f.write(f"Avec mots-cles: {has_keywords} ({has_keywords/total*100:.0f}%)\n")
    f.write(f"NON-enrichis: {total - enriched}\n")

print("Resultat ecrit dans diagnostic_resultat.txt")

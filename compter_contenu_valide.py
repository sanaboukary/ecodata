#!/usr/bin/env python3
"""Check how many articles have valid vs corrupted content"""

from pymongo import MongoClient
import re

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

print("="*80)
print("DIAGNOSTIC CONTENU RICHBOURSE")
print("="*80)

articles = list(db.curated_observations.find({"source": "RICHBOURSE"}))

valid_count = 0
corrupted_count = 0
enriched_count = 0
keywords_count = 0

# Signature du contenu enrichi
ENRICHED_SIGNATURE = "BICC continue son evolution positive"

# Mots-clés à chercher
KEYWORDS = ["hausse", "baisse", "bénéfice", "dividende", "résultat", "croissance", "progression"]

for doc in articles:
    contenu = doc.get("attrs", {}).get("contenu", "")
    
    # Check si enrichi
    if ENRICHED_SIGNATURE in contenu:
        enriched_count += 1
   
    # Check si contient des mots-clés
    if any(kw.lower() in contenu.lower() for kw in KEYWORDS):
        keywords_count += 1
        valid_count += 1
    # Check si corrompu (caractères binaires)
    elif any(c in contenu for c in ['�', '☺', '♥', '♦', '♣', '♠']):
        corrupted_count += 1
    elif len(contenu) >= 100:
        # Contenu long sans mots-clés ni corruption
        valid_count += 1

total = len(articles)

print(f"\nTotal articles RICHBOURSE: {total}")
print(f"\nREPARTITION:")
print(f"   Enrichi (generique):  {enriched_count} ({enriched_count/total*100:.0f}%)")
print(f"   Avec mots-cles:       {keywords_count} ({keywords_count/total*100:.0f}%)")
print(f"   Contenu valide:       {valid_count} ({valid_count/total*100:.0f}%)")
print(f"   Contenu corrompu:     {corrupted_count} ({corrupted_count/total*100:.0f}%)")

# Exemples de corrupted
if corrupted_count > 0:
    print(f"\nExemples de contenu CORROMPU:")
    corrupted_samples = [
        doc for doc in articles 
        if any(c in doc.get("attrs", {}).get("contenu", "") for c in ['�', '☺', '♥'])
    ][:3]
    
    for doc in corrupted_samples:
        titre = doc.get("attrs", {}).get("titre", "N/A")
        print(f"   - {titre[:60]}")

print(f"\nSOLUTION:")
print(f"   Les {total - enriched_count} articles non-enrichis doivent etre traites")
print(f"   -> Enrichissement cible necessaire")
print(f"   -> Ou ameliorer l'extraction PDF")

print("\n" + "="*80)

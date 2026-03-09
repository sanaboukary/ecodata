#!/usr/bin/env python3
"""Check actual content of RICHBOURSE articles"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

print("="*80)
print("CONTENU RÉEL DES ARTICLES RICHBOURSE")
print("="*80)

# Prendre 3 exemples
articles = list(db.curated_observations.find({"source": "RICHBOURSE"}).limit(3))

for i, doc in enumerate(articles, 1):
    attrs = doc.get("attrs", {})
    titre = attrs.get("titre", "N/A")
    contenu = attrs.get("contenu", "")
    
    print(f"\n📰 ARTICLE {i}: {titre}")
    print(f"   Longueur: {len(contenu)} caractères")
    print(f"\n   CONTENU (300 premiers caractères):")
    print(f"   {'-'*76}")
    print(f"   {contenu[:300]}")
    print(f"   {'-'*76}")
    
    # Chercher mots-clés
    keywords = [
        "hausse", "baisse", "bénéfice", "dividende", "résultat",
        "croissance", "progression", "augmentation", "recul", "perte"
    ]
    
    found = [kw for kw in keywords if kw.lower() in contenu.lower()]
    print(f"\n   MOTS-CLÉS TROUVÉS: {found if found else '❌ AUCUN'}")
    print()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFIER LE CONTENU DES PUBLICATIONS
"""

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']
coll = db['curated_observations']

print("="*80)
print("VERIFICATION CONTENU PUBLICATIONS")
print("="*80)

# Prendre 3 exemples de chaque source
for source in ['BRVM_PUBLICATION', 'RICHBOURSE']:
    print(f"\n{'='*80}")
    print(f"{source}")
    print(f"{'='*80}")
    
    docs = list(coll.find({'source': source}).limit(3))
    
    for i, doc in enumerate(docs, 1):
        print(f"\nPublication {i}:")
        attrs = doc.get('attrs', {})
        
        # Afficher tous les champs attrs
        print(f"  Champs attrs: {list(attrs.keys())}")
        
        # Chercher le texte
        text = attrs.get('full_text') or attrs.get('description') or attrs.get('contenu') or attrs.get('text')
        
        if text:
            print(f"\n  TEXTE ({len(text)} chars):")
            print(f"  {text[:400]}")
            print(f"  ...")
        else:
            print("  ❌ AUCUN TEXTE TROUVE!")
            print(f"  attrs.keys(): {list(attrs.keys())[:10]}")
            # Afficher les 3 premiers champs
            for key in list(attrs.keys())[:5]:
                val = attrs[key]
                if isinstance(val, str) and len(val) > 0:
                    print(f"    {key}: {val[:100]}")
        
        # Afficher les scores sémantiques
        print(f"\n  semantic_score_base: {attrs.get('semantic_score_base', 'N/A')}")
        print(f"  semantic_tags: {attrs.get('semantic_tags', 'N/A')}")
        print(f"  semantic_reasons: {attrs.get('semantic_reasons', 'N/A')}")

print("\n" + "="*80)
print("FIN")
print("="*80)

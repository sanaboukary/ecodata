#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUTION RAPIDE - Analyser seulement RICHBOURSE
(Les PDFs BRVM sont trop complexes à extraire)
"""

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("SOLUTION PRAGMATIQUE - RICHBOURSE SEULEMENT")
print("="*80)

# 1. Vérifier RICHBOURSE
richbourse = list(db.curated_observations.find({'source': 'RICHBOURSE'}))
print(f"\n[1] RICHBOURSE: {len(richbourse)} publications")

avec_contenu = 0
sans_contenu = 0

for doc in richbourse:
    contenu = doc.get('attrs', {}).get('contenu', '')
    if contenu and len(contenu) > 20:
        avec_contenu += 1
    else:
        sans_contenu += 1

print(f"  ✅ Avec contenu (>20 chars): {avec_contenu}")
print(f"  ❌ Sans contenu: {sans_contenu}")

if avec_contenu > 0:
    print(f"\n✅ {avec_contenu} articles RICHBOURSE ont du texte exploitable!")
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("  1. python analyse_semantique_brvm_v3.py")
    print("     → Analyser les {avec_contenu} articles RICHBOURSE")
    print("  2. python agregateur_semantique_actions.py")
    print("     → Agréger par action")
    print("  3. python pipeline_brvm.py")
    print("     → Générer recommandations avec sentiment")
else:
    print("\n❌ RICHBOURSE n'a pas de contenu non plus!")
    print("   Il faut re-collecter avec extraction de texte")

# Montrer exemples
print("\n" + "="*80)
print("EXEMPLES RICHBOURSE AVEC CONTENU:")
print("="*80)

for doc in richbourse[:3]:
    attrs = doc.get('attrs', {})
    titre = attrs.get('titre', 'Sans titre')
    contenu = attrs.get('contenu', '')
    
    print(f"\nTitre: {titre[:70]}")
    print(f"Contenu ({len(contenu)} chars): {contenu[:200]}...")

print("\n" + "="*80)

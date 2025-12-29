#!/usr/bin/env python3
import os
import glob

print("\n" + "="*80)
print("📊 INVENTAIRE FICHIERS PUBLICATIONS")
print("="*80)
print()

categories = {
    'Bulletins BRVM': 'bulletins_brvm_*.json',
    'Convocations AG': 'convocations_ag_*.json',
    'Rapports sociétés': 'rapports_brvm_*.json',
    'Sentiment NLP': 'sentiment_nlp_*.json',
    'Recommandations': 'recommandations_hebdo_*.json',
    'HTML bulletins': 'brvm_bulletins_*.html',
    'HTML AG': 'brvm_ag_*.html',
    'HTML rapports': 'brvm_rapports_*.html'
}

for nom, pattern in categories.items():
    fichiers = glob.glob(pattern)
    if fichiers:
        dernier = sorted(fichiers)[-1]
        taille = os.path.getsize(dernier) / 1024  # Ko
        print(f"✓ {nom:<25} : {len(fichiers)} fichier(s) | Dernier: {dernier} ({taille:.1f} Ko)")
    else:
        print(f"✗ {nom:<25} : Aucun fichier")

print("\n" + "="*80)
print()

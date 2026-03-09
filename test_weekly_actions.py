#!/usr/bin/env python3
"""Test rapide pour compter les actions hebdomadaires"""

from pymongo import MongoClient

# Connexion MongoDB
db = MongoClient('mongodb://localhost:27017').centralisation_db

# Obtenir toutes les actions hebdomadaires
actions = db.curated_observations.distinct('ticker', {
    'dataset': 'STOCK_PRICE',
    'granularite': 'WEEKLY'
})

# Filtrer les indices BRVM (non tradables)
indices_brvm = ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']
actions_tradables = [a for a in actions if a and a not in indices_brvm]

print(f"\n{'='*60}")
print(f"ANALYSE DES ACTIONS HEBDOMADAIRES")
print(f"{'='*60}\n")
print(f"Total actions trouvées: {len(actions_tradables)}")

# Compter celles avec >= 14 semaines
actions_avec_donnees = []
actions_sans_donnees = []

for ticker in actions_tradables:
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': ticker
    })
    
    if count >= 14:
        actions_avec_donnees.append((ticker, count))
    else:
        actions_sans_donnees.append((ticker, count))

print(f"\n✓ Actions avec ≥14 semaines: {len(actions_avec_donnees)}")
print(f"✗ Actions avec <14 semaines: {len(actions_sans_donnees)}")

if actions_avec_donnees:
    print(f"\nÉchantillon actions analysables (≥14 semaines):")
    for ticker, count in sorted(actions_avec_donnees[:10], key=lambda x: -x[1]):
        print(f"  • {ticker:6s}: {count:2d} semaines")

if actions_sans_donnees:
    print(f"\nActions avec données insuffisantes:")
    for ticker, count in sorted(actions_sans_donnees, key=lambda x: -x[1]):
        print(f"  • {ticker:6s}: {count:2d} semaines")

print(f"\n{'='*60}\n")

#!/usr/bin/env python3
"""
Vérification simple des actions BRVM - Sans Django
"""
import os
from pymongo import MongoClient

# Connexion MongoDB directe
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_NAME = os.getenv('MONGODB_NAME', 'centralisation_db')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_NAME]

print("="*80)
print("📊 LISTE DES ACTIONS BRVM DANS MONGODB")
print("="*80)

# Récupérer toutes les actions
actions = sorted(db.curated_observations.distinct('key', {'source': 'BRVM'}))

print(f"\n✓ Total: {len(actions)} actions\n")

# Afficher avec comptage
for i, action in enumerate(actions, 1):
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'key': action
    })
    print(f"{i:3d}. {action:<20} ({count:,} observations)")

print("\n" + "="*80)

# Liste officielle des 47 actions
ACTIONS_OFFICIELLES = {
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM',
    'CABC', 'CBIBF', 'CFAC', 'CIEC', 'CIAC', 'ECOC', 'ETIT',
    'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONTBF', 'ORAC', 'ORGT',
    'PALC', 'PHCC', 'PRSC', 'SABC', 'SCRC', 'SDCC', 'SDSC',
    'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICB', 'SICC', 'SIVC',
    'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'SVOC',
    'TPCI', 'TTLC', 'TTLS', 'UNLC', 'UNXC'
}

# Analyse
actions_set = set(actions)
invalides = actions_set - ACTIONS_OFFICIELLES
manquantes = ACTIONS_OFFICIELLES - actions_set

print(f"\n📈 ANALYSE:")
print(f"   • Actions officielles BRVM: {len(ACTIONS_OFFICIELLES)}")
print(f"   • Actions dans MongoDB: {len(actions)}")
print(f"   • Actions invalides: {len(invalides)}")
print(f"   • Actions manquantes: {len(manquantes)}")

if invalides:
    print(f"\n❌ ACTIONS INVALIDES ({len(invalides)}):")
    for action in sorted(invalides):
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'key': action
        })
        print(f"   • {action:<20} ({count:,} observations) ⚠️")

if manquantes:
    print(f"\n⚠️  ACTIONS MANQUANTES ({len(manquantes)}):")
    for action in sorted(manquantes):
        print(f"   • {action}")

if not invalides and not manquantes:
    print(f"\n✅ Toutes les actions sont correctes!")

print("\n" + "="*80)

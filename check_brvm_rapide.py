#!/usr/bin/env python3
"""Vérification rapide des symboles BRVM"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

# Symboles distincts
symboles = db.curated_observations.distinct('key', {
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})

print(f"\n{'='*80}")
print(f"SYMBOLES BRVM DISTINCTS: {len(symboles)}")
print(f"{'='*80}\n")

OFFICIELS = [
    'ABJC', 'BICC', 'BICB', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAG', 'BOAM', 'BOAN', 'BOAS',
    'CABC', 'CBIBF', 'CFAC', 'CIAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'LIBC', 'LNBB',
    'NEIC', 'NSBC', 'NSIAC', 'NSIAS', 'NTLC', 'ONTBF', 'ORAC', 'ORGT', 'PALC', 'PRSC',
    'PVBC', 'SAFH', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SGBCI', 'SGBSL',
    'SHEC', 'SIBC', 'BISC', 'SICC', 'SICG', 'SITC', 'SIVC', 'SLBC', 'SMBC', 'SNDC',
    'SNTS', 'SOAC', 'SOGC', 'SPHB', 'SPHC', 'STAC', 'STBC', 'SVOC', 'TPCI', 'TTBC',
    'TTLC', 'TTLS', 'TTRC', 'UNLB', 'UNLC', 'UNXC'
]

non_officiels = [s for s in symboles if s not in OFFICIELS]

if non_officiels:
    print(f"❌ {len(non_officiels)} SYMBOLES NON OFFICIELS (doublons):\n")
    for s in sorted(non_officiels):
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': s
        })
        print(f"   {s:15s} - {count:,} obs")
    
    print(f"\n{'='*80}")
    print("COMMANDE DE NETTOYAGE:")
    print(f"{'='*80}\n")
    print("python nettoyer_duplications_brvm.py\n")
else:
    print("✅ Aucun doublon - 47 actions officielles uniquement\n")

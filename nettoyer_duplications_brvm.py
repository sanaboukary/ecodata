#!/usr/bin/env python3
"""
Nettoyage des duplications BRVM - Conservation uniquement des 47 actions officielles
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Liste officielle des 47 actions BRVM
ACTIONS_BRVM_OFFICIELLES = [
    'ABJC', 'BICC', 'BICB', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAG', 'BOAM', 'BOAN', 'BOAS',
    'CABC', 'CBIBF', 'CFAC', 'CIAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'LIBC', 'LNBB',
    'NEIC', 'NSBC', 'NSIAC', 'NSIAS', 'NTLC', 'ONTBF', 'ORAC', 'ORGT', 'PALC', 'PRSC',
    'PVBC', 'SAFH', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SGBCI', 'SGBSL',
    'SHEC', 'SIBC', 'BISC', 'SICC', 'SICG', 'SITC', 'SIVC', 'SLBC', 'SMBC', 'SNDC',
    'SNTS', 'SOAC', 'SOGC', 'SPHB', 'SPHC', 'STAC', 'STBC', 'SVOC', 'TPCI', 'TTBC',
    'TTLC', 'TTLS', 'TTRC', 'UNLB', 'UNLC', 'UNXC'
]

print("=" * 120)
print("🧹 NETTOYAGE DES DUPLICATIONS BRVM")
print("=" * 120)
print()

# 1. Compter avant nettoyage
total_avant = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})

print(f"📊 Observations BRVM avant nettoyage: {total_avant:,}")
print()

# 2. Récupérer tous les symboles distincts
pipeline = [
    {'$match': {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    }},
    {'$group': {
        '_id': '$key',
        'count': {'$sum': 1}
    }}
]

symboles_db = list(db.curated_observations.aggregate(pipeline))
symboles_dict = {item['_id']: item['count'] for item in symboles_db}

print(f"📊 Symboles distincts avant nettoyage: {len(symboles_dict)}")
print()

# 3. Identifier les symboles à supprimer
symboles_a_supprimer = []
for symbol in symboles_dict.keys():
    if symbol not in ACTIONS_BRVM_OFFICIELLES:
        symboles_a_supprimer.append(symbol)

if symboles_a_supprimer:
    print(f"❌ {len(symboles_a_supprimer)} symboles non officiels détectés:")
    print("-" * 120)
    for symbol in sorted(symboles_a_supprimer):
        count = symboles_dict[symbol]
        print(f"   ❌ {symbol:15s} - {count:5,} observations → À SUPPRIMER")
    print()
    
    # Demander confirmation
    print("=" * 120)
    reponse = input("⚠️  Confirmer la suppression de ces symboles ? (oui/non): ").strip().lower()
    print()
    
    if reponse in ['oui', 'o', 'yes', 'y']:
        print("🧹 Suppression en cours...")
        print("-" * 120)
        
        total_supprime = 0
        for symbol in symboles_a_supprimer:
            result = db.curated_observations.delete_many({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol
            })
            supprime = result.deleted_count
            total_supprime += supprime
            print(f"   ✅ {symbol:15s} - {supprime:5,} observations supprimées")
        
        print()
        print(f"✅ Total supprimé: {total_supprime:,} observations")
        print()
        
        # 4. Vérifier après nettoyage
        total_apres = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE'
        })
        
        pipeline_apres = [
            {'$match': {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE'
            }},
            {'$group': {
                '_id': '$key'
            }}
        ]
        
        symboles_apres = list(db.curated_observations.aggregate(pipeline_apres))
        
        print("=" * 120)
        print("📊 RÉSULTAT DU NETTOYAGE")
        print("=" * 120)
        print(f"Observations AVANT  : {total_avant:,}")
        print(f"Observations APRÈS  : {total_apres:,}")
        print(f"Supprimées          : {total_supprime:,}")
        print()
        print(f"Symboles AVANT      : {len(symboles_dict)}")
        print(f"Symboles APRÈS      : {len(symboles_apres)}")
        print(f"Actions officielles : 47")
        print()
        
        if len(symboles_apres) == 47:
            print("✅ Base de données nettoyée ! 47 actions officielles restantes.")
        else:
            print(f"⚠️  {len(symboles_apres)} symboles restants (attendu: 47)")
        
        print()
        print("📋 PROCHAINES ÉTAPES:")
        print("   1. Re-générer les recommandations IA")
        print("      python generer_recommandations_maintenant.py")
        print()
        print("   2. Vérifier le dashboard")
        print("      http://127.0.0.1:8000/brvm/")
        print()
        
    else:
        print("❌ Nettoyage annulé")
        print()

else:
    print("✅ Aucun symbole non officiel détecté - Base de données propre !")
    print()

print("=" * 120)

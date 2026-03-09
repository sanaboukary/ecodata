#!/usr/bin/env python3
"""Check AGREGATION_SEMANTIQUE_ACTION data"""
import os, sys, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== AGREGATION_SEMANTIQUE_ACTION ===\n")

# Count documents
count = db.curated_observations.count_documents({'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
print(f"Nombre total de documents : {count}\n")

if count == 0:
    print("❌ Aucune donnée! Le script agregateur_semantique_actions.py doit être exécuté.\n")
    sys.exit(1)

# Get all symbols
symbols = db.curated_observations.distinct('key', {'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
print(f"Actions disponibles : {len(symbols)}")
print(f"  {symbols}\n")

# Check one document
doc = db.curated_observations.find_one({'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
print(f"Exemple de document (symbol={doc.get('key')}) :")
print(json.dumps(doc, indent=2, default=str))

print("\n=== VÉRIFICATION DES ATTRIBUTS REQUIS ===\n")

# Check attrs for all symbols
required_attrs = ['score_ct', 'volume_moyen', 'spread', 'prix_actuel', 'SMA5', 'SMA10', 'rsi']

for sym in symbols[:5]:  # Check first 5
    doc = db.curated_observations.find_one({'dataset': 'AGREGATION_SEMANTIQUE_ACTION', 'key': sym})
    attrs = doc.get('attrs', {})
    
    print(f"\n{sym}:")
    for attr in required_attrs:
        val = attrs.get(attr)
        status = "✅" if val is not None and val != 0 else "❌"
        print(f"  {status} {attr:20s} = {val}")
    
    # Filtres decision_finale_brvm.py
    print(f"\n  Filtres decision_finale_brvm:")
    volume = attrs.get('volume_moyen', 0)
    spread = attrs.get('spread', 100)
    score_tech = attrs.get('score_ct', 0)
    
    print(f"    volume_moyen >= 1000 ? {volume} → {'✅ PASS' if volume >= 1000 else '❌ FAIL'}")
    print(f"    spread <= 10 ? {spread} → {'✅ PASS' if spread <= 10 else '❌ FAIL'}")
    print(f"    score_ct >= 40 ? {score_tech} → {'✅ PASS' if score_tech >= 40 else '❌ FAIL'}")

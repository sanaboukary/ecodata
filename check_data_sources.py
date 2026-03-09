#!/usr/bin/env python3
"""Check data sources in curated_observations"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== SOURCES DISPONIBLES ===\n")
sources = db.curated_observations.distinct('source')
print(f"Sources trouvées : {sources}\n")

counts = {s: db.curated_observations.count_documents({'source': s}) for s in sources}
print("Nombre de documents par source :")
for s, c in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {s:30s} : {c:5d} docs")

print("\n=== DATASETS DISPONIBLES ===\n")
datasets = db.curated_observations.distinct('dataset')
print(f"Datasets dans curated_observations : {datasets}\n")

# Check AGREGATION_SEMANTIQUE_ACTION (utilisé par decision_finale_brvm.py)
print("\n=== AGREGATION_SEMANTIQUE_ACTION ===\n")
count = db.curated_observations.count_documents({'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
print(f"Documents avec dataset=AGREGATION_SEMANTIQUE_ACTION : {count}")

if count > 0:
    sample = db.curated_observations.find_one({'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
    print(f"\nExemple de document :")
    import json
    print(json.dumps(sample, indent=2, default=str))
    
    # Check prix data
    symbols = db.curated_observations.distinct('key', {'dataset': 'AGREGATION_SEMANTIQUE_ACTION'})
    print(f"\n{len(symbols)} actions dans AGREGATION_SEMANTIQUE_ACTION")
    
    # Pick first symbol and check attrs
    if symbols:
        sym = symbols[0]
        doc = db.curated_observations.find_one({'dataset': 'AGREGATION_SEMANTIQUE_ACTION', 'key': sym})
        print(f"\nAttrs disponibles pour {sym} :")
        if 'attrs' in doc:
            for k, v in doc['attrs'].items():
                print(f"  {k:25s} : {v}")

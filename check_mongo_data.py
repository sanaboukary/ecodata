"""
Vérification simple des données MongoDB
"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== Vérification MongoDB ===\n")

# Compter les documents
count = db.curated_observations.count_documents({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
print(f"Documents AGREGATION_SEMANTIQUE_ACTION: {count}")

if count > 0:
    # Afficher un exemple
    sample = db.curated_observations.find_one({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
    print(f"\nExemple de document:")
    print(f"Symbol: {sample.get('attrs', {}).get('symbol')}")
    print(f"\nChamps disponibles dans attrs:")
    attrs = sample.get('attrs', {})
    for key in sorted(attrs.keys()):
        val = attrs[key]
        if not isinstance(val, (list, dict)):
            print(f"  - {key}: {val}")
        else:
            print(f"  - {key}: {type(val).__name__} (longueur: {len(val)})")

# Vérifier decisions_finales_brvm
count_decisions = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE"})
print(f"\n\nDécisions hebdomadaires dans MongoDB: {count_decisions}")

if count_decisions > 0:
    decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))
    print(f"\nDécisions trouvées:")
    for d in decisions:
        print(f"  - {d.get('symbol')}: {d.get('decision')} (classe {d.get('classe')})")

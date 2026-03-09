"""Vérification des données Publications BRVM"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Compter publications
pubs_count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'})
print(f"📄 Publications BRVM: {pubs_count}")

if pubs_count > 0:
    print("\n✅ Échantillon des publications:")
    samples = list(db.curated_observations.find({'source': 'BRVM_PUBLICATION'}).limit(5))
    for s in samples:
        print(f"  - {s.get('key', 'N/A')[:60]}")
        print(f"    Date: {s.get('ts', 'N/A')[:10]}")
        print()
else:
    print("\n⚠️ AUCUNE publication trouvée!")
    print("Sources disponibles:")
    sources = db.curated_observations.distinct('source')
    for src in sources:
        count = db.curated_observations.count_documents({'source': src})
        print(f"  - {src}: {count}")

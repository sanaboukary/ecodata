"""Audit: find future-dated documents in curated_observations."""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Top 10 ts les plus grands (string)
docs = list(db.curated_observations.find(
    {"ts": {"$type": "string"}},
    {"ts": 1, "source": 1, "dataset": 1, "key": 1}
).sort("ts", -1).limit(10))

print("Top 10 ts les plus grands (string) :")
for d in docs:
    print(f"  ts={d['ts']!r:30s} source={d.get('source','?'):20s} dataset={d.get('dataset','?'):30s} key={d.get('key','?')}")

# Compter docs avec ts ≥ 2026-06 (futurs)
futur = db.curated_observations.count_documents({"ts": {"$gte": "2026-06", "$type": "string"}})
print(f"\nDocs avec ts >= 2026-06 : {futur}")

# Supprimer les documents avec ts = 2026-12-31 (date de test fictive)
result = db.curated_observations.delete_many({"ts": "2026-12-31"})
print(f"Suppression ts='2026-12-31' : {result.deleted_count} docs supprimés")

# Vérifier le nouveau max
docs2 = list(db.curated_observations.find(
    {"ts": {"$type": "string"}},
    {"ts": 1}
).sort("ts", -1).limit(5))
print("\nNouveau top 5 ts :")
for d in docs2:
    print(f"  {d['ts']!r}")

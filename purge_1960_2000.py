
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()
result_wb = db.curated_observations.delete_many({
    "source": "WorldBank",
    "ts": {"$gte": "1960", "$lt": "2001"}
})
result_fmi = db.curated_observations.delete_many({
    "source": "IMF",
    "ts": {"$gte": "1960", "$lt": "2001"}
})
result_bad = db.curated_observations.delete_many({
    "source": "AfDB",
    "ts": {"$gte": "1960", "$lt": "2001"}
})

print("WorldBank supprimés:", result_wb.deleted_count)
print("IMF supprimés:", result_fmi.deleted_count)
print("AfDB supprimés:", result_bad.deleted_count)

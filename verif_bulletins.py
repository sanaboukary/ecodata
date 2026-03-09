import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
from plateforme_centralisation.mongo import get_mongo_db
import pprint

_, db = get_mongo_db()
result = list(db.curated_observations.find(
    {},
    {'_id': 0}
).sort([('ts', -1)])[:20]
pprint.pprint(result)

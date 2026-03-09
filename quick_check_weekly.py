#!/usr/bin/env python3
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()
count = db.prices_weekly.count_documents({})
print(f'Weekly docs: {count}')

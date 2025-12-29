#!/usr/bin/env python3
"""Inspect curated_observations collection and report counts, samples, schema issues."""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()
co = db.curated_observations

print('\n=== curated_observations quick inspection ===\n')

total = co.count_documents({})
print('Total documents:', total)

# Counts per source
pipeline = [{'$group': {'_id': '$source', 'count': {'$sum': 1}}}, {'$sort': {'count': -1}}]
by_source = list(co.aggregate(pipeline))
print('\nCounts by source:')
for r in by_source:
    print(' -', r.get('_id'), ':', r.get('count'))

# Distinct sample fields
print('\nDistinct top-level fields (sample of 50):')
print(list(co.aggregate([{'$project': {'k': {'$objectToArray': '$$ROOT'}}}, {'$unwind': '$k'}, {'$group': {'_id': '$k.k'}}, {'$limit': 50}])))

# For each source, show distinct indicators (limited), sample doc and counts of missing core fields
def show_source(src):
    q = {'source': src} if src else {}
    count = co.count_documents(q)
    print(f"\n--- Source: {src} (count={count}) ---")
    # distinct indicators
    inds = co.distinct('indicator', q)
    print('distinct indicators (first 20):', inds[:20])
    # sample doc
    doc = co.find_one(q)
    print('\nsample doc keys:', list(doc.keys()) if doc else None)
    if doc:
        # pretty print sample limited
        sample = {k: (v if k in ('indicator','ts','value','source') else '<...>') for k,v in doc.items()}
        print('sample doc (truncated):')
        print(json.dumps(sample, default=str, indent=2, ensure_ascii=False))
    # missing fields counts
    missing_ts = co.count_documents({**q, 'ts': {'$in': [None, '']}})
    missing_indicator = co.count_documents({**q, 'indicator': {'$in': [None, '']}})
    missing_value = co.count_documents({**q, 'value': {'$in': [None, '']}})
    missing_country = co.count_documents({**q, '$or': [{'metadata.country': {'$in': [None, '']}}, {'metadata': {'$exists': False}}]})
    print('missing ts:', missing_ts, ' missing indicator:', missing_indicator, ' missing value:', missing_value, ' missing metadata.country:', missing_country)

sources = [r.get('_id') for r in by_source]
for s in sources:
    show_source(s)

# Overall anomalies (documents with unexpected shapes)
anom = co.find_one({'$or': [{'metadata': {'$type': 2}}, {'indicator': {'$type': 3}}]})
if anom:
    print('\nWarning: found document(s) with metadata as string or indicator as string type that may need standardization. Example doc id:', anom.get('_id'))

print('\nInspection complete.')

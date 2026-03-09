from pymongo import MongoClient

db = MongoClient()['centralisation_db']

# Get all distinct weeks and sort them
weeks = sorted(db.prices_weekly.distinct('week'))

print(f"Total weeks in database: {len(weeks)}")
print(f"\nFirst 5 weeks:")
for w in weeks[:5]:
    count = db.prices_weekly.count_documents({'week': w})
    print(f"  {w}: {count} actions")

print(f"\nLast 10 weeks:")
for w in weeks[-10:]:
    count = db.prices_weekly.count_documents({'week': w})
    print(f"  {w}: {count} actions")

# What week TOP5 ENGINE used
print(f"\n=== TOP5 ENGINE recommendations ===")
top5_docs = list(db.top5_weekly_brvm.find().limit(3))
for doc in top5_docs:
    print(f"  {doc['symbol']}: {doc.get('date_analyse', 'N/A')}")

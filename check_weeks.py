from pymongo import MongoClient

db = MongoClient()['centralisation_db']
weeks = sorted(db.prices_weekly.distinct('semaine'))
print("Dernières semaines:")
for w in weeks[-10:]:
    count = db.prices_weekly.count_documents({'semaine': w})
    print(f"  {w}: {count} actions")

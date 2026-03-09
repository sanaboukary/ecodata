from pymongo import MongoClient
from datetime import datetime

db = MongoClient()['centralisation_db']

# Check prices_weekly
pw_count = db.prices_weekly.count_documents({})
print(f"prices_weekly: {pw_count} documents total")

if pw_count > 0:
    # Get some sample docs
    sample = list(db.prices_weekly.find().limit(3))
    for doc in sample:
        print(f"  {doc.get('symbol')}: {doc.get('semaine')} - {doc.get('close')} FCFA")
    
    # Get distinct weeks
    weeks = sorted(db.prices_weekly.distinct('semaine'))
    print(f"\nSemaines: {len(weeks)} distinct")
    print(f"Première: {weeks[0]}")
    print(f"Dernière: {weeks[-1]}")

# Check top5_weekly_brvm
print(f"\ntop5_weekly_brvm: {db.top5_weekly_brvm.count_documents({})} documents")
if db.top5_weekly_brvm.count_documents({}) > 0:
    latest = db.top5_weekly_brvm.find_one(sort=[('_id', -1)])
    print(f"  Dernière reco: {latest.get('symbol')} - {latest.get('date_analyse')}")

# Check decisions_finales_brvm
print(f"\ndecisions_finales_brvm: {db.decisions_finales_brvm.count_documents({})} documents")

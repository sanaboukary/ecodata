from pymongo import MongoClient
from datetime import datetime, timedelta

db = MongoClient()['centralisation_db']

# Simulate TOP5 ENGINE's week selection
week_ago = datetime.now() - timedelta(days=7)
week_str = week_ago.strftime("%Y-W%V")

print(f"TOP5 ENGINE searching for week: {week_str}")
print(f"(7 days ago from {datetime.now().strftime('%Y-%m-%d')})\n")

# Check if this week exists
count = db.prices_weekly.count_documents({'week': week_str})
print(f"Documents found with week={week_str}: {count}")

if count > 0:
    sample = list(db.prices_weekly.find({'week': week_str}).limit(5))
    print("\nSample data:")
    for doc in sample:
        print(f"  {doc['symbol']}: {doc['close']} FCFA")
else:
    # Show what weeks actually exist
    weeks = sorted(db.prices_weekly.distinct('week'))
    print(f"\nWeeks available: {len(weeks)} total")
    if weeks:
        print(f"Latest week in DB: {weeks[-1]}")
        latest_count = db.prices_weekly.count_documents({'week': weeks[-1]})
        print(f"Actions in latest week: {latest_count}")

# Check decision_finale_brvm approach
current_week_str = datetime.now().strftime("%Y-W%V")
print(f"\n\nDECISION_FINALE searching for week: {current_week_str}")
print(f"(current week from {datetime.now().strftime('%Y-%m-%d')})\n")

count2 = db.prices_weekly.count_documents({'week': current_week_str})
print(f"Documents found with week={current_week_str}: {count2}")

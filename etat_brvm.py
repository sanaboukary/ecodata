from pymongo import MongoClient
from datetime import datetime

c = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin', serverSelectionTimeoutMS=3000)
db = c['centralisation_db']

print("\n=== ETAT BASE BRVM ===\n")

# Total
total = db.curated_observations.count_documents({'source':'BRVM'})
print(f"Total observations: {total:,}")

# Dates
dates = sorted(db.curated_observations.distinct('ts', {'source':'BRVM'}))
if dates:
    print(f"Premiere date: {dates[0][:10]}")
    print(f"Derniere date: {dates[-1][:10]}")
    print(f"Nb jours: {len(dates)}")

# Actions
symbols = db.curated_observations.distinct('key', {'source':'BRVM'})
print(f"Actions: {len(symbols)}")

# Dernière séance
if dates:
    last_date = dates[-1][:10]
    count_last = db.curated_observations.count_documents({'source':'BRVM','ts':{'$regex':f'^{last_date}'}})
    print(f"\nDerniere seance ({last_date}): {count_last} actions")

print("\n=== RECOMMENDATION ===")
print("Marche ferme 26/12 (Noel)")
print("Utiliser donnees du 23/12 pour Top 5\n")

c.close()

print("START")

from pymongo import MongoClient

print("Import OK")

client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)

print("Client created")

db = client['centralisation_db']

print("DB selected")

count = db.prices_weekly.count_documents({})

print(f"Documents prices_weekly: {count}")

doc = db.prices_weekly.find_one({'symbol': 'SAFC', 'week': '2026-W06'})

print(f"SAFC 2026-W06: {doc is not None}")

if doc:
    print(f"Close: {doc.get('close')}")
    print(f"ATR%: {doc.get('atr_pct')}")
    print(f"Volume Zscore: {doc.get('volume_zscore')}")
    print(f"Acceleration: {doc.get('acceleration')}")

print("END")

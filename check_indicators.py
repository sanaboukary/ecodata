from pymongo import MongoClient
from datetime import datetime, timedelta
import json

db = MongoClient()['centralisation_db']

# Semaine W07
week_ago = datetime.now() - timedelta(days=7)
week_str = week_ago.strftime("%Y-W%V")

# Get full document
doc = db.prices_weekly.find_one({'week': week_str})

print(f"=== Structure complète d'un document prices_weekly (W07) ===\n")
print(json.dumps(doc, indent=2, default=str))
print(f"\n=== Champs présents ===")
print(list(doc.keys()))

print(f"\n=== Champs manquants pour ELITE filters ===")
required = ['rs_4_weeks', 'volume_spike', 'acceleration', 'atr_pct', 'breakout_3w']
for field in required:
    status = "✅" if field in doc else "❌"
    value = doc.get(field, "ABSENT")
    print(f"{status} {field}: {value}")

#!/usr/bin/env python3
import time
from pymongo import MongoClient

print("Suivi progression en temps reel...")
print("(Ctrl+C pour arreter)")
print()

db = MongoClient()['centralisation_db']
total = db.prices_weekly.count_documents({})

for i in range(20):  # 20 iterations
    after = db.prices_weekly.count_documents({'indicators_computed': True})
    pct = 100*after/total
    remaining = total - after
    
    print(f"\r[{i+1}/20] {after}/{total} ({pct:.1f}%) - Reste: {remaining}    ", end='', flush=True)
    time.sleep(3)  # Attendre 3 secondes

print()
print("\nFin du suivi")

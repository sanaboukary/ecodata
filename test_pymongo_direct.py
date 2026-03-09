#!/usr/bin/env python3
"""Test ultra-direct avec pymongo seul"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["brvm_db"]

print("\n=== DECISIONS BUY ===\n")
recos = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE", "decision": "BUY"}))
print(f"Total: {len(recos)}\n")

for r in recos:
    sym = r.get('symbol', 'N/A')
    cls = r.get('classe', 'N/A')
    conf = r.get('confidence', 0)
    gain = r.get('gain_attendu', 0)
    rr = r.get('rr', 0)
    print(f"{sym:8s} | {cls} | {conf:.1f}% | {gain:.1f}% | RR {rr:.2f}")

print("\n=== TOP5 ===\n")
top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
print(f"Total: {len(top5)}\n")

for t in top5:
    print(f"#{t.get('rank')} - {t.get('symbol')}")

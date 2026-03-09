#!/usr/bin/env python3
"""Test direct MongoDB pour TOP5"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== DECISIONS BUY HEBDOMADAIRES ===\n")
recos = list(db.decisions_finales_brvm.find({
    "horizon": "SEMAINE",
    "decision": "BUY"
}))

print(f"Total BUY: {len(recos)}\n")

for r in recos:
    print(f"{r['symbol']:8s} | Classe: {r.get('classe', 'N/A')} | Conf: {r.get('confidence', 0):.1f}% | Gain: {r.get('gain_attendu', 0):.1f}% | RR: {r.get('rr', 0):.2f}")

print("\n=== TOP5 SAUVEGARDES ===\n")
top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
print(f"Total TOP5: {len(top5)}\n")

for t in top5:
    print(f"#{t['rank']} - {t['symbol']}")

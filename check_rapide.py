#!/usr/bin/env python3
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client.centralisation_db

today = datetime.now().strftime('%Y-%m-%d')

print(f"\n{'='*60}")
print(f"VERIFICATION RAPIDE - {today}")
print(f"{'='*60}\n")

try:
    brvm_today = db.curated_observations.count_documents({'source': 'BRVM', 'ts': today})
    print(f"✅ BRVM aujourd'hui ({today}): {brvm_today} observations")
except Exception as e:
    print(f"❌ Erreur: {e}")

try:
    brvm_total = db.curated_observations.count_documents({'source': 'BRVM'})
    print(f"📊 BRVM total: {brvm_total} observations")
except Exception as e:
    print(f"❌ Erreur: {e}")

try:
    wb_2025 = db.curated_observations.count_documents({'source': 'WorldBank', 'ts': {'$regex': '^2025'}})
    wb_2026 = db.curated_observations.count_documents({'source': 'WorldBank', 'ts': {'$regex': '^2026'}})
    print(f"🌍 World Bank 2025: {wb_2025} observations")
    print(f"🌍 World Bank 2026: {wb_2026} observations")
except Exception as e:
    print(f"❌ Erreur: {e}")

print(f"\n{'='*60}\n")

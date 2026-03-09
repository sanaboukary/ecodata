#!/usr/bin/env python3
"""Lancer collecte + pipeline DAILY pour aujourd'hui"""
import os, sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

print(f"\n🚀 COLLECTE + PIPELINE DAILY - {datetime.now().strftime('%Y-%m-%d')}\n")
print("="*80)

# 1. Vérifier état actuel
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

print("\n📊 État avant collecte:")
raw_before = db.prices_intraday_raw.count_documents({})
daily_before = db.prices_daily.count_documents({})
print(f"   RAW: {raw_before:,}")
print(f"   DAILY: {daily_before:,}")

# 2. Lancer collecte RAW
print("\n1️⃣ COLLECTE RAW...")
print("-"*80)
from brvm_pipeline.collector_raw_no_overwrite import collect_today
collect_today()

raw_after = db.prices_intraday_raw.count_documents({})
print(f"✅ RAW collecté: +{raw_after - raw_before} docs (total: {raw_after:,})")

# 3. Lancer pipeline DAILY
print("\n2️⃣ PIPELINE DAILY...")
print("-"*80)
from brvm_pipeline.pipeline_daily import process_single_date
today = datetime.now().strftime('%Y-%m-%d')
process_single_date(today)

daily_after = db.prices_daily.count_documents({})
print(f"✅ DAILY traité: +{daily_after - daily_before} docs (total: {daily_after:,})")

print("\n" + "="*80)
print("✅ COLLECTE JOURNALIÈRE TERMINÉE")
print("="*80 + "\n")

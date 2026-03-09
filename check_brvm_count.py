#!/usr/bin/env python3
"""
Vérification rapide du nombre d'observations BRVM
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

_, db = get_mongo_db()

total_brvm = db.curated_observations.count_documents({
    "source": "BRVM",
    "dataset": "STOCK_PRICE"
})

print(f"Total observations BRVM : {total_brvm}")

# Dernière collecte
derniere = db.curated_observations.find_one(
    {"source": "BRVM", "dataset": "STOCK_PRICE"},
    sort=[("timestamp", -1)]
)

if derniere:
    ts = derniere.get("timestamp", derniere.get("ts"))
    print(f"Dernière collecte : {ts}")
    print(f"Action : {derniere.get('key', derniere.get('attrs', {}).get('symbole'))}")

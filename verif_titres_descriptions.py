#!/usr/bin/env python3
"""
VÉRIFICATION DES CHAMPS TITRE ET DESCRIPTION DANS LES PUBLICATIONS
Affiche un échantillon de titres et descriptions pour diagnostic
"""
import os
import sys
from pprint import pprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== ÉCHANTILLON TITRES/DESCRIPTIONS DES PUBLICATIONS ===\n")

cursor = db.curated_observations.find({}, {"attrs.titre": 1, "attrs.description": 1}).sort("ts", -1).limit(10)

for pub in cursor:
    titre = pub.get("attrs", {}).get("titre", "")
    description = pub.get("attrs", {}).get("description", "")
    print(f"Titre : {titre}")
    print(f"Description : {description}")
    print("-")

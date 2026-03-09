#!/usr/bin/env python3
"""
VÉRIFICATION DES PUBLICATIONS ENRICHIES (SCORES SÉMANTIQUES)
Affiche un exemple brut de publication pour diagnostic
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

print("\n=== EXEMPLE BRUT DE PUBLICATION (MongoDB) ===\n")

# Cherche une publication avec ou sans score sémantique
pub = db.curated_observations.find_one({}, sort=[("ts", -1)])

if pub:
    pprint(pub)
else:
    print("Aucune publication trouvée dans la base.")

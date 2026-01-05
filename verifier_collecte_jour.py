#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vérification rapide de la collecte du jour"""

from pymongo import MongoClient
from datetime import datetime

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Date du jour
today = datetime.now().strftime('%Y-%m-%d')

# Comptage
count_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today
})

count_total = db.curated_observations.count_documents({'source': 'BRVM'})

print(f"📅 Date: {today}")
print(f"✅ Observations BRVM du jour: {count_today}")
print(f"📊 Total observations BRVM: {count_total}")

if count_today > 0:
    print(f"\n🎯 Collecte effectuée pour le {today}")
else:
    print(f"\n⚠️ Aucune donnée collectée pour le {today}")
    print("💡 Lancer: python mettre_a_jour_cours_brvm.py")

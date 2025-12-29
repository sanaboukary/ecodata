#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collecte quotidienne express - 26/12/2025"""

from pymongo import MongoClient
from datetime import datetime
import sys

print("="*80)
print("COLLECTE QUOTIDIENNE EXPRESS - 26/12/2025")
print("="*80)

# MongoDB
client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin')
db = client['centralisation_db']

print("\n26 décembre = Lendemain de Noël")
print("Le marché BRVM est probablement FERMÉ")
print("\nOptions:")
print("1. Utiliser données du 23/12 (dernière séance)")
print("2. Importer CSV si disponible")
print("3. Attendre réouverture (probablement 27/12)")

# Vérifier données disponibles
date_23 = "2025-12-23"
count_23 = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$regex': f'^{date_23}'}
})

print(f"\nDonnées 23/12: {count_23} observations")

if count_23 > 0:
    print("\n✅ Données du 23/12 déjà disponibles")
    print("   Recommandation: Utiliser ces données pour générer Top 5")
    print("\nCommandes:")
    print("  python top5_express.py      # Générer Top 5")
    print("  python valider_simple.py    # Valider recommandations")
else:
    print("\n⚠️  Pas de données récentes")
    print("   Action: Importer CSV historique")
    print("\nCommande:")
    print("  python collecter_csv_automatique.py")

# Stats globales
total = db.curated_observations.count_documents({'source': 'BRVM'})
symbols = len(db.curated_observations.distinct('key', {'source': 'BRVM'}))
dates = len(db.curated_observations.distinct('ts', {'source': 'BRVM'}))

print(f"\n" + "="*80)
print("STATISTIQUES MONGODB")
print("="*80)
print(f"Total observations: {total:,}")
print(f"Actions distinctes: {symbols}")
print(f"Jours de données:   {dates}")
print("="*80)

client.close()

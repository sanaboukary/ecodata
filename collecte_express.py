#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte Express - BRVM 24/12/2025
Option 1: Scraping automatique
Option 2: Import CSV rapide
Option 3: Utiliser données 23/12 (si marché fermé)
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys

print("=" * 80)
print("📦 COLLECTE EXPRESS BRVM - 24/12/2025")
print("=" * 80)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

today = datetime.now().strftime('%Y-%m-%d')
hier = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# Vérifier données aujourd'hui
count_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': today
})

count_hier = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': hier
})

print(f"\n📊 État actuel:")
print(f"   24/12/2025 : {count_today}/47 actions")
print(f"   23/12/2025 : {count_hier}/47 actions")
print()

if count_today >= 40:
    print("✅ Données du jour suffisantes !")
    print("   Vous pouvez lancer la validation directement.")
    print()
    print("   Commande: .venv/Scripts/python.exe workflow_quotidien_fiable.py")
    
elif count_today > 0:
    print(f"⚠️  Collecte partielle ({count_today} actions)")
    print("\n🚀 Options:")
    print("   1. Compléter la collecte (recommandé)")
    print("   2. Continuer avec les données partielles")
    print("   3. Utiliser données du 23/12")
    
else:
    print("❌ Aucune donnée aujourd'hui")
    
    # Vérifier si c'est un jour de marché
    jour_semaine = datetime.now().weekday()  # 0=Lundi, 6=Dimanche
    
    if jour_semaine in [5, 6]:  # Samedi ou Dimanche
        print("\n📅 WEEK-END DÉTECTÉ")
        print("   La BRVM est fermée le week-end")
        print(f"   Utilisation des données du 23/12 ({count_hier} actions)")
        
        if count_hier >= 30:
            print("\n✅ Les données du 23/12 sont utilisables pour validation")
            print("   Le validateur acceptera automatiquement J-1")
        else:
            print(f"\n⚠️  Données du 23/12 insuffisantes ({count_hier}/47)")
    
    else:
        print("\n🚀 OPTIONS DE COLLECTE:")
        print()
        print("Option A - Scraping automatique (si site accessible):")
        print("   .venv/Scripts/python.exe scripts/connectors/brvm_scraper_production.py")
        print()
        print("Option B - Import CSV (si vous avez un fichier CSV):")
        print("   .venv/Scripts/python.exe collecter_csv_automatique.py")
        print()
        print("Option C - Saisie manuelle rapide (5-10 minutes):")
        print("   .venv/Scripts/python.exe mettre_a_jour_cours_brvm.py")
        print()
        print("Option D - Utiliser données 23/12 (temporaire):")
        print("   Le validateur peut accepter J-1 si configuré")

print()
print("=" * 80)
print("📋 WORKFLOW RECOMMANDÉ:")
print("=" * 80)
print()

if count_today >= 30 or (count_today == 0 and count_hier >= 30):
    print("1. ✅ Données disponibles")
    print("2. 🎯 Lancer workflow: .venv/Scripts/python.exe workflow_quotidien_fiable.py")
    print("3. 📊 Obtenir recommandations validées")
    print("4. 💰 Trader avec stop-loss et position sizing")
else:
    print("1. 📦 Collecter données (choisir option A, B ou C ci-dessus)")
    print("2. 🎯 Lancer workflow: .venv/Scripts/python.exe workflow_quotidien_fiable.py")
    print("3. 📊 Obtenir recommandations validées")
    print("4. 💰 Trader avec stop-loss et position sizing")

print()
print("=" * 80)

client.close()

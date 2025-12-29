#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Diagnostic: Vérifier les cours BRVM actuels en base"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

client, db = get_mongo_db()

print("\n" + "="*80)
print("🔍 DIAGNOSTIC COURS BRVM EN BASE DE DONNÉES")
print("="*80 + "\n")

# Chercher les cours récents
today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

for date in [today, yesterday]:
    print(f"\n📅 Cours du {date}:")
    print("-" * 80)
    
    cours = list(db.curated_observations.find({
        'source': 'BRVM',
        'ts': date,
        'dataset': 'STOCK_PRICE'
    }).sort('key', 1))
    
    if not cours:
        print(f"  ❌ Aucun cours trouvé pour le {date}")
    else:
        print(f"  ✅ {len(cours)} actions trouvées\n")
        for c in cours[:10]:  # Afficher les 10 premiers
            quality = c.get('attrs', {}).get('data_quality', 'UNKNOWN')
            print(f"  {c['key']:10s} : {c['value']:10,.0f} FCFA   (Qualité: {quality})")
        
        if len(cours) > 10:
            print(f"  ... et {len(cours) - 10} autres actions")
        
        # Vérifier la qualité des données
        real_data = sum(1 for c in cours if c.get('attrs', {}).get('data_quality') in ['REAL_MANUAL', 'REAL_SCRAPER'])
        fake_data = len(cours) - real_data
        
        print(f"\n  📊 Qualité des données:")
        print(f"     - Données RÉELLES: {real_data}/{len(cours)} ({real_data/len(cours)*100:.1f}%)")
        print(f"     - Données SUSPECTES: {fake_data}/{len(cours)} ({fake_data/len(cours)*100:.1f}%)")

# Chercher le dernier cours ECOC pour vérifier
print(f"\n" + "="*80)
print("🔍 VÉRIFICATION ECOC (Ecobank Côte d'Ivoire)")
print("="*80)

ecoc_recent = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'ECOC'
}).sort('ts', -1).limit(5))

if ecoc_recent:
    print(f"\n Derniers cours ECOC en base:")
    for c in ecoc_recent:
        quality = c.get('attrs', {}).get('data_quality', 'UNKNOWN')
        print(f"  {c['ts']}: {c['value']:,.0f} FCFA (Qualité: {quality})")
    
    prix_actuel = ecoc_recent[0]['value']
    prix_reel = 15000
    ecart = abs(prix_actuel - prix_reel)
    ecart_pct = (ecart / prix_reel) * 100
    
    print(f"\n  🔴 PROBLÈME DÉTECTÉ:")
    print(f"     Prix en base: {prix_actuel:,.0f} FCFA")
    print(f"     Prix réel:    {prix_reel:,.0f} FCFA")
    print(f"     Écart:        {ecart:,.0f} FCFA ({ecart_pct:.1f}%)")
    
    if ecart_pct > 10:
        print(f"\n  ⚠️  ÉCART > 10% : DONNÉES NON FIABLES !")
else:
    print("  ❌ Aucun cours ECOC trouvé")

print(f"\n" + "="*80)
print("💡 SOLUTION:")
print("="*80)
print("""
1. OPTION A - Import CSV (RECOMMANDÉ):
   - Ouvrez: template_cours_brvm_22dec.csv
   - Remplissez avec les VRAIS cours de https://www.brvm.org
   - Exécutez: python importer_csv_cours_reels.py template_cours_brvm_22dec.csv

2. OPTION B - Saisie manuelle:
   - Éditez: mettre_a_jour_cours_REELS_22dec.py
   - Complétez le dictionnaire VRAIS_COURS_BRVM
   - Exécutez: python mettre_a_jour_cours_REELS_22dec.py

3. OPTION C - Scraping (si site accessible):
   - Créer le scraper brvm_scraper_production.py
   
⚠️  PRIORITÉ: Mettre à jour avec les VRAIS cours AVANT toute analyse !
""")
print("="*80 + "\n")

#!/usr/bin/env python3
import os, sys
from pathlib import Path
from datetime import datetime
import csv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*90)
print("                 RESTAURATION DONNÉES MANQUANTES")
print("="*90 + "\n")

fichiers = [
    ("donnees_brvm_2026-01-05.csv", "2026-01-05"),
    ("donnees_brvm_2026-01-09.csv", "2026-01-09"),
    ("donnees_brvm_2026-02-02.csv", "2026-02-02"),
]

total = 0

for fichier, date in fichiers:
    chemin = BASE_DIR / fichier
    if not chemin.exists():
        print(f"⏭️  {fichier} - Non trouvé")
        continue
    
    print(f"\n📁 {fichier} ({date})")
    
    try:
        with open(chemin, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported = 0
            
            for row in reader:
                ticker = row.get('Ticker', '').strip().upper()
                cours_str = row.get('Cours', '0')
                
                if not ticker:
                    continue
                
                try:
                    cours = float(cours_str)
                    if cours <= 0:
                        continue
                except:
                    continue
                
                doc = {
                    "source": "BRVM_CSV_RESTAURATION",
                    "dataset": "STOCK_PRICE",
                    "key": ticker,
                    "ts": date,
                    "timestamp": datetime.strptime(date, "%Y-%m-%d"),
                    "value": cours,
                    "attrs": {
                        "symbole": ticker,
                        "cours": cours,
                        "data_quality": "CSV_IMPORT",
                        "fichier_source": fichier
                    }
                }
                
                # Ajouter autres champs
                if 'Variation_%' in row and row['Variation_%']:
                    try:
                        doc['attrs']['variation_pct'] = float(row['Variation_%'])
                    except:
                        pass
                
                if 'Volume' in row and row['Volume']:
                    try:
                        doc['attrs']['volume'] = int(float(row['Volume']))
                    except:
                        pass
                
                if 'Ouv' in row and row['Ouv']:
                    try:
                        doc['attrs']['ouverture'] = float(row['Ouv'])
                    except:
                        pass
                
                if 'Haut' in row and row['Haut']:
                    try:
                        doc['attrs']['haut'] = float(row['Haut'])
                    except:
                        pass
                
                if 'Bas' in row and row['Bas']:
                    try:
                        doc['attrs']['bas'] = float(row['Bas'])
                    except:
                        pass
                
                db.curated_observations.update_one(
                    {
                        "source": "BRVM_CSV_RESTAURATION",
                        "dataset": "STOCK_PRICE",
                        "key": ticker,
                        "ts": date
                    },
                    {"$set": doc},
                    upsert=True
                )
                imported += 1
            
            print(f"   ✅ {imported} observations")
            total += imported
    
    except Exception as e:
        print(f"   ❌ Erreur : {e}")

print("\n" + "="*90)
print(f"📊 TOTAL IMPORTÉ : {total:,}\n")

# Vérifier
restored = db.curated_observations.count_documents({
    'source': 'BRVM_CSV_RESTAURATION',
    'dataset': 'STOCK_PRICE'
})
print(f"Données restaurées en base : {restored:,}")

total_global = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"TOTAL STOCK_PRICE : {total_global:,}")

print("\n" + "="*90 + "\n")

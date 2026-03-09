#!/usr/bin/env python3
"""
Restauration des données manquantes à partir des fichiers CSV trouvés
Période cible : 2025-12-13 → 2026-02-10
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*100)
print("                    RESTAURATION DONNÉES MANQUANTES")
print("="*100 + "\n")

# Fichiers CSV avec leur date associée
fichiers_a_importer = [
    ("donnees_brvm_2026-01-05.csv", "2026-01-05"),
    ("donnees_brvm_2026-01-09.csv", "2026-01-09"),
    ("donnees_brvm_2026-02-02.csv", "2026-02-02"),
    ("out_brvm/brvm_complet_20260105_110056.csv", "2026-01-05"),
]

total_imported = 0
fichiers_ok = 0

for fichier, date_collecte in fichiers_a_importer:
    chemin = BASE_DIR / fichier
    
    if not chemin.exists():
        print(f"⏭️  {fichier} - Fichier non trouvé")
        continue
    
    print(f"\n📁 {fichier}")
    print(f"   Date : {date_collecte}")
    
    try:
        # Lire le CSV
        df = pd.read_csv(chemin)
        
        # Identifier les colonnes
        ticker_col = None
        for col in ['Ticker', 'ticker', 'symbole', 'Symbole', 'SYM']:
            if col in df.columns:
                ticker_col = col
                break
        
        cours_col = None
        for col in ['Cours', 'cours', 'Cours Clôture (FCFA)', 'close', 'prix']:
            if col in df.columns:
                cours_col = col
                break
        
        if not ticker_col or not cours_col:
            print(f"   ❌ Colonnes manquantes (ticker ou cours)")
            continue
        
        # Nettoyer et importer
        imported = 0
        skipped = 0
        
        for _, row in df.iterrows():
            ticker = row.get(ticker_col)
            cours = row.get(cours_col)
            
            # Validation
            if not ticker or pd.isna(ticker) or not cours or pd.isna(cours):
                skipped += 1
                continue
            
            ticker = str(ticker).strip().upper()
            
            try:
                cours = float(cours)
            except:
                skipped += 1
                continue
            
            if cours <= 0:
                skipped += 1
                continue
            
            # Préparer le document
            doc = {
                "source": "BRVM_CSV_RESTAURATION",
                "dataset": "STOCK_PRICE",
                "key": ticker,
                "ts": date_collecte,
                "timestamp": datetime.strptime(date_collecte, "%Y-%m-%d"),
                "value": cours,
                "attrs": {
                    "symbole": ticker,
                    "cours": cours,
                    "data_quality": "CSV_IMPORT",
                    "fichier_source": fichier
                }
            }
            
            # Ajouter autres champs disponibles
            for col_name in df.columns:
                col_lower = col_name.lower()
                val = row.get(col_name)
                
                if pd.isna(val) or col_name == ticker_col or col_name == cours_col:
                    continue
                
                if 'variation' in col_lower or 'var' in col_lower:
                    try:
                        doc['attrs']['variation_pct'] = float(val)
                    except:
                        pass
                elif 'volume' in col_lower or 'vol' in col_lower:
                    try:
                        doc['attrs']['volume'] = int(float(val))
                    except:
                        pass
                elif 'ouv' in col_lower or 'open' in col_lower:
                    try:
                        doc['attrs']['ouverture'] = float(val)
                    except:
                        pass
                elif 'haut' in col_lower or 'high' in col_lower:
                    try:
                        doc['attrs']['haut'] = float(val)
                    except:
                        pass
                elif 'bas' in col_lower or 'low' in col_lower:
                    try:
                        doc['attrs']['bas'] = float(val)
                    except:
                        pass
                elif 'nom' in col_lower or 'libelle' in col_lower or 'libellé' in col_lower:
                    doc['attrs']['nom'] = str(val)
            
            # Insérer ou mettre à jour
            db.curated_observations.update_one(
                {
                    "source": "BRVM_CSV_RESTAURATION",
                    "dataset": "STOCK_PRICE",
                    "key": ticker,
                    "ts": date_collecte
                },
                {"$set": doc},
                upsert=True
            )
            imported += 1
        
        print(f"   ✅ {imported} observations importées, {skipped} ignorées")
        total_imported += imported
        fichiers_ok += 1
        
    except Exception as e:
        print(f"   ❌ Erreur : {e}")

# Résumé final
print("\n" + "="*100)
print("📊 RÉSUMÉ RESTAURATION :")
print("-"*100)
print(f"  Fichiers traités   : {fichiers_ok}/{len(fichiers_a_importer)}")
print(f"  Total importé      : {total_imported:,} observations")

# Vérifier l'état final
total_brvm_resto = db.curated_observations.count_documents({
    'source': 'BRVM_CSV_RESTAURATION',
    'dataset': 'STOCK_PRICE'
})

print(f"\n  Données restaurées en base : {total_brvm_resto:,}")

# Dates disponibles
dates = db.curated_observations.distinct('ts', {
    'source': 'BRVM_CSV_RESTAURATION',
    'dataset': 'STOCK_PRICE'
})
dates_sorted = sorted(dates)

if dates_sorted:
    print(f"  Dates : {', '.join(dates_sorted)}")

# Total global
total_global = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"\n  TOTAL STOCK_PRICE : {total_global:,}")

print("\n" + "="*100 + "\n")

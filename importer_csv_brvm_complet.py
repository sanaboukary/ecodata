#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import CSV complet BRVM - 47 actions avec toutes les données
Format attendu: TICKER,COURS,VARIATION_%,VOLUME,VALEUR,OUVERTURE,HAUT,BAS,SECTEUR
"""

import sys
import io
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

# Fix encodage
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 100)
print("📥 IMPORT CSV BRVM COMPLET")
print("=" * 100)
print()

# Chercher fichier CSV
import glob
csv_files = glob.glob('*.csv') + glob.glob('data/*.csv') + glob.glob('brvm_data/*.csv')
csv_brvm = [f for f in csv_files if 'brvm' in f.lower() or 'cours' in f.lower()]

if not csv_brvm:
    print("❌ Aucun fichier CSV trouvé")
    print()
    print("📋 Format CSV attendu (TOUTES COLONNES OPTIONNELLES):")
    print()
    print("TICKER,COURS,VARIATION_%,VOLUME,VALEUR,OUVERTURE,HAUT,BAS,PRECEDENT,SECTEUR,LIBELLE")
    print("SNTS,15500,2.3,8500,131750000,15400,15600,15350,15150,Telecommunications,SONATEL")
    print("SGBC,8200,-0.5,3200,26240000,8250,8300,8150,8241,Finance,SOGB")
    print("...")
    print()
    print("Créez un fichier 'brvm_cours_complet.csv' avec vos données et relancez.")
    sys.exit(1)

print(f"✅ Fichiers CSV trouvés: {len(csv_brvm)}")
for f in csv_brvm:
    print(f"   • {f}")
print()

# Utiliser le premier ou demander
csv_file = csv_brvm[0]
print(f"📂 Import: {csv_file}")
print()

# Lire CSV
try:
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"✅ {len(df)} lignes chargées")
    print(f"Colonnes: {list(df.columns)}")
    print()
    
    # Afficher aperçu
    print("Aperçu:")
    print(df.head(3).to_string(index=False))
    print()
    
except Exception as e:
    print(f"❌ Erreur lecture CSV: {e}")
    sys.exit(1)

# Normaliser colonnes
col_map = {
    'TICKER': 'Ticker', 'SYMBOL': 'Ticker', 'SYMBOLE': 'Ticker', 'ticker': 'Ticker',
    'COURS': 'Cours', 'CLOSE': 'Cours', 'PRIX': 'Cours', 'DERNIER': 'Cours',
    'VARIATION_%': 'Variation_%', 'VARIATION_PCT': 'Variation_%', 'VAR_%': 'Variation_%',
    'VOLUME': 'Volume', 'VOL': 'Volume',
    'VALEUR': 'Valeur', 'VALUE': 'Valeur',
    'OUVERTURE': 'Ouverture', 'OPEN': 'Ouverture',
    'HAUT': 'Haut', 'HIGH': 'Haut',
    'BAS': 'Bas', 'LOW': 'Bas',
    'PRECEDENT': 'Precedent', 'PREVIOUS': 'Precedent',
    'SECTEUR': 'Secteur', 'SECTOR': 'Secteur',
    'LIBELLE': 'Libelle', 'NAME': 'Libelle', 'NOM': 'Libelle',
}

df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})

# Nettoyer
if 'Ticker' in df.columns:
    df['Ticker'] = df['Ticker'].astype(str).str.strip().str.upper()
else:
    print("❌ Colonne TICKER manquante")
    sys.exit(1)

# MongoDB
print("💾 Sauvegarde MongoDB...")
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

date_str = datetime.now().strftime('%Y-%m-%d')
saved = 0

for _, row in df.iterrows():
    ticker = row.get('Ticker')
    cours = row.get('Cours')
    
    if pd.notna(ticker) and pd.notna(cours):
        obs = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE_COMPLET',
            'key': str(ticker),
            'ts': date_str,
            'value': float(cours),
            'attrs': {
                'data_quality': 'REAL_MANUAL',
                'import_source': 'CSV',
                'cours': float(cours),
                'variation_pct': float(row.get('Variation_%')) if pd.notna(row.get('Variation_%')) else None,
                'volume': float(row.get('Volume')) if pd.notna(row.get('Volume')) else None,
                'valeur': float(row.get('Valeur')) if pd.notna(row.get('Valeur')) else None,
                'ouverture': float(row.get('Ouverture')) if pd.notna(row.get('Ouverture')) else None,
                'haut': float(row.get('Haut')) if pd.notna(row.get('Haut')) else None,
                'bas': float(row.get('Bas')) if pd.notna(row.get('Bas')) else None,
                'precedent': float(row.get('Precedent')) if pd.notna(row.get('Precedent')) else None,
                'secteur': str(row.get('Secteur', '')),
                'libelle': str(row.get('Libelle', '')),
            }
        }
        
        db.curated_observations.update_one(
            {'source': 'BRVM', 'key': ticker, 'ts': date_str},
            {'$set': obs},
            upsert=True
        )
        saved += 1

print()
print("=" * 100)
print(f"✅ {saved} actions importées dans MongoDB")
print("=" * 100)

client.close()

#!/usr/bin/env python3
"""
RESTAURATION COMPLETE - ACCEPTE TOUS LES SYMBOLES BRVM REELS
Sans filtrage arbitraire - importe toutes les données historiques
"""

import pandas as pd
import pymongo
from datetime import datetime

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("RESTAURATION BRVM")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

# Compter avant
avant = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"Avant: {avant} observations Stock")

# Clés existantes 
keys = set(db.curated_observations.distinct('key', {'dataset': 'STOCK_PRICE'}))

fichiers = [
    ('historique_brvm.csv', 'Historique sept-nov 2025'),
    ('historique_brvm_complement_nov_dec.csv', 'Complement nov-dec 2025'),
    ('donnees_reelles_brvm.csv', 'Donnees reelles dec 2025')
]

total_imports = 0
total_doublons = 0

for path, desc in fichiers:
    print(f"\n[{path}]")
    try:
        df = pd.read_csv(path)
        print(f"  Lignes: {len(df)}")
        
        imports = 0
        doublons = 0
        
        for _, row in df.iterrows():
            date = str(row['DATE'])
            symbol = str(row['SYMBOL'])
            
            # Ignorer si symbole vide  
            if not symbol or symbol == 'nan':
                continue
            
            key = f"{symbol}_{date}"
            
            # Skip doublon
            if key in keys:
                doublons += 1
                continue
            
            # Créer observation
            obs = {
                'key': key,
                'source': 'BRVM_CSV_HISTORIQUE',
                'ts': date,
                'dataset': 'STOCK_PRICE',
                'ticker': symbol,
                'value': float(row['CLOSE']) if pd.notna(row['CLOSE']) else 0.0,
                'attrs': {
                    'close': float(row['CLOSE']) if pd.notna(row['CLOSE']) else 0.0,
                    'volume': int(row['VOLUME']) if pd.notna(row['VOLUME']) else 0,
                    'variation': float(row['VARIATION']) if pd.notna(row['VARIATION']) else 0.0,
                    'source_file': path
                }
            }
            
            db.curated_observations.insert_one(obs)
            keys.add(key)
            imports += 1
        
        total_imports += imports
        total_doublons += doublons
        
        print(f"  Importes: {imports}")
        if doublons > 0:
            print(f"  Doublons evites: {doublons}")
        
    except Exception as e:
        print(f"  ERREUR: {e}")

# Compter après
apres = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
tickers = db.curated_observations.distinct('ticker', {'dataset': 'STOCK_PRICE'})
tickers_valides = [t for t in tickers if t and t != 'None']

print(f"\n===========================")
print(f"RESULTAT")
print(f"===========================")
print(f"Avant: {avant}")
print(f"Apres: {apres}")
print(f"Gain: +{apres - avant}")
print(f"Imports: {total_imports}")
print(f"Doublons evites: {total_doublons}")
print(f"Tickers: {len(tickers_valides)} actions")
print(f"\n{sorted(tickers_valides)[:20]}")

client.close()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Afficher données BRVM collectées aujourd'hui."""

import sys
import io
from datetime import datetime
from pymongo import MongoClient
import pandas as pd

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

# Date du jour
date_aujourdhui = datetime.now().strftime('%Y-%m-%d')

print("=" * 100)
print(f"📊 DONNÉES BRVM COLLECTÉES LE {date_aujourdhui}")
print("=" * 100)
print()

# Récupérer toutes les observations du jour
observations = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': date_aujourdhui
}).sort('key', 1))

if not observations:
    print("❌ Aucune donnée collectée aujourd'hui")
    print()
    print("Dernière collecte:")
    last_obs = list(db.curated_observations.find({'source': 'BRVM'}).sort('ts', -1).limit(1))
    if last_obs:
        print(f"   Date: {last_obs[0]['ts']}")
        print(f"   Actions: {db.curated_observations.count_documents({'source': 'BRVM', 'ts': last_obs[0]['ts']})}")
    else:
        print("   Aucune donnée BRVM dans la base")
    sys.exit(1)

print(f"✅ {len(observations)} actions collectées")
print()

# Créer DataFrame
data = []
for obs in observations:
    attrs = obs.get('attrs', {})
    data.append({
        'Ticker': obs['key'],
        'Libellé': attrs.get('libelle', '')[:30],
        'Cours': obs['value'],
        'Variation_%': attrs.get('variation_pct'),
        'Volatilité_%': attrs.get('volatilite_pct'),
        'Volume': attrs.get('volume'),
        'Liquidité': attrs.get('liquidite_moyenne'),
        'Ouv': attrs.get('ouverture'),
        'Haut': attrs.get('haut'),
        'Bas': attrs.get('bas'),
        'Cap.(M)': attrs.get('capitalisation', 0) / 1_000_000 if attrs.get('capitalisation') else None,
        'Secteur': attrs.get('secteur', '')[:20]
    })

df = pd.DataFrame(data)

# Afficher tableau complet
print("TABLEAU COMPLET:")
print("=" * 100)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 150)
pd.set_option('display.float_format', lambda x: f'{x:,.2f}' if pd.notna(x) else '-')
print(df.to_string(index=False))
print()

# Statistiques
print("=" * 100)
print("📈 STATISTIQUES:")
print("=" * 100)
print(f"Total actions: {len(df)}")
print(f"Avec variation: {df['Variation_%'].notna().sum()}")
print(f"Avec volatilité: {(df['Volatilité_%'] > 0).sum()}")
print(f"Avec volume: {(df['Volume'] > 0).sum()}")
print()

if df['Variation_%'].notna().sum() > 0:
    print("TOP 5 HAUSSES:")
    top5_hausse = df.nlargest(5, 'Variation_%')[['Ticker', 'Libellé', 'Cours', 'Variation_%']]
    print(top5_hausse.to_string(index=False))
    print()
    
    print("TOP 5 BAISSES:")
    top5_baisse = df.nsmallest(5, 'Variation_%')[['Ticker', 'Libellé', 'Cours', 'Variation_%']]
    print(top5_baisse.to_string(index=False))
    print()

if (df['Volume'] > 0).sum() > 0:
    print("TOP 5 VOLUMES:")
    top5_vol = df.nlargest(5, 'Volume')[['Ticker', 'Libellé', 'Volume', 'Cours']]
    print(top5_vol.to_string(index=False))
    print()

if (df['Volatilité_%'] > 0).sum() > 0:
    print("TOP 5 VOLATILITÉ:")
    top5_vol = df.nlargest(5, 'Volatilité_%')[['Ticker', 'Libellé', 'Volatilité_%', 'Variation_%']]
    print(top5_vol.to_string(index=False))
    print()

print("=" * 100)

# Export CSV
csv_file = f"donnees_brvm_{date_aujourdhui}.csv"
df.to_csv(csv_file, index=False, encoding='utf-8-sig')
print(f"💾 Export CSV: {csv_file}")
print("=" * 100)

client.close()

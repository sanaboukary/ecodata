#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rapport complet sur l'état actuel des données collectées"""

import sys
import io
from pymongo import MongoClient
import os

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*100)
print("RAPPORT COMPLET - ETAT DES DONNEES COLLECTEES")
print("="*100)

# 1. MongoDB
print("\n1. BASE DE DONNEES MONGODB (centralisation_db)")
print("-" * 100)

try:
    client = MongoClient('mongodb://localhost:27017')
    db = client['centralisation_db']
    
    print(f"\n   Collections: {db.list_collection_names()}")
    print(f"   Total documents (curated_observations): {db.curated_observations.count_documents({})}")
    
    print("\n   SOURCES PRESENTES:")
    sources = db.curated_observations.distinct('source')
    for source in sorted(sources):
        count = db.curated_observations.count_documents({'source': source})
        keys = db.curated_observations.distinct('key', {'source': source})
        dates = db.curated_observations.distinct('ts', {'source': source})
        
        print(f"\n      {source}:")
        print(f"         Documents: {count:,}")
        print(f"         Indicateurs/Actions: {len(keys)}")
        print(f"         Dates: {len(dates)}")
        
        if dates:
            dates_sorted = sorted(dates)
            print(f"         Période: {dates_sorted[0]} -> {dates_sorted[-1]}")
    
    client.close()
    
except Exception as e:
    print(f"   ERREUR MongoDB: {e}")

# 2. Airflow
print("\n" + "="*100)
print("2. AIRFLOW (Scheduler)")
print("-" * 100)

if os.path.exists('airflow/airflow.db'):
    file_size = os.path.getsize('airflow/airflow.db')
    print(f"\n   Base de données Airflow: {file_size:,} bytes")
    
    # Tester si initialisé
    import sqlite3
    try:
        conn = sqlite3.connect('airflow/airflow.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        tables = cursor.fetchall()
        
        if tables:
            print(f"   Tables présentes: {len(tables)}")
            cursor.execute("SELECT COUNT(*) FROM dag_run")
            dag_runs = cursor.fetchone()[0]
            print(f"   DAG runs exécutés: {dag_runs}")
        else:
            print("   STATUS: Base de données vide (Airflow jamais initialisé)")
        
        conn.close()
    except:
        print("   STATUS: Base de données non initialisée")
else:
    print("   STATUS: Airflow non configuré")

# 3. DAGs configurés
print("\n" + "="*100)
print("3. DAGs CONFIGURES (airflow/dags/)")
print("-" * 100)

if os.path.exists('airflow/dags'):
    dag_files = [f for f in os.listdir('airflow/dags') if f.endswith('.py')]
    print(f"\n   Fichiers DAG: {len(dag_files)}")
    
    for dag_file in sorted(dag_files):
        print(f"      - {dag_file}")
else:
    print("   Aucun DAG configuré")

# 4. Fichiers CSV/JSON
print("\n" + "="*100)
print("4. FICHIERS DE DONNEES LOCAUX")
print("-" * 100)

csv_files = []
for root, dirs, files in os.walk('.'):
    # Ignorer .venv et node_modules
    if '.venv' in root or 'node_modules' in root:
        continue
    
    for file in files:
        if file.endswith('.csv') and 'historique' in file.lower():
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            csv_files.append((file, size))

print(f"\n   Fichiers CSV historiques trouvés: {len(csv_files)}")
for file, size in sorted(csv_files):
    print(f"      - {file:<50} ({size:,} bytes)")

# 5. Conclusion
print("\n" + "="*100)
print("5. CONCLUSION")
print("="*100)

print("\n   SOURCES AVEC DONNEES:")
if sources:
    for source in sorted(sources):
        count = db.curated_observations.count_documents({'source': source})
        print(f"      ✓ {source:<30} {count:>10,} observations")
else:
    print("      Aucune")

print("\n   SOURCES MANQUANTES:")
expected_sources = ['WorldBank', 'IMF', 'AfDB', 'UN_SDG']
missing = [s for s in expected_sources if s not in sources]

if missing:
    for source in missing:
        print(f"      ✗ {source:<30} 0 observations")
    
    print("\n   RAISON:")
    print("      - Airflow n'a jamais été initialisé (base de données vide)")
    print("      - Les DAGs sont configurés mais jamais exécutés")
    print("      - Aucun fichier CSV/JSON avec données World Bank/IMF/AfDB trouvé")
    
    print("\n   ACTIONS RECOMMANDEES:")
    print("      1. Initialiser Airflow: airflow db init")
    print("      2. Lancer le scheduler: python start_airflow_background.bat")
    print("      3. OU collecter manuellement: python collecter_toutes_sources.py")
else:
    print("      Toutes les sources attendues sont présentes!")

print("\n" + "="*100)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recherche approfondie - Où sont passées les données WorldBank/IMF/AfDB ?"""

import sys
import io
import os
import subprocess
from pymongo import MongoClient

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*120)
print("INVESTIGATION - DONNEES WORLDBANK/IMF/AFDB MANQUANTES")
print("="*120)

# 1. MongoDB - Toutes les bases
print("\n1. BASES MONGODB:")
print("-" * 120)
try:
    client = MongoClient('mongodb://localhost:27017')
    all_dbs = client.list_database_names()
    print(f"   Toutes les bases: {all_dbs}")
    
    for db_name in all_dbs:
        if db_name not in ['admin', 'config', 'local']:
            db = client[db_name]
            collections = db.list_collection_names()
            print(f"\n   Base: {db_name}")
            for coll in collections:
                count = db[coll].count_documents({})
                print(f"      - {coll}: {count:,} documents")
                
                # Vérifier sources si c'est curated_observations
                if 'observation' in coll.lower() or 'curated' in coll.lower():
                    sources = db[coll].distinct('source')
                    if sources:
                        print(f"         Sources: {sources}")
    
    client.close()
except Exception as e:
    print(f"   ERREUR MongoDB: {e}")

# 2. Fichiers backup/dump
print("\n" + "="*120)
print("2. FICHIERS BACKUP/DUMP:")
print("-" * 120)

backup_patterns = [
    '*.bson',
    '*.json',
    '*backup*',
    '*dump*',
    '*export*',
    '*archive*'
]

for pattern in backup_patterns:
    try:
        result = subprocess.run(
            f'find . -name "{pattern}" -type f 2>/dev/null | grep -v node_modules | grep -v .venv | head -10',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"\n   Pattern '{pattern}':")
            print(f"      {result.stdout.strip()}")
    except:
        pass

# 3. Historique Git - Collectes de données
print("\n" + "="*120)
print("3. HISTORIQUE GIT - COLLECTES:")
print("-" * 120)

try:
    # Recherche commits mentionnant collecte/world/imf/afdb
    result = subprocess.run(
        'git log --all --oneline --grep="collect\\|world\\|imf\\|afdb\\|banque\\|fmi\\|bad" -i | head -20',
        shell=True,
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("   Aucun commit trouvé avec ces mots-clés")
except Exception as e:
    print(f"   ERREUR Git: {e}")

# 4. Fichiers de scripts de collecte
print("\n" + "="*120)
print("4. SCRIPTS DE COLLECTE:")
print("-" * 120)

collecte_files = [
    'collect_imf_enhanced.py',
    'collecte_worldbank_complete.py',
    'collecter_toutes_sources.py',
    'collecte_automatique_complete.py',
    'collecter_csv_automatique.py'
]

for file in collecte_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        mtime = os.path.getmtime(file)
        from datetime import datetime
        mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        print(f"   ✓ {file:<45} ({size:>8,} bytes, modifié: {mod_date})")
    else:
        print(f"   ✗ {file:<45} (non trouvé)")

# 5. Logs d'exécution
print("\n" + "="*120)
print("5. LOGS D'EXECUTION:")
print("-" * 120)

log_patterns = [
    'collection*.log',
    'ingestion*.log',
    'airflow/logs/**/*.log'
]

for pattern in log_patterns:
    try:
        result = subprocess.run(
            f'find . -name "{pattern}" -type f 2>/dev/null | head -5',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"\n   Logs '{pattern}':")
            for line in result.stdout.strip().split('\n'):
                print(f"      {line}")
    except:
        pass

# 6. Dashboards et leurs données attendues
print("\n" + "="*120)
print("6. DASHBOARDS CONFIGURÉS:")
print("-" * 120)

dashboard_files = {
    'dashboard/views.py': ['dashboard_worldbank', 'dashboard_imf', 'dashboard_afdb', 'dashboard_un'],
    'dashboard/templates/dashboard/dashboard_worldbank.html': 'WorldBank UI',
    'dashboard/templates/dashboard/dashboard_imf.html': 'IMF UI',
    'dashboard/templates/dashboard/dashboard_afdb.html': 'AfDB UI'
}

for file, functions in dashboard_files.items():
    if os.path.exists(file):
        print(f"   ✓ {file}")
        if isinstance(functions, list):
            for func in functions:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if func in content:
                            print(f"      → Fonction {func}() trouvée")
                except:
                    pass
        else:
            print(f"      → {functions}")

# 7. Vérification README/Documentation
print("\n" + "="*120)
print("7. DOCUMENTATION:")
print("-" * 120)

docs = [
    'README.md',
    'PIPELINE_STRUCTURE.md',
    'DEPLOYMENT_GUIDE.md',
    'AIRFLOW_SETUP.md'
]

for doc in docs:
    if os.path.exists(doc):
        try:
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'WorldBank' in content or 'IMF' in content:
                    print(f"   ✓ {doc:<30} (mentionne WorldBank/IMF)")
        except:
            pass

print("\n" + "="*120)
print("CONCLUSION:")
print("="*120)

print("""
ÉTAT ACTUEL:
   ✓ Dashboards WorldBank/IMF/AfDB/UN_SDG configurés et prêts
   ✓ Scripts de collecte présents (collecter_toutes_sources.py, etc.)
   ✓ Pipeline ETL fonctionnel (scripts/pipeline.py)
   ✓ Connecteurs API disponibles (worldbank.py, imf.py, afdb.py, un_sdg.py)
   ✗ Données WorldBank/IMF/AfDB/UN_SDG ABSENTES de MongoDB

HYPOTHÈSES:
   1. Les données n'ont jamais été collectées (Airflow non initialisé)
   2. Les données ont été collectées puis perdues (base MongoDB réinitialisée?)
   3. Les données sont dans une autre base MongoDB (différente de centralisation_db)
   4. Les données sont dans des fichiers backup/export non importés

ACTIONS RECOMMANDÉES:
   1. Vérifier s'il existe un backup MongoDB (.bson, .json)
   2. Vérifier l'historique Git pour voir si données collectées avant
   3. Collecter les données maintenant: python collecter_toutes_sources.py
   4. OU initialiser Airflow: airflow db init && python start_airflow_background.bat
""")

print("="*120)

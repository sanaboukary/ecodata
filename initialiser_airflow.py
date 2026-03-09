#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialisation et lancement d'Airflow pour collecte automatique"""

import os
import sys
import subprocess
import time

# Configuration Airflow
AIRFLOW_HOME = os.path.join(os.getcwd(), 'airflow')
os.environ['AIRFLOW_HOME'] = AIRFLOW_HOME

print("="*100)
print("INITIALISATION AIRFLOW - Collecte automatique toutes sources")
print("="*100)

print(f"\nAIRFLOW_HOME: {AIRFLOW_HOME}")

# 1. Initialiser la base de données Airflow
print("\n1. INITIALISATION BASE DE DONNÉES AIRFLOW...")
print("-" * 100)

try:
    result = subprocess.run(
        ['airflow', 'db', 'init'],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("✓ Base de données Airflow initialisée")
    else:
        print(f"Sortie: {result.stdout[-500:]}")
        if "already exists" in result.stderr or "already initialized" in result.stdout:
            print("✓ Base de données déjà initialisée")
        else:
            print(f"Erreur: {result.stderr[-500:]}")
            
except subprocess.TimeoutExpired:
    print("✓ Initialisation en cours (peut prendre du temps)...")
except Exception as e:
    print(f"Erreur: {e}")

# 2. Créer utilisateur admin (si pas existant)
print("\n2. CRÉATION UTILISATEUR ADMIN...")
print("-" * 100)

try:
    result = subprocess.run(
        [
            'airflow', 'users', 'create',
            '--username', 'admin',
            '--password', 'admin',
            '--firstname', 'Admin',
            '--lastname', 'User',
            '--role', 'Admin',
            '--email', 'admin@example.com'
        ],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✓ Utilisateur admin créé")
        print("   Username: admin")
        print("   Password: admin")
    elif "already exists" in result.stderr:
        print("✓ Utilisateur admin existe déjà")
    else:
        print(f"Info: {result.stderr[:200]}")
        
except Exception as e:
    print(f"Info: {e}")

# 3. Vérifier les DAGs
print("\n3. VÉRIFICATION DAGs...")
print("-" * 100)

dags_dir = os.path.join(AIRFLOW_HOME, 'dags')
if os.path.exists(dags_dir):
    dag_files = [f for f in os.listdir(dags_dir) if f.endswith('.py')]
    print(f"✓ Dossier DAGs: {dags_dir}")
    print(f"✓ {len(dag_files)} DAGs trouvés:")
    for dag_file in sorted(dag_files):
        print(f"   - {dag_file}")
else:
    print(f"✗ Dossier DAGs non trouvé: {dags_dir}")

# 4. Lister les DAGs disponibles
print("\n4. DAGs DISPONIBLES DANS AIRFLOW...")
print("-" * 100)

try:
    result = subprocess.run(
        ['airflow', 'dags', 'list'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        # Filtrer les DAGs pertinents
        lines = result.stdout.split('\n')
        relevant_dags = [l for l in lines if any(k in l.lower() for k in ['world', 'imf', 'afdb', 'brvm', 'master'])]
        
        if relevant_dags:
            print("DAGs de collecte détectés:")
            for line in relevant_dags:
                print(f"   {line}")
        else:
            print("Tous les DAGs:")
            print(result.stdout[:500])
            
except Exception as e:
    print(f"Erreur: {e}")

# 5. Dépauser les DAGs principaux
print("\n5. ACTIVATION DES DAGs...")
print("-" * 100)

dags_to_unpause = [
    'worldbank_data_collection',
    'imf_data_collection', 
    'afdb_un_data_collection',
    'brvm_complete_daily',
    'master_complete_dag'
]

for dag_id in dags_to_unpause:
    try:
        result = subprocess.run(
            ['airflow', 'dags', 'unpause', dag_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✓ DAG activé: {dag_id}")
        else:
            # Vérifier si DAG existe
            if "not found" in result.stderr.lower():
                print(f"  DAG non trouvé: {dag_id}")
            else:
                print(f"  {dag_id}: {result.stderr[:100]}")
                
    except Exception as e:
        print(f"  {dag_id}: {e}")

print("\n" + "="*100)
print("INITIALISATION TERMINÉE")
print("="*100)

print("""
PROCHAINES ÉTAPES:

1. Lancer Airflow Scheduler (collecteur automatique):
   python lancer_airflow_scheduler.py

2. Lancer Airflow Webserver (interface web):
   python lancer_airflow_webserver.py
   
3. Accéder à l'interface: http://localhost:8080
   Username: admin
   Password: admin

4. Déclencher manuellement un DAG:
   airflow dags trigger worldbank_data_collection
   airflow dags trigger imf_data_collection
   
5. Vérifier les données collectées:
   python voir_donnees.py
""")

print("="*100)

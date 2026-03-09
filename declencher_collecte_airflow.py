#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Déclenchement manuel des DAGs pour collecte immédiate"""

import os
import subprocess
import time

AIRFLOW_HOME = os.path.join(os.getcwd(), 'airflow')
os.environ['AIRFLOW_HOME'] = AIRFLOW_HOME

print("="*100)
print("DÉCLENCHEMENT MANUEL - COLLECTE TOUTES SOURCES")
print("="*100)

dags_to_trigger = [
    ('worldbank_data_collection', 'World Bank - Indicateurs économiques'),
    ('imf_data_collection', 'IMF - Séries monétaires'),
    ('afdb_un_data_collection', 'AfDB + UN SDG - Développement'),
    ('brvm_complete_daily', 'BRVM - Bourse + Publications')
]

print("\nDéclenchement des DAGs de collecte...\n")

for dag_id, description in dags_to_trigger:
    print(f"► {description}")
    print(f"  DAG: {dag_id}")
    
    try:
        result = subprocess.run(
            ['airflow', 'dags', 'trigger', dag_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"  ✓ Déclenché avec succès")
            # Extraire le run_id si disponible
            if "Created" in result.stdout:
                print(f"  {result.stdout.split('Created')[1].strip()[:100]}")
        else:
            if "not found" in result.stderr.lower():
                print(f"  ⚠ DAG non trouvé (peut-être pas encore chargé)")
            else:
                print(f"  ✗ Erreur: {result.stderr[:200]}")
                
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
    
    print()
    time.sleep(1)

print("="*100)
print("\nPour suivre l'exécution:")
print("  1. Interface web: http://localhost:8080")
print("  2. Logs: airflow/logs/")
print("  3. Commande: airflow dags list-runs")
print("\nPour vérifier les données collectées:")
print("  python voir_donnees.py")
print("="*100)

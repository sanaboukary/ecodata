#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifier l'historique des DAGs Airflow dans la base SQLite"""

import sqlite3
import sys
import io

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = 'airflow/airflow.db'

print("="*100)
print("VERIFICATION HISTORIQUE AIRFLOW")
print("="*100)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Lister tous les DAGs
    print("\n1. DAGs ENREGISTRES:")
    print("-" * 100)
    cursor.execute("SELECT dag_id, is_active, is_paused FROM dag ORDER BY dag_id")
    dags = cursor.fetchall()
    
    if dags:
        print(f"{'DAG ID':<50} {'Active':<10} {'Paused':<10}")
        print("-" * 100)
        for dag_id, active, paused in dags:
            print(f"{dag_id:<50} {str(active):<10} {str(paused):<10}")
    else:
        print("   Aucun DAG trouvé")
    
    # 2. Historique des exécutions (dag_run)
    print("\n2. HISTORIQUE EXECUTIONS (DAG RUNS):")
    print("-" * 100)
    cursor.execute("""
        SELECT dag_id, execution_date, state, start_date, end_date 
        FROM dag_run 
        ORDER BY execution_date DESC 
        LIMIT 50
    """)
    runs = cursor.fetchall()
    
    if runs:
        print(f"{'DAG ID':<40} {'Execution Date':<20} {'State':<15} {'Start':<20}")
        print("-" * 100)
        for dag_id, exec_date, state, start, end in runs:
            exec_str = str(exec_date)[:19] if exec_date else 'N/A'
            start_str = str(start)[:19] if start else 'N/A'
            print(f"{dag_id:<40} {exec_str:<20} {state:<15} {start_str:<20}")
    else:
        print("   Aucune exécution trouvée")
    
    # 3. Recherche DAGs World Bank, IMF, AfDB
    print("\n3. RECHERCHE DAGs ECONOMIQUES:")
    print("-" * 100)
    
    keywords = ['worldbank', 'imf', 'afdb', 'un_sdg', 'world_bank']
    for keyword in keywords:
        cursor.execute(f"SELECT dag_id, is_paused FROM dag WHERE dag_id LIKE '%{keyword}%'")
        results = cursor.fetchall()
        if results:
            print(f"\n   '{keyword}':")
            for dag_id, paused in results:
                status = "PAUSED" if paused else "ACTIVE"
                print(f"      {dag_id:<60} {status}")
                
                # Nombre d'exécutions
                cursor.execute("SELECT COUNT(*) FROM dag_run WHERE dag_id = ?", (dag_id,))
                count = cursor.fetchone()[0]
                print(f"         Exécutions: {count}")
    
    # 4. Task instances pour sources économiques
    print("\n4. TASK INSTANCES (COLLECTE DONNEES):")
    print("-" * 100)
    cursor.execute("""
        SELECT DISTINCT dag_id, task_id, state, execution_date 
        FROM task_instance 
        WHERE dag_id LIKE '%worldbank%' OR dag_id LIKE '%imf%' OR dag_id LIKE '%afdb%'
        ORDER BY execution_date DESC 
        LIMIT 20
    """)
    tasks = cursor.fetchall()
    
    if tasks:
        print(f"{'DAG ID':<40} {'Task ID':<30} {'State':<15} {'Date':<20}")
        print("-" * 100)
        for dag_id, task_id, state, exec_date in tasks:
            exec_str = str(exec_date)[:19] if exec_date else 'N/A'
            print(f"{dag_id:<40} {task_id:<30} {state:<15} {exec_str:<20}")
    else:
        print("   Aucune task instance trouvée pour les sources économiques")
    
    conn.close()
    
except Exception as e:
    print(f"\nERREUR: {e}")
    print("\nAirflow n'a peut-être jamais été initialisé ou la base de données est corrompue")

print("\n" + "="*100)
print("FIN VERIFICATION")
print("="*100)

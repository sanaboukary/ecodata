#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lancement du Scheduler Airflow en arrière-plan"""

import os
import sys
import subprocess
import time

AIRFLOW_HOME = os.path.join(os.getcwd(), 'airflow')
os.environ['AIRFLOW_HOME'] = AIRFLOW_HOME

print("="*100)
print("LANCEMENT AIRFLOW SCHEDULER")
print("="*100)

print(f"\nAIRFLOW_HOME: {AIRFLOW_HOME}")
print("Le scheduler va collecter automatiquement les données selon les DAGs programmés")
print("\nAppuyez sur Ctrl+C pour arrêter...")
print("-" * 100)

try:
    # Lancer le scheduler
    subprocess.run(
        ['airflow', 'scheduler'],
        cwd=os.getcwd()
    )
except KeyboardInterrupt:
    print("\n\nScheduler arrêté par l'utilisateur")
except Exception as e:
    print(f"\nErreur: {e}")

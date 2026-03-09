#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lancement du Webserver Airflow (interface web)"""

import os
import sys
import subprocess

AIRFLOW_HOME = os.path.join(os.getcwd(), 'airflow')
os.environ['AIRFLOW_HOME'] = AIRFLOW_HOME

print("="*100)
print("LANCEMENT AIRFLOW WEBSERVER")
print("="*100)

print(f"\nAIRFLOW_HOME: {AIRFLOW_HOME}")
print("\nInterface web: http://localhost:8080")
print("Username: admin")
print("Password: admin")
print("\nAppuyez sur Ctrl+C pour arrêter...")
print("-" * 100)

try:
    # Lancer le webserver
    subprocess.run(
        ['airflow', 'webserver', '--port', '8080'],
        cwd=os.getcwd()
    )
except KeyboardInterrupt:
    print("\n\nWebserver arrêté par l'utilisateur")
except Exception as e:
    print(f"\nErreur: {e}")

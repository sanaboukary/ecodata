#!/usr/bin/env python3
"""
WORKFLOW COMPLET BRVM - Production Ready
=========================================

Génération → TOP5 → Dashboard
Sans emojis, logs fichier, production-ready
"""

import subprocess
import sys

PYTHON = sys.executable

print("\n" + "="*70)
print(" WORKFLOW COMPLET BRVM ".center(70))
print("="*70 + "\n")

# ÉTAPE 1 : Génération décisions
print("[ETAPE 1/3] Generation decisions BUY...")
result = subprocess.run([PYTHON, "generer_avec_log.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"ERREUR: {result.stderr}")
    sys.exit(1)

# ÉTAPE 2 : TOP5 ENGINE
print("\n[ETAPE 2/3] Classement TOP5...")
result = subprocess.run([PYTHON, "top5_engine_final.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"ERREUR: {result.stderr}")
    sys.exit(1)

# ÉTAPE 3 : Dashboard
print("\n[ETAPE 3/3] Affichage dashboard...")
result = subprocess.run([PYTHON, "dashboard_recommandations.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"ERREUR: {result.stderr}")
    sys.exit(1)

print("\n" + "="*70)
print(" WORKFLOW TERMINE ".center(70))
print("="*70 + "\n")

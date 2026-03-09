#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE BRVM SIMPLIFIÉ - Windows Compatible
=============================================

Exécution complète: Collecte → Analyse → Recommandations DUAL MOTOR

UTILISATION:
  python pipeline_brvm_simple.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
PYTHON = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")

print("\n" + "="*80)
print("PIPELINE BRVM - SYSTEME DUAL MOTOR")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

def run_command(title, cmd, required=True):
    """Exécute une commande"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=str(BASE_DIR), timeout=300)
        
        if result.returncode != 0:
            print(f"\n[ERREUR] Code: {result.returncode}")
            if required:
                print(f"[ARRET] Etape critique echouee")
                sys.exit(1)
            else:
                print(f"[WARNING] Continuation malgre erreur")
                return False
        else:
            print(f"\n[OK] Etape terminee")
            return True
            
    except Exception as e:
        print(f"\n[EXCEPTION] {e}")
        if required:
            sys.exit(1)
        return False

# PIPELINE
print("Etapes du pipeline:")
print("1. Enrichissement metriques experts")
print("2. Analyse technique IA")  
print("3. Decision WOS STABLE")
print("4. Decision EXPLOSION 7-10J")
print("5. Comparaison Dual Motor")
print("6. Affichage recommandations")
print()

input("Appuyez sur ENTREE pour commencer...")

# Etape 1
run_command(
    "ETAPE 1: Enrichissement metriques experts",
    f'"{PYTHON}" recalcul_simple.py',
    required=True
)

# Etape 2
run_command(
    "ETAPE 2: Analyse technique IA",
    f'"{PYTHON}" analyse_ia_simple.py',
    required=False
)

# Etape 3
run_command(
    "ETAPE 3: Decision WOS STABLE",
    f'"{PYTHON}" decision_finale_brvm.py',
    required=False
)

# Etape 4
run_command(
    "ETAPE 4: Decision EXPLOSION 7-10J",
    f'"{PYTHON}" explosion_simple.py 2026-W06',
    required=True
)

# Etape 5
run_command(
    "ETAPE 5: Comparaison Dual Motor",
    f'"{PYTHON}" comparer_dual_motor_simple.py',
    required=False
)

# Etape 6
run_command(
    "ETAPE 6: Affichage recommandations",
    f'"{PYTHON}" afficher_toutes_recommandations.py',
    required=False
)

# RESUME
print("\n" + "="*80)
print("[TERMINE] PIPELINE COMPLET")
print("="*80)

from pymongo import MongoClient
db = MongoClient('localhost', 27017)['centralisation_db']

wos_count = db.decisions_finales_brvm.count_documents({})
exp_count = db.decisions_explosion_7j.count_documents({})

print(f"\nRESULTATS:")
print(f"  Decisions WOS STABLE:   {wos_count}")
print(f"  Decisions EXPLOSION 7J: {exp_count}")
print(f"  TOTAL:                  {wos_count + exp_count}")

print(f"\nCOMMANDES UTILES:")
print(f"  python afficher_recommandations_ia.py")
print(f"  python comparer_dual_motor_simple.py")
print(f"  python caracteristiques_systeme.py")

print("\n" + "="*80)
print("[OK] SYSTEME DUAL MOTOR OPERATIONNEL")
print("="*80 + "\n")

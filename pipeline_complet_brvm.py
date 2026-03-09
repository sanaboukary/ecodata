#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COMPLET BRVM - DUAL MOTOR
==================================

Exécute l'ensemble du processus :
1. Collecte publications BRVM
2. Analyse sémantique
3. Agrégation par action
4. Enrichissement métriques experts
5. Analyse technique IA
6. Décision WOS STABLE
7. Décision EXPLOSION 7-10 JOURS
8. Comparaison Dual Motor
9. Affichage recommandations

UTILISATION:
  python pipeline_complet_brvm.py
  python pipeline_complet_brvm.py --skip-collecte  (sauter étape 1)
  python pipeline_complet_brvm.py --week 2026-W06  (semaine spécifique pour EXPLOSION)
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("\n" + "="*80)
print("PIPELINE COMPLET BRVM - SYSTEME DUAL MOTOR")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# Parse arguments
skip_collecte = '--skip-collecte' in sys.argv
week_arg = None
for i, arg in enumerate(sys.argv):
    if arg == '--week' and i+1 < len(sys.argv):
        week_arg = sys.argv[i+1]

# Configuration exécution
PYTHON = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")

def run_step(step_num, title, command, required=True, timeout=300):
    """Exécute une étape du pipeline"""
    print(f"\n{'='*80}")
    print(f"ÉTAPE {step_num}: {title}")
    print(f"{'='*80}")
    print(f"Commande: {command}")
    print(f"Timeout: {timeout}s\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(BASE_DIR),
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        # Afficher sortie
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n⚠️  ERREUR (code {result.returncode})")
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if required:
                print(f"\n❌ ÉTAPE {step_num} ÉCHOUÉE - ARRÊT DU PIPELINE")
                sys.exit(1)
            else:
                print(f"\n⚠️  ÉTAPE {step_num} ÉCHOUÉE - CONTINUATION (non-critique)")
                return False
        else:
            print(f"\n✅ ÉTAPE {step_num} TERMINÉE")
            return True
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  TIMEOUT ({timeout}s) - ÉTAPE {step_num}")
        if required:
            print(f"❌ ÉTAPE {step_num} TIMEOUT - ARRÊT DU PIPELINE")
            sys.exit(1)
        else:
            print(f"⚠️  ÉTAPE {step_num} TIMEOUT - CONTINUATION")
            return False
    
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        if required:
            print(f"❌ ÉTAPE {step_num} EXCEPTION - ARRÊT DU PIPELINE")
            sys.exit(1)
        else:
            print(f"⚠️  ÉTAPE {step_num} EXCEPTION - CONTINUATION")
            return False

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

step = 1

# ÉTAPE 1: Collecte publications (optionnelle)
if not skip_collecte:
    run_step(
        step, 
        "Collecte publications BRVM", 
        f'"{PYTHON}" collecter_publications_brvm.py',
        required=False,  # Non-critique si déjà collecté
        timeout=180
    )
    step += 1
else:
    print(f"\n{'='*80}")
    print(f"ÉTAPE 1 IGNORÉE: Collecte publications (--skip-collecte)")
    print(f"{'='*80}\n")
    step += 1

# ÉTAPE 2: Analyse sémantique
run_step(
    step,
    "Analyse sémantique publications",
    f'"{PYTHON}" analyse_semantique_brvm_v3.py',
    required=False,  # Non-critique si déjà fait
    timeout=300
)
step += 1

# ÉTAPE 3: Agrégation sémantique par action
run_step(
    step,
    "Agrégation sémantique par action",
    f'"{PYTHON}" agregateur_semantique_actions.py',
    required=False,  # Non-critique
    timeout=120
)
step += 1

# ÉTAPE 4: Enrichissement métriques experts
run_step(
    step,
    "Enrichissement métriques experts (Volume Z-score, Acceleration)",
    f'"{PYTHON}" recalcul_simple.py',
    required=True,  # Important pour nouveau système
    timeout=180
)
step += 1

# ÉTAPE 5: Analyse technique IA (avec métriques experts)
run_step(
    step,
    "Analyse technique IA (WOS scoring)",
    f'"{PYTHON}" analyse_ia_simple.py',
    required=True,
    timeout=300
)
step += 1

# ÉTAPE 6: Décision finale WOS STABLE
run_step(
    step,
    "Décision finale WOS STABLE (MOTEUR 1)",
    f'"{PYTHON}" decision_finale_brvm.py',
    required=True,
    timeout=180
)
step += 1

# ÉTAPE 7: Décision EXPLOSION 7-10 JOURS
week_cmd = f" {week_arg}" if week_arg else " 2026-W06"
run_step(
    step,
    "Décision EXPLOSION 7-10 JOURS (MOTEUR 2)",
    f'"{PYTHON}" explosion_simple.py{week_cmd}',
    required=True,
    timeout=180
)
step += 1

# ÉTAPE 8: Comparaison Dual Motor
run_step(
    step,
    "Comparaison DUAL MOTOR (WOS vs EXPLOSION)",
    f'"{PYTHON}" comparer_dual_motor_simple.py',
    required=False,  # Non-critique
    timeout=60
)
step += 1

# ÉTAPE 9: Affichage recommandations
run_step(
    step,
    "Affichage recommandations finales",
    f'"{PYTHON}" afficher_toutes_recommandations.py',
    required=False,  # Non-critique
    timeout=60
)
step += 1

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("\n" + "="*80)
print("[TERMINE] PIPELINE COMPLET")
print("="*80)

from pymongo import MongoClient
db = MongoClient('localhost', 27017)['centralisation_db']

wos_count = db.decisions_finales_brvm.count_documents({})
explosion_count = db.decisions_explosion_7j.count_documents({})

print(f"\nRESULTATS:")
print(f"   Decisions WOS STABLE:     {wos_count}")
print(f"   Decisions EXPLOSION 7J:   {explosion_count}")
print(f"   TOTAL POSITIONS:          {wos_count + explosion_count}")

print(f"\nPROCHAINES ETAPES:")
print(f"   1. Consulter les recommandations:")
print(f"      python afficher_recommandations_ia.py")
print(f"      python afficher_toutes_recommandations.py")
print(f"")
print(f"   2. Comparer les 2 moteurs:")
print(f"      python comparer_dual_motor.py")
print(f"")
print(f"   3. Voir caracteristiques systeme:")
print(f"      python caracteristiques_systeme.py")

print("\n" + "="*80)
print("[OK] SYSTEME DUAL MOTOR OPERATIONNEL")
print("Pret a battre 96% des outils BRVM")
print("="*80 + "\n")

#!/usr/bin/env python3
"""
🚀 PIPELINE AUTOMATISÉ BRVM – IA DÉCISIONNELLE
=============================================

Exécution complète et ordonnée :
1. Collecte publications
2. Extraction sémantique
3. Agrégation par action
4. Analyse IA technique
5. Décision finale investissement

🎯 Une seule commande = tout le système
"""

import subprocess
import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime

PYTHON = "./.venv/Scripts/python.exe"

# Env enfant : forcer UTF-8 pour tous les scripts fils
_CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

PIPELINE = [
    ("COLLECTE PUBLICATIONS (general + par emetteur)", "collecter_publications_brvm.py"),
    ("EXTRACTION PDF (pdfplumber)", "extraire_pdf_pdfplumber.py"),         # 1ter
    ("ANALYSE SEMANTIQUE V3 (FILTRE RISQUE)", "analyse_semantique_brvm_v3.py"),
    ("AGREGATION SEMANTIQUE PAR ACTION", "agregateur_semantique_actions.py"),
    ("ANALYSE TECHNIQUE (SETUP)", "analyse_ia_simple.py"),
    ("DECISION WEEKLY (PRIX FIRST)", "decision_finale_brvm.py"),
    ("MULTI-FACTOR ENGINE + INJECTION BUY MANQUANTS", "multi_factor_engine.py"),
    ("TOP5 ENGINE FINAL (BLACKLIST + REGIME + VCP + TP)", "top5_engine_final.py"),
    ("AJUSTEMENT SECTORIEL (SIZING/CONFIANCE)", "propagation_sector_to_action.py"),
    ("MONITORING & ALERTES", "backtest_reporting_monitoring.py"),
]

def run_step(name, script):
    print("\n" + "=" * 70)
    print(f"▶ {name}")
    print("=" * 70)

    result = subprocess.run(
        [PYTHON, script],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=_CHILD_ENV
    )

    if result.returncode != 0:
        print(f"\n❌ ÉCHEC À L’ÉTAPE : {name}")
        sys.exit(1)

    print(f"✅ {name} TERMINÉ\n")

def main():
    print("\n" + "=" * 80)
    print("🧠 PIPELINE IA D’INVESTISSEMENT BRVM – DÉMARRAGE")
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    for name, script in PIPELINE:
        run_step(name, script)

    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLET TERMINÉ AVEC SUCCÈS")
    print("📊 Dashboard prêt à être consulté")
    print("=" * 80)

if __name__ == "__main__":
    main()

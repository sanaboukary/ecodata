#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte quotidienne BRVM - Version minimale sans Django initial
"""

import subprocess
import sys
from datetime import datetime

print("=" * 80)
print("🚀 COLLECTE QUOTIDIENNE BRVM")
print("=" * 80)
print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Utiliser subprocess pour éviter les imports qui bloquent
python_path = sys.executable

print("Lancement de la collecte via Django management command...")
print()

try:
    # Lancer la commande Django ingest_source
    result = subprocess.run(
        [python_path, "manage.py", "ingest_source", "--source", "brvm"],
        capture_output=True,
        text=True,
        timeout=300  # 5 minutes max
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("Erreurs :")
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n✅ Collecte terminée avec succès")
    else:
        print(f"\n❌ Erreur lors de la collecte (code: {result.returncode})")
        
except subprocess.TimeoutExpired:
    print("❌ Timeout : la collecte a pris plus de 5 minutes")
except Exception as e:
    print(f"❌ Erreur : {e}")

print("\n" + "=" * 80)
print(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

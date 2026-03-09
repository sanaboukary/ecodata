#!/usr/bin/env python3
"""
WORKFLOW COMPLET BRVM - Version Production Django
==================================================

Génération (Django) → TOP5 → Dashboard → Track Record
"""

import subprocess
import sys
from datetime import datetime

PYTHON = sys.executable

print("\n" + "="*80)
print(" WORKFLOW COMPLET BRVM - PRODUCTION ".center(80))
print("="*80)
print(f" Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("="*80 + "\n")

# ÉTAPE 1 : Génération décisions (Version Django)
print("[ETAPE 1/4] Generation decisions BUY (Django)...")
print("-" * 80)
result = subprocess.run([PYTHON, "decision_finale_brvm.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"[ERREUR] {result.stderr}")
    sys.exit(1)

# ÉTAPE 2 : TOP5 ENGINE
print("\n[ETAPE 2/4] Classement TOP5...")
print("-" * 80)
result = subprocess.run([PYTHON, "top5_engine_final.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"[ERREUR] {result.stderr}")
    sys.exit(1)

# ÉTAPE 3 : Dashboard
print("\n[ETAPE 3/4] Generation dashboard...")
print("-" * 80)
result = subprocess.run([PYTHON, "dashboard_affichage.py"], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
if result.returncode != 0:
    print(f"[ERREUR] {result.stderr}")
    sys.exit(1)

# ÉTAPE 4 : Figer recommandations pour track record
print("\n[ETAPE 4/4] Figer recommandations semaine...")
print("-" * 80)
try:
    from pymongo import MongoClient
    from datetime import datetime, timezone
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["centralisation_db"]
    
    # Figer les TOP5 pour suivi performance
    week_id = datetime.now().strftime("%Y-W%U")
    top5 = list(db.top5_weekly_brvm.find().sort([("rank", 1)]).limit(5))
    
    if top5:
        for reco in top5:
            reco["week_id"] = week_id
            reco["figee_le"] = datetime.now(timezone.utc)
            reco["statut"] = "EN_COURS"  # GAGNANT/PERDANT/EN_COURS
        
        # Sauvegarder dans track_record_weekly
        db.track_record_weekly.delete_many({"week_id": week_id})
        db.track_record_weekly.insert_many(top5)
        
        print(f"[OK] {len(top5)} recommandations figees pour semaine {week_id}")
        print(f"     Symbols: {', '.join([r['symbol'] for r in top5])}")
    else:
        print("[INFO] Aucune recommandation TOP5 a figer")
    
except Exception as e:
    print(f"[ERREUR] Track record: {e}")

print("\n" + "="*80)
print(" WORKFLOW TERMINE ".center(80))
print("="*80)
print(f" Dashboard disponible : dashboard_output.txt")
print(f" Logs detailles       : generation_log.txt (si utilise)")
print("="*80 + "\n")

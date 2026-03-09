#!/usr/bin/env python3
"""
Lancement sequentiel de toutes les collectes internationales
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

print("\n" + "="*80)
print("COLLECTE COMPLETE - TOUTES SOURCES (1990-2026)")
print("="*80)
print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

scripts = [
    ('World Bank', 'collecter_worldbank_complet.py'),
    ('IMF', 'collecter_imf_complet.py'),
    ('AfDB + UN SDG', 'collecter_afdb_un_complet.py'),
]

for nom, script in scripts:
    print(f"\n{'='*80}")
    print(f"LANCEMENT: {nom}")
    print(f"{'='*80}\n")
    
    script_path = BASE_DIR / script
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n[OK] {nom} termine avec succes")
        else:
            print(f"\n[ECHEC] {nom} termine avec erreur (code {result.returncode})")
            
    except Exception as e:
        print(f"\n[ERREUR] {nom}: {e}")

print("\n" + "="*80)
print("TOUTES LES COLLECTES TERMINEES")
print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# Afficher resume
print("Lancement du resume...")
subprocess.run([sys.executable, str(BASE_DIR / 'resume_simple.py')])

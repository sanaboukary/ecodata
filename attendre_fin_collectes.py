#!/usr/bin/env python3
"""
Attendre la fin des collectes et generer un rapport complet
"""
import sys
from pathlib import Path
import time
from datetime import datetime
import os

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db

def compter_lignes(fichier):
    """Compter lignes avec OK/ECHEC"""
    if not os.path.exists(fichier):
        return 0, 0, False
    
    try:
        with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
            contenu = f.read()
            ok = contenu.count('OK -')
            echec = contenu.count('ECHEC')
            termine = 'RAPPORT FINAL' in contenu
            return ok, echec, termine
    except:
        return 0, 0, False

def verifier_processus():
    """Verifier si les processus tournent encore"""
    try:
        # Chercher les processus Python qui contiennent "collecter"
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        collecteurs = [l for l in lines if 'collecter_imf' in l or 'collecter_afdb' in l]
        return len(collecteurs) > 0
    except:
        return True  # Assumer qu'ils tournent si on ne peut pas verifier

print("\n" + "="*80)
print("SUIVI COLLECTES INTERNATIONALES")
print("="*80)
print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nAttente de la fin des collectes...")
print("(Les collectes tournent en arriere-plan, cela peut prendre 5-10 minutes)\n")

# Boucle de surveillance
iteration = 0
while True:
    iteration += 1
    
    # Compter progression
    imf_ok, imf_echec, imf_termine = compter_lignes('imf_collecte.log')
    afdb_ok, afdb_echec, afdb_termine = compter_lignes('afdb_un_collecte.log')
    
    total_ok = imf_ok + afdb_ok
    total_echec = imf_echec + afdb_echec
    
    # Affichage toutes les 10 iterations (30 secondes)
    if iteration % 10 == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] IMF: {imf_ok}/64 | AfDB/UN: {afdb_ok}/96 | Total: {total_ok}/160")
    
    # Verifier si termine
    processus_actifs = verifier_processus()
    
    if (imf_termine and afdb_termine) or not processus_actifs:
        print("\n✓ Collectes terminees !\n")
        break
    
    time.sleep(3)

# Rapport final
print("="*80)
print("RAPPORT FINAL DES COLLECTES")
print("="*80)
print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print(f"[IMF]")
print(f"  Reussies  : {imf_ok:3d}/64")
print(f"  Echouees  : {imf_echec:3d}")
print(f"  Taux reussite: {imf_ok/64*100:.1f}%\n")

print(f"[AfDB + UN SDG]")
print(f"  Reussies  : {afdb_ok:3d}/96")
print(f"  Echouees  : {afdb_echec:3d}")
print(f"  Taux reussite: {afdb_ok/96*100:.1f}%\n")

print(f"[TOTAL]")
print(f"  Reussies  : {total_ok:4d}/160")
print(f"  Echouees  : {total_echec:4d}")
print(f"  Taux reussite: {total_ok/160*100:.1f}%")

# Stats MongoDB
print("\n" + "="*80)
print("VERIFICATION BASE DE DONNEES")
print("="*80)

try:
    client, db = get_mongo_db()
    
    # Compter observations par source
    sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
    
    print("\nObservations dans curated_observations:\n")
    
    total_obs = 0
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        total_obs += count
        print(f"  {source:15s}: {count:6d} observations")
    
    print(f"\n  {'TOTAL':15s}: {total_obs:6d} observations")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"Erreur MongoDB: {e}")

print("\nPour voir le detail:")
print("  python resume_simple.py")
print("  python show_complete_data.py")

#!/usr/bin/env python3
"""
Moniteur de collecte World Bank en temps reel
"""
import sys
from pathlib import Path
import time
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def afficher_progres():
    """Afficher le progres de la collecte"""
    try:
        _, db = get_mongo_db()
        
        # Total observations World Bank
        total_wb = db.curated_observations.count_documents({'source': 'WorldBank'})
        
        # Par annee recente
        annees_recentes = {}
        for annee in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
            count = db.curated_observations.count_documents({
                'source': 'WorldBank',
                'ts': {'$regex': f'^{annee}'}
            })
            annees_recentes[annee] = count
        
        # Affichage
        print("\n" + "="*70)
        print(f"PROGRES COLLECTE WORLD BANK - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        print(f"\nTotal observations World Bank: {total_wb:,}")
        
        print(f"\nPar annee (2020-2026):")
        for annee, count in annees_recentes.items():
            barre = "█" * min(50, count // 10)
            print(f"  {annee}: {count:>6,} obs {barre}")
        
        # Objectif: 65 indicateurs x 8 pays x 67 annees = 34,880 max
        objectif = 34880
        progress_pct = (total_wb / objectif * 100) if objectif > 0 else 0
        
        print(f"\nObjectif total: {objectif:,} observations")
        print(f"Progression: {progress_pct:.1f}%")
        print(f"Reste: {objectif - total_wb:,} observations")
        print("="*70)
        
        return total_wb
        
    except Exception as e:
        print(f"Erreur: {e}")
        return 0

def verifier_logs():
    """Afficher les dernieres lignes des logs"""
    log_files = list(Path('.').glob('collecte_wb_*.log'))
    if not log_files:
        print("\nAucun fichier log trouve")
        return
    
    # Prendre le plus recent
    latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    
    print(f"\nDernieres lignes de {latest_log.name}:")
    print("-" * 70)
    
    try:
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(line.rstrip())
    except Exception as e:
        print(f"Erreur lecture log: {e}")

def moniteur_continu(interval=30):
    """Moniteur en boucle avec rafraichissement"""
    print("\n" + "="*70)
    print("MONITEUR COLLECTE WORLD BANK - Appuyez sur Ctrl+C pour quitter")
    print("="*70)
    
    obs_precedent = 0
    try:
        while True:
            obs_actuel = afficher_progres()
            
            if obs_precedent > 0:
                delta = obs_actuel - obs_precedent
                vitesse = delta / interval  # obs par seconde
                print(f"\nVitesse: +{delta} obs en {interval}s ({vitesse:.1f} obs/s)")
            
            obs_precedent = obs_actuel
            
            print(f"\nProchain rafraichissement dans {interval}s...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMoniteur arrete")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continu':
        moniteur_continu(30)
    else:
        afficher_progres()
        verifier_logs()
        print("\n")
        print("Pour monitoring continu: python moniteur_collecte.py --continu")

if __name__ == '__main__':
    main()

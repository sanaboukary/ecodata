#!/usr/bin/env python3
"""
📊 MONITEUR TEMPS RÉEL - COLLECTES EN COURS
Affiche la progression toutes les 30 secondes
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

def afficher_progression_temps_reel():
    """Affiche la progression en temps réel"""
    _, db = get_mongo_db()
    
    print("\n" + "="*70)
    print("MONITEUR TEMPS REEL - COLLECTES EN COURS")
    print("="*70)
    print("Appuyez sur Ctrl+C pour arrêter le monitoring\n")
    
    iteration = 0
    previous_counts = {}
    
    try:
        while True:
            iteration += 1
            now = datetime.now().strftime('%H:%M:%S')
            
            # Compter les observations
            counts = {
                'WorldBank': db.curated_observations.count_documents({'source': 'WorldBank'}),
                'IMF': db.curated_observations.count_documents({'source': 'IMF'}),
                'AfDB': db.curated_observations.count_documents({'source': 'AfDB'}),
                'UN_SDG': db.curated_observations.count_documents({'source': 'UN_SDG'}),
                'BRVM': db.curated_observations.count_documents({'source': 'BRVM'}),
            }
            
            total = sum(counts.values())
            
            # Calculer les gains
            gains = {}
            for source, count in counts.items():
                prev = previous_counts.get(source, count)
                gains[source] = count - prev
            
            # Affichage
            print(f"\n[{now}] Iteration #{iteration}")
            print("-" * 70)
            
            for source in ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM']:
                count = counts[source]
                gain = gains[source]
                
                if gain > 0:
                    print(f"  {source:12} : {count:6,} obs (+{gain:4,} depuis derniere iteration)")
                else:
                    print(f"  {source:12} : {count:6,} obs")
            
            print(f"  {'TOTAL':12} : {total:6,} obs")
            
            # Sauvegarder pour prochaine itération
            previous_counts = counts.copy()
            
            # Attendre 30 secondes
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring arrêté par l'utilisateur")
        print("="*70)
        print(f"Dernier état :")
        for source in ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM']:
            print(f"  {source:12} : {counts[source]:6,} obs")
        print(f"  {'TOTAL':12} : {total:6,} obs")
        print("="*70 + "\n")

if __name__ == '__main__':
    afficher_progression_temps_reel()

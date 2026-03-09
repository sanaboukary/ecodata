#!/usr/bin/env python3
"""
📊 Suivi en temps réel de la collecte
"""
import time
import os
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def afficher_progression():
    """Afficher la progression de la collecte"""
    _, db = get_mongo_db()
    
    sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
    
    print("\n" + "="*70)
    print(f"📊 PROGRESSION COLLECTE - {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        print(f"  {source:15} : {count:>8,} observations")
    
    total = db.curated_observations.count_documents({})
    print(f"  {'-'*60}")
    print(f"  {'TOTAL':15} : {total:>8,} observations")
    print("="*70)
    
    # Dernières ingestions
    print("\n📋 Dernières exécutions:")
    for run in db.ingestion_runs.find().sort('start_time', -1).limit(5):
        status = "✅" if run.get('status') == 'success' else "❌"
        source = run.get('source', 'N/A')
        obs_count = run.get('obs_count', 0)
        start = run.get('start_time', 'N/A')
        print(f"  {status} {source:12} - {obs_count:>5,} obs - {start}")
    
    print("="*70 + "\n")

def main():
    print("\n🔄 Suivi de la collecte (rafraîchissement toutes les 10 secondes)")
    print("   Appuyez sur Ctrl+C pour arrêter\n")
    
    try:
        while True:
            afficher_progression()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n✋ Suivi arrêté\n")

if __name__ == '__main__':
    # Setup Django
    import sys
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    main()

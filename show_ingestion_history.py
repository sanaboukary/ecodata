#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification de l'historique des ingestions
Affiche les stats et derniers runs pour chaque source
"""
import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("=" * 80)
    print("📊 HISTORIQUE DES INGESTIONS")
    print("=" * 80)
    
    sources = ['BRVM', 'WorldBank', 'IMF', 'UN_SDG', 'AfDB']
    
    for source in sources:
        print(f"\n{'='*80}")
        print(f"Source: {source}")
        print(f"{'='*80}")
        
        # Stats globales
        total = db.ingestion_runs.count_documents({'source': source})
        success = db.ingestion_runs.count_documents({'source': source, 'status': 'success'})
        error = total - success
        
        print(f"📈 Total exécutions: {total}")
        print(f"✅ Succès: {success}")
        print(f"❌ Erreurs: {error}")
        if total > 0:
            print(f"📊 Taux de réussite: {success/total*100:.1f}%")
        
        # Derniers runs
        print(f"\n🕐 5 dernières exécutions:")
        runs = list(db.ingestion_runs.find({'source': source}).sort('started_at', -1).limit(5))
        
        if not runs:
            print("   Aucun historique disponible")
        else:
            for run in runs:
                status_icon = "✅" if run['status'] == 'success' else "❌"
                date = run['started_at'].strftime('%Y-%m-%d %H:%M:%S')
                duration = run.get('duration_sec', 0)
                obs = run.get('obs_count', 0)
                print(f"   {status_icon} {date} - {obs} obs - {duration:.2f}s")
                if run.get('error_msg'):
                    print(f"      ⚠️  Erreur: {run['error_msg'][:80]}")
    
    # Stats totales
    print(f"\n{'='*80}")
    print("RÉSUMÉ GLOBAL")
    print(f"{'='*80}")
    
    total_runs = db.ingestion_runs.count_documents({})
    total_success = db.ingestion_runs.count_documents({'status': 'success'})
    total_obs = sum(run.get('obs_count', 0) for run in db.ingestion_runs.find({'status': 'success'}))
    
    print(f"📈 Total exécutions: {total_runs}")
    print(f"✅ Succès: {total_success}")
    print(f"📊 Observations ingérées: {total_obs}")
    
    # Dernière exécution globale
    last_run = db.ingestion_runs.find_one({}, sort=[('started_at', -1)])
    if last_run:
        print(f"\n🕐 Dernière exécution:")
        print(f"   Source: {last_run['source']}")
        print(f"   Date: {last_run['started_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Statut: {last_run['status']}")
        print(f"   Observations: {last_run.get('obs_count', 0)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

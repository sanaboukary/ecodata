#!/usr/bin/env python3
"""Afficher statistiques actuelles de la base de donnees"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

try:
    client, db = get_mongo_db()
    
    print("\n" + "="*80)
    print(f"STATISTIQUES BASE DE DONNEES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Observations par source
    sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
    
    print("\n[OBSERVATIONS PAR SOURCE]\n")
    
    total_obs = 0
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        total_obs += count
        
        if count > 0:
            # Derniere observation
            derniere = db.curated_observations.find_one(
                {'source': source},
                sort=[('ts', -1)]
            )
            derniere_date = derniere.get('ts', 'N/A') if derniere else 'N/A'
            
            print(f"  {source:15s}: {count:6d} obs (derniere: {derniere_date})")
        else:
            print(f"  {source:15s}: {count:6d} obs")
    
    print(f"\n  {'TOTAL':15s}: {total_obs:6d} observations")
    
    # Executions
    print("\n" + "="*80)
    print("[DERNIERES EXECUTIONS]\n")
    
    runs = list(db.ingestion_runs.find(
        {},
        sort=[('end_time', -1)]
    ).limit(10))
    
    for run in runs:
        source = run.get('source', 'N/A')
        status = run.get('status', 'N/A')
        obs_count = run.get('obs_count', 0)
        end_time = run.get('end_time', 'N/A')
        
        status_icon = '✓' if status == 'success' else '✗'
        print(f"  {status_icon} {source:15s} - {obs_count:4d} obs - {end_time}")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\nERREUR: {e}")
    import traceback
    traceback.print_exc()

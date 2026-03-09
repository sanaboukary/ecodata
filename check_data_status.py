#!/usr/bin/env python3
"""Vérifier l'état des données BRVM"""
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("🔍 ÉTAT ACTUEL DES DONNÉES BRVM")
    print("="*80 + "\n")
    
    collections = {
        'curated_observations': 'Données historiques (source)',
        'prices_intraday_raw': 'RAW (nouvelles collectes)',
        'prices_daily': 'DAILY (agrégation journalière)',
        'prices_weekly': 'WEEKLY (hebdomadaire + indicateurs)',
        'top5_weekly_brvm': 'TOP5 recommandations',
        'opportunities_brvm': 'Opportunités détectées'
    }
    
    for coll_name, desc in collections.items():
        count = db[coll_name].count_documents({})
        print(f"📊 {coll_name:<25} : {count:>6,} docs - {desc}")
        
        if count > 0:
            # Dates disponibles
            if 'date' in db[coll_name].find_one():
                dates = db[coll_name].distinct('date')
                if dates:
                    dates_sorted = sorted(dates)
                    print(f"   📅 Dates: {dates_sorted[0]} → {dates_sorted[-1]} ({len(dates)} dates)")
            elif 'datetime' in db[coll_name].find_one():
                first = db[coll_name].find_one(sort=[('datetime', 1)])
                last = db[coll_name].find_one(sort=[('datetime', -1)])
                if first and last:
                    print(f"   📅 Période: {first.get('datetime')} → {last.get('datetime')}")
            elif 'week' in db[coll_name].find_one():
                weeks = sorted(db[coll_name].distinct('week'))
                print(f"   📅 Semaines: {weeks[0]} → {weeks[-1]} ({len(weeks)} semaines)")
    
    print("\n" + "="*80)
    
    # Fichiers de sauvegarde
    print("\n🗂️  FICHIERS CSV DISPONIBLES:\n")
    csv_files = list(Path(BASE_DIR).glob("*.csv"))
    for f in csv_files[:10]:
        size = f.stat().st_size / 1024
        print(f"   {f.name:<50} ({size:>8,.1f} KB)")
    
    if len(csv_files) > 10:
        print(f"\n   ... et {len(csv_files) - 10} autres fichiers CSV")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()

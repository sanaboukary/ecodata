#!/usr/bin/env python3
"""
Vérifier le progrès de la collecte World Bank 2025-2026
"""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("\n" + "="*60)
    print("ÉTAT COLLECTE WORLD BANK 2025-2026")
    print("="*60)
    
    # Données 2025
    count_2025 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2025'}
    })
    
    # Données 2026
    count_2026 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2026'}
    })
    
    # Total World Bank
    total_wb = db.curated_observations.count_documents({
        'source': 'WorldBank'
    })
    
    print(f"\n📊 Observations collectées:")
    print(f"  2025: {count_2025:,} observations")
    print(f"  2026: {count_2026:,} observations")
    print(f"  Total World Bank: {total_wb:,} observations")
    
    # Objectif: 13 indicateurs × 15 pays × 2 ans = 390 observations max
    total_cible = 390
    total_actuel = count_2025 + count_2026
    progress = (total_actuel / total_cible * 100) if total_cible > 0 else 0
    
    print(f"\n📈 Progrès:")
    print(f"  Cible: {total_cible} observations")
    print(f"  Collecté: {total_actuel} observations")
    print(f"  Progression: {progress:.1f}%")
    
    # Dernières observations
    latest = list(db.curated_observations.find(
        {'source': 'WorldBank'},
        {'key': 1, 'dataset': 1, 'ts': 1, '_id': 0}
    ).sort('_id', -1).limit(5))
    
    if latest:
        print(f"\n🕐 Dernières observations collectées:")
        for obs in latest:
            print(f"  {obs.get('ts', 'N/A')[:10]} | {obs.get('dataset', 'N/A')} | {obs.get('key', 'N/A')}")
    
    print("="*60 + "\n")
    
    # Statut du processus
    import subprocess
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'collecter_worldbank_2025_2026' in result.stdout:
            print("✅ Processus de collecte EN COURS\n")
        else:
            print("⚠️  Processus de collecte TERMINÉ ou NON DÉTECTÉ\n")
    except:
        print("ℹ️  Impossible de vérifier le statut du processus\n")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Affichage simple World Bank"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("DONNEES WORLD BANK")
print("="*80)

# Total
total = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"\nTotal: {total:,} observations")

if total == 0:
    print("\nAucune donnee World Bank.")
    print("\nCollectez avec:")
    print("  python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI")
else:
    # Echantillon
    print("\nEchantillon (10 premieres):")
    print(f"{'PAYS':<8} {'INDICATEUR':<35} {'ANNEE':<6} {'VALEUR':>15}")
    print("-"*80)
    
    for obs in db.curated_observations.find({'source': 'WorldBank'}).limit(10):
        pays = obs.get('key', 'N/A')[:8]
        indic = obs.get('dataset', 'N/A')[:35]
        annee = obs.get('ts', 'N/A')[:6]
        val = obs.get('value', 0)
        
        if isinstance(val, (int, float)):
            if val > 1e9:
                val_str = f"{val/1e9:.2f}B"
            elif val > 1e6:
                val_str = f"{val/1e6:.2f}M"
            else:
                val_str = f"{val:,.2f}"
        else:
            val_str = str(val)[:15]
        
        print(f"{pays:<8} {indic:<35} {annee:<6} {val_str:>15}")

print("="*80 + "\n")

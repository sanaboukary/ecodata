#!/usr/bin/env python3
"""Rapport World Bank vers fichier"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

output_file = BASE_DIR / f"rapport_worldbank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

with open(output_file, 'w', encoding='utf-8') as f:
    _, db = get_mongo_db()
    
    f.write("="*80 + "\n")
    f.write("RAPPORT DONNEES WORLD BANK\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*80 + "\n\n")
    
    # Total
    total = db.curated_observations.count_documents({'source': 'WorldBank'})
    f.write(f"Total observations: {total:,}\n\n")
    
    if total == 0:
        f.write("Aucune donnee World Bank trouvee.\n")
    else:
        f.write("Echantillon (20 premieres observations):\n")
        f.write(f"{'PAYS':<8} {'INDICATEUR':<40} {'ANNEE':<6} {'VALEUR':>15}\n")
        f.write("-"*80 + "\n")
        
        for obs in db.curated_observations.find({'source': 'WorldBank'}).limit(20):
            pays = str(obs.get('key', 'N/A'))[:8]
            indic = str(obs.get('dataset', 'N/A'))[:40]
            annee = str(obs.get('ts', 'N/A'))[:6]
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
            
            f.write(f"{pays:<8} {indic:<40} {annee:<6} {val_str:>15}\n")
    
    f.write("\n" + "="*80 + "\n")

print(f"Rapport genere: {output_file}")
print(f"Taille: {output_file.stat().st_size} octets")

#!/usr/bin/env python3
"""
📥 IMPORT CSV BRVM - DONNÉES RÉELLES UNIQUEMENT
Politique TOLÉRANCE ZÉRO: Importe UNIQUEMENT les cours > 0
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import csv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("=" * 100)
print("📥 IMPORT CSV BRVM - DONNÉES RÉELLES UNIQUEMENT")
print("=" * 100)
print()

# Fichiers à importer (ordonnés par priorité)
FICHIERS_CSV = [
    ('donnees_reelles_brvm.csv', '9 décembre 2025'),
    ('historique_brvm.csv', 'Historique multi-dates'),
]

def importer_csv_brvm(fichier_path, description):
    """Importer un CSV BRVM en filtrant les valeurs à 0"""
    
    if not Path(fichier_path).exists():
        print(f"⏭️  {fichier_path} - Fichier introuvable")
        return 0
    
    print(f"📄 {fichier_path}")
    print(f"   {description}")
    
    _, db = get_mongo_db()
    
    inserted = 0
    updated = 0
    skipped_zero = 0
    errors = 0
    
    with open(fichier_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Extraire données
                date = row.get('DATE', '').strip()
                symbol = row.get('SYMBOL', '').strip()
                close = float(row.get('CLOSE', 0))
                volume = int(float(row.get('VOLUME', 0)))
                variation = float(row.get('VARIATION', 0))
                
                # 🔴 POLITIQUE TOLÉRANCE ZÉRO: Ignorer cours à 0
                if close <= 0:
                    skipped_zero += 1
                    continue
                
                # Valider date
                if not date or len(date) != 10:
                    continue
                
                # Normaliser symbole
                if not symbol.endswith('.BC'):
                    symbol += '.BC'
                
                # Créer observation
                observation = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbol.replace('.BC', ''),
                    'ts': date,
                    'value': close,
                    'attrs': {
                        'symbol': symbol.replace('.BC', ''),
                        'close': close,
                        'volume': volume,
                        'variation': variation,
                        'data_quality': 'REAL_MANUAL',  # ✅ Données vérifiées
                        'import_source': fichier_path,
                        'import_datetime': datetime.now().isoformat(),
                    }
                }
                
                # Upsert
                result = db.curated_observations.update_one(
                    {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': observation['key'],
                        'ts': date
                    },
                    {'$set': observation},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1
                    
            except Exception as e:
                errors += 1
    
    print(f"   ✅ Insérées    : {inserted}")
    print(f"   🔄 Mises à jour: {updated}")
    print(f"   ⏭️  Ignorées (0) : {skipped_zero}")
    print(f"   ❌ Erreurs     : {errors}")
    print()
    
    return inserted + updated

def main():
    total_imported = 0
    
    for fichier, desc in FICHIERS_CSV:
        count = importer_csv_brvm(fichier, desc)
        total_imported += count
    
    print("=" * 100)
    print("📊 RÉSULTAT FINAL")
    print("=" * 100)
    
    # Vérifier en base
    _, db = get_mongo_db()
    
    total_brvm = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    })
    
    print(f"✅ Total importé: {total_imported} observations")
    print(f"📊 Total en base: {total_brvm} observations BRVM")
    
    # Dernières données
    if total_brvm > 0:
        latest = db.curated_observations.find_one(
            {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
            sort=[('ts', -1)]
        )
        print(f"📅 Dernière date: {latest.get('ts', 'N/A')[:10]}")
        
        # Stats par date
        pipeline = [
            {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
            {'$group': {'_id': '$ts', 'count': {'$sum': 1}}},
            {'$sort': {'_id': -1}},
            {'$limit': 5}
        ]
        
        print(f"\nTop 5 dates récentes:")
        for item in db.curated_observations.aggregate(pipeline):
            print(f"  {item['_id'][:10]}: {item['count']:3d} actions")
    
    print()
    print("🔍 Vérifier dashboard: http://127.0.0.1:8000/brvm/")
    print("=" * 100)

if __name__ == '__main__':
    main()

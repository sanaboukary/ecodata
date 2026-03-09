import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("DÉTAIL PAR SOURCE")
print("="*80)

sources = ['AGREGATION_HEBDOMADAIRE', 'BRVM', 'BRVM_CSV_HISTORIQUE', 'BRVM_CSV_RESTAURATION']

for source in sources:
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'source': source
    })
    
    jours = len(db.curated_observations.distinct('ts', {
        'dataset': 'STOCK_PRICE',
        'source': source
    }))
    
    # Premier et dernier
    first = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'source': source
    }).sort('ts', 1).limit(1))
    
    last = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'source': source
    }).sort('ts', -1).limit(1))
    
    first_ts = first[0]['ts'] if first else 'N/A'
    last_ts = last[0]['ts'] if last else 'N/A'
    
    print(f"\n{source}:")
    print(f"  Observations : {count:,}")
    print(f"  Jours        : {jours}")
    print(f"  Première date: {first_ts}")
    print(f"  Dernière date: {last_ts}")

print("\n" + "="*80 + "\n")

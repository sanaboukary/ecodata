#!/usr/bin/env python3
"""
Charge l'historique des données BRVM (30 derniers jours)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from scripts.connectors.brvm_historical import fetch_brvm_historical
from scripts.pipeline import normalize_brvm
from scripts.mongo_utils import get_db, write_raw, upsert_observations
from scripts.settings import MONGO_URI, MONGO_DB

print("=" * 100)
print("CHARGEMENT HISTORIQUE BRVM - 30 DERNIERS JOURS")
print("=" * 100)

# Fetch des données historiques
print("\n🔄 Génération des données historiques...")
data = fetch_brvm_historical(days=30)
print(f"✓ {len(data)} cotations générées")

# Analyse
from collections import defaultdict
dates = set()
symbols = set()

for rec in data:
    dates.add(rec['ts'][:10])
    symbols.add(rec['symbol'])

print(f"\n📊 Statistiques:")
print(f"  - Actions: {len(symbols)}")
print(f"  - Jours de cotation: {len(dates)}")
print(f"  - Total observations: {len(data)}")
print(f"  - Moyenne par action: {len(data) / len(symbols):.1f} cotations")

# Connexion DB
print(f"\n💾 Connexion à MongoDB...")
db = get_db(MONGO_URI, MONGO_DB)

# Normalisation
print(f"\n🔄 Normalisation des données...")
obs = normalize_brvm(data)
print(f"✓ {len(obs)} observations normalisées")

# Enregistrement
print(f"\n💾 Enregistrement dans MongoDB...")
try:
    write_raw(db, "BRVM_HISTORICAL", {"days": 30, "rows": len(data)})
    upsert_observations(db, obs)
    print(f"✓ Données enregistrées avec succès")
    
    # Vérification
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    client, db = get_mongo_db()
    
    total = db.curated_observations.count_documents({'source': 'BRVM'})
    symbols_db = db.curated_observations.distinct('key', {'source': 'BRVM'})
    
    print(f"\n✓ Total observations BRVM en base: {total}")
    print(f"✓ Actions distinctes: {len(symbols_db)}")
    
    # Période couverte
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {
            '_id': None,
            'min_date': {'$min': '$ts'},
            'max_date': {'$max': '$ts'}
        }}
    ]
    
    result = list(db.curated_observations.aggregate(pipeline))
    if result:
        print(f"✓ Période couverte: {result[0]['min_date']} → {result[0]['max_date']}")
    
    client.close()
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'=' * 100}")
print("✅ CHARGEMENT TERMINÉ")
print(f"{'=' * 100}")

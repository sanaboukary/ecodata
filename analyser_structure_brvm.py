"""Analyser la structure des données BRVM collectées"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

client, db = get_mongo_db()

print("=" * 90)
print("🔍 ANALYSE DE LA STRUCTURE DES DONNÉES BRVM")
print("=" * 90)

# 1. Trouver les datasets utilisés pour BRVM
print("\n1️⃣ Datasets BRVM disponibles:")
datasets = db.curated_observations.distinct('dataset', {'source': 'BRVM'})
for dataset in datasets:
    count = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': dataset})
    print(f"   - {dataset}: {count} observations")

# 2. Examiner un échantillon de chaque dataset
print("\n2️⃣ Échantillon de chaque dataset:")
for dataset in datasets:
    print(f"\n   📂 Dataset: {dataset}")
    sample = db.curated_observations.find_one({'source': 'BRVM', 'dataset': dataset})
    if sample:
        print(f"      Source: {sample.get('source')}")
        print(f"      Dataset: {sample.get('dataset')}")
        print(f"      Key: {sample.get('key')}")
        print(f"      TS: {sample.get('ts')}")
        print(f"      Value: {sample.get('value')}")
        print(f"      Attrs clés: {list(sample.get('attrs', {}).keys())}")

# 3. Trouver les données les plus récentes
print("\n3️⃣ Données les plus récentes (7 derniers jours):")
depuis = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
recent = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': {'$gte': depuis}
}).sort('ts', -1).limit(5))

for r in recent:
    print(f"   - {r.get('key')}: {r.get('value')} FCFA (Date: {r.get('ts')}, Dataset: {r.get('dataset')})")

# 4. Vérifier la structure pour les recommandations
print("\n4️⃣ Ce que le code recherche actuellement:")
print('   - Source: "BRVM"')
print('   - Dataset: "QUOTES"')

quotes_count = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'QUOTES'})
print(f"   ❌ Observations trouvées: {quotes_count}")

print("\n5️⃣ Ce qui devrait être utilisé:")
if 'STOCK_PRICE' in datasets:
    print('   ✅ Dataset: "STOCK_PRICE" (recommandé)')
    stock_count = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
    print(f'   ✅ Observations: {stock_count}')
elif datasets:
    print(f'   ✅ Dataset: "{datasets[0]}" (premier disponible)')
    print(f'   OU pas de filtre sur dataset du tout')

print("\n" + "=" * 90)

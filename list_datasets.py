#!/usr/bin/env python3
"""Liste tous les datasets disponibles dans curated_observations"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = client["centralisation_db"]

print("\n" + "=" * 80)
print("DATASETS DISPONIBLES dans curated_observations")
print("=" * 80 + "\n")

datasets = db.curated_observations.distinct("dataset")
print(f"Total: {len(datasets)} datasets\n")

# Compter et trier par nombre
dataset_counts = []
for ds in datasets:
    count = db.curated_observations.count_documents({"dataset": ds})
    dataset_counts.append((ds, count))

dataset_counts.sort(key=lambda x: x[1], reverse=True)

print(f"{'Dataset':<50s} {'Count':>10s}")
print("-" * 80)
for ds, count in dataset_counts:
    print(f"{ds:<50s} {count:>10,}")

# Vérifier spécifiquement RS
print("\n" + "=" * 80)
print("VERIFICATION RS:")
print("-" * 80)

rs_datasets = [ds for ds in datasets if "RS" in ds.upper() or "RELATIVE" in ds.upper() or "TECHNIQUE" in ds.upper()]
if rs_datasets:
    print(f"Datasets avec RS/Technique trouvés: {len(rs_datasets)}")
    for ds in rs_datasets:
        count = db.curated_observations.count_documents({"dataset": ds})
        print(f"   {ds}: {count} docs")
        
        # Sample
        sample = db.curated_observations.find_one({"dataset": ds})
        if sample:
            print(f"      Sample: {sample.get('key', '?')} - attrs: {list(sample.get('attrs', {}).keys())[:5]}")
else:
    print("❌ Aucun dataset RS/Technique trouvé")

# Vérifier DECISION_FINALE_BRVM (v1 production)
print("\n" + "=" * 80)
print("VERIFICATION V1 PRODUCTION:")
print("-" * 80)

count_v1 = db.curated_observations.count_documents({"dataset": "DECISION_FINALE_BRVM"})
print(f"DECISION_FINALE_BRVM: {count_v1} documents")

if count_v1 > 0:
    sample_v1 = db.curated_observations.find_one({"dataset": "DECISION_FINALE_BRVM"})
    if sample_v1:
        print(f"Sample: {sample_v1.get('key', '?')}")
        print(f"Attrs: {list(sample_v1.get('attrs', {}).keys())}")

print("\n" + "=" * 80 + "\n")

client.close()

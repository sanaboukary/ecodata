"""
Script pour vérifier les datasets disponibles dans BRVM
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    client, db = get_mongo_db()
    
    print("🔍 Analyse des datasets BRVM\n")
    
    # Récupérer tous les datasets uniques de BRVM
    datasets = db.curated_observations.distinct('dataset', {'source': 'BRVM'})
    
    print(f"📊 Datasets trouvés dans BRVM: {len(datasets)}\n")
    
    # Compter les observations par dataset
    for dataset in sorted(datasets):
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': dataset
        })
        print(f"  • {dataset}: {count:,} observations")
    
    print("\n" + "="*60)
    print("🔎 Recherche spécifique de publications...\n")
    
    # Recherche de publications
    pub_queries = [
        {'source': 'BRVM', 'dataset': 'PUBLICATION'},
        {'source': 'BRVM', 'dataset': 'COMMUNIQUE'},
        {'source': 'BRVM', 'dataset': 'RAPPORT'},
        {'source': 'BRVM', 'dataset': {'$regex': 'publication', '$options': 'i'}},
        {'source': 'BRVM', 'dataset': {'$regex': 'communique', '$options': 'i'}},
        {'source': 'BRVM', 'dataset': {'$regex': 'rapport', '$options': 'i'}},
        {'source': 'BRVM_PUBLICATIONS'},
    ]
    
    for query in pub_queries:
        count = db.curated_observations.count_documents(query)
        if count > 0:
            print(f"✅ Trouvé {count} observations pour: {query}")
    
    # Vérifier les attrs pour publications
    print("\n" + "="*60)
    print("🔎 Recherche dans attrs.type...\n")
    
    sample = db.curated_observations.find_one({
        'source': 'BRVM',
        'attrs.type': {'$exists': True}
    })
    
    if sample:
        print(f"✅ Exemple trouvé avec attrs.type: {sample.get('attrs', {}).get('type')}")
        print(f"   Dataset: {sample.get('dataset')}")
        print(f"   Key: {sample.get('key')}")
    
    client.close()

if __name__ == '__main__':
    main()

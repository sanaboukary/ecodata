"""
Vérification de la connexion permanente entre l'algorithme de collecte 
et la base de données centralisation_db
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.settings import MONGO_URI, MONGO_DB

print("╔════════════════════════════════════════════════════════════════╗")
print("║   VERIFICATION CONNEXION PERMANENTE - CENTRALISATION_DB       ║")
print("╚════════════════════════════════════════════════════════════════╝\n")

# 1. Vérifier la configuration
print("📋 CONFIGURATION:")
print(f"   URI MongoDB: {MONGO_URI}")
print(f"   Base de données: {MONGO_DB}")

# 2. Tester la connexion
try:
    client, db = get_mongo_db()
    print(f"\n✅ Connexion établie avec succès")
    print(f"   Nom de la base: {db.name}")
    
    # 3. Vérifier les collections
    collections = db.list_collection_names()
    print(f"\n📊 Collections disponibles ({len(collections)}):")
    for col in sorted(collections):
        count = db[col].count_documents({})
        print(f"   • {col}: {count:,} documents")
    
    # 4. Vérifier curated_observations (collection principale)
    curated = db['curated_observations']
    
    print(f"\n📈 DONNÉES PAR SOURCE (curated_observations):")
    sources = curated.distinct('source')
    total = 0
    for source in sorted(sources):
        count = curated.count_documents({'source': source})
        total += count
        print(f"   • {source}: {count:,} observations")
    
    print(f"\n   TOTAL: {total:,} observations")
    
    # 5. Vérifier l'historique d'ingestion
    ingestion_runs = db['ingestion_runs']
    last_runs = list(ingestion_runs.find().sort('started_at', -1).limit(5))
    
    if last_runs:
        print(f"\n🕐 DERNIÈRES COLLECTES:")
        for run in last_runs:
            source = run.get('source', 'Unknown')
            status = run.get('status', 'unknown')
            obs_count = run.get('obs_count', 0)
            started = run.get('started_at', 'N/A')
            status_icon = '✅' if status == 'success' else '❌'
            print(f"   {status_icon} {source}: {obs_count} obs - {started}")
    else:
        print(f"\n⚠️  Aucun historique de collecte trouvé")
    
    # 6. État de la connexion
    print(f"\n🔗 ÉTAT DE LA CONNEXION:")
    print(f"   ✅ Base de données: CONNECTÉE")
    print(f"   ✅ Collection curated: {curated.count_documents({}):,} documents")
    print(f"   ✅ Prête pour collecte automatique")
    
    print(f"\n💡 POUR LANCER LA COLLECTE AUTOMATIQUE:")
    print(f"   python start_automated_collection.py")
    
except Exception as e:
    print(f"\n❌ ERREUR DE CONNEXION:")
    print(f"   {str(e)}")
    print(f"\n💡 Vérifiez que MongoDB est démarré:")
    print(f"   docker start centralisation_db")

print("\n" + "="*66)

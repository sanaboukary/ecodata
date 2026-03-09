"""Afficher les données BRVM collectées aujourd'hui"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Date d'aujourd'hui
aujourdhui = datetime.now().strftime('%Y-%m-%d')

print("=" * 90)
print(f"📊 DONNÉES BRVM COLLECTÉES AUJOURD'HUI ({aujourdhui})")
print("=" * 90)

# Récupérer toutes les observations d'aujourd'hui
observations = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': aujourdhui
}).sort('key', 1))

if not observations:
    print(f"\n⚠️ Aucune donnée trouvée pour aujourd'hui ({aujourdhui})")
    print("\n🔍 Recherche des dates disponibles...")
    
    # Trouver les dates les plus récentes
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': '$ts'}},
        {'$sort': {'_id': -1}},
        {'$limit': 5}
    ]
    dates = list(db.curated_observations.aggregate(pipeline))
    print("\n📅 Dates disponibles (5 plus récentes):")
    for d in dates:
        count = db.curated_observations.count_documents({'source': 'BRVM', 'ts': d['_id']})
        print(f"  - {d['_id']}: {count} observations")
else:
    print(f"\n✅ {len(observations)} observations trouvées pour aujourd'hui\n")
    print(f"{'SYMBOLE':<10} {'NOM':<35} {'PRIX (FCFA)':>15} {'QUALITÉ':<20}")
    print("-" * 90)
    
    for obs in observations:
        symbol = obs.get('key', 'N/A')
        name = obs.get('attrs', {}).get('name', 'N/A')
        price = obs.get('value', 0)
        quality = obs.get('attrs', {}).get('data_quality', 'N/A')
        
        # Formater le prix avec séparateur de milliers
        prix_formate = f"{price:,.0f}".replace(',', ' ')
        
        print(f"{symbol:<10} {name:<35} {prix_formate:>15} {quality:<20}")
    
    print("\n" + "=" * 90)
    print(f"📈 Total: {len(observations)} actions")
    
    # Statistiques sur la qualité des données
    quality_stats = {}
    for obs in observations:
        quality = obs.get('attrs', {}).get('data_quality', 'UNKNOWN')
        quality_stats[quality] = quality_stats.get(quality, 0) + 1
    
    print("\n📊 Répartition par qualité:")
    for quality, count in quality_stats.items():
        print(f"  {quality}: {count} observations")
    
    # Vérifier Sonatel spécifiquement
    snts = next((o for o in observations if o.get('key') == 'SNTS'), None)
    if snts:
        snts_price = snts.get('value', 0)
        print(f"\n🔍 Prix Sonatel (SNTS): {snts_price:,.0f} FCFA")
        if snts_price == 25500:
            print("   ✅ Prix correct (25 500 FCFA)")
        else:
            print(f"   ⚠️ Prix différent de 25 500 FCFA")

print("\n" + "=" * 90)

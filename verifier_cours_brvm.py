"""Vérifier les cours BRVM réels dans MongoDB"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
cours_reels = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': 'REAL_MANUAL'
})
cours_simules = total_brvm - cours_reels

print(f"\n📊 ÉTAT DES COURS BRVM:\n")
print(f"   Total observations BRVM: {total_brvm}")
print(f"   ✅ Cours réels (manuels): {cours_reels}")
print(f"   ⚠️  Cours simulés (anciens): {cours_simules}")

if cours_reels > 0:
    print(f"\n✅ Les cours réels sont maintenant dans la base !")
    print(f"   Vérifiez sur: http://localhost:8000/dashboard/brvm/\n")
    
    # Afficher un échantillon
    sample = list(db.curated_observations.find(
        {'source': 'BRVM', 'attrs.data_quality': 'REAL_MANUAL'},
        limit=5
    ).sort('ts', -1))
    
    if sample:
        print("📋 Échantillon des derniers cours:\n")
        for obs in sample:
            print(f"   {obs['key']:8s} | {obs['value']:8.0f} FCFA | {obs['attrs'].get('day_change_pct', 0):+6.2f}%")
else:
    print(f"\n⚠️ Aucun cours réel trouvé. Lancez:")
    print(f"   python mettre_a_jour_cours_brvm.py\n")

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

try:
    client, db = get_mongo_db()
    print("Connexion MongoDB: OK")
    
    today = "2026-01-05"
    count_today = db.curated_observations.count_documents({"source": "BRVM", "ts": today})
    total_brvm = db.curated_observations.count_documents({"source": "BRVM"})
    
    print(f"\nObservations BRVM aujourd'hui ({today}): {count_today}")
    print(f"Total observations BRVM: {total_brvm}")
    
    if count_today > 0:
        print(f"\n✅ COLLECTE EFFECTUEE AUJOURD'HUI")
    else:
        print(f"\n❌ AUCUNE COLLECTE AUJOURD'HUI")
        
        # Trouver la dernière date
        last = list(db.curated_observations.find({"source": "BRVM"}).sort("ts", -1).limit(1))
        if last:
            print(f"Dernière collecte: {last[0]['ts']}")
        
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()

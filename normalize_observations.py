#!/usr/bin/env python3
"""
Script pour normaliser la structure des observations MongoDB
Objectif : Uniformiser tous les documents avec la même structure
"""
import os
import sys
import django
from datetime import datetime
from dateutil import parser as date_parser

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("=" * 100)
print("NORMALISATION DES OBSERVATIONS")
print("=" * 100)

# Schéma cible uniforme :
# {
#   "source": str,
#   "dataset": str,
#   "key": str,
#   "timestamp": datetime,
#   "value": float,
#   "attributes": dict,
#   "created_at": datetime,
#   "updated_at": datetime
# }

def parse_timestamp(ts_value):
    """Convertir une chaîne de date en datetime"""
    if isinstance(ts_value, datetime):
        return ts_value
    if isinstance(ts_value, str):
        try:
            return date_parser.parse(ts_value)
        except:
            return None
    return None

def normalize_observation(obs):
    """Normaliser une observation vers le schéma cible"""
    normalized = {
        "source": obs.get("source"),
        "created_at": obs.get("created_at", datetime.utcnow()),
        "updated_at": datetime.utcnow()
    }
    
    # Normaliser le timestamp
    ts = obs.get("ts") or obs.get("timestamp")
    normalized["timestamp"] = parse_timestamp(ts)
    
    # Normaliser la valeur
    normalized["value"] = obs.get("value")
    
    # Normaliser dataset, key, attributes selon la source
    if obs.get("source") == "WorldBank":
        # WorldBank utilise indicator/metadata
        normalized["dataset"] = obs.get("indicator")
        normalized["key"] = obs.get("metadata", {}).get("country")
        normalized["attributes"] = obs.get("metadata", {})
    else:
        # Autres sources utilisent dataset/key/attrs
        normalized["dataset"] = obs.get("dataset")
        normalized["key"] = obs.get("key")
        normalized["attributes"] = obs.get("attrs", {})
    
    return normalized

# Analyser chaque source
sources = db.curated_observations.distinct('source')
print(f"\nSources trouvées: {sources}\n")

total_updated = 0
total_errors = 0

for source in sources:
    print(f"\n{'─' * 100}")
    print(f"NORMALISATION: {source}")
    print(f"{'─' * 100}")
    
    count = db.curated_observations.count_documents({'source': source})
    print(f"Total observations: {count}")
    
    updated = 0
    errors = 0
    
    # Traiter en batch
    batch_size = 100
    cursor = db.curated_observations.find({'source': source})
    
    for obs in cursor:
        try:
            normalized = normalize_observation(obs)
            
            # Mise à jour du document
            db.curated_observations.update_one(
                {'_id': obs['_id']},
                {'$set': normalized}
            )
            updated += 1
            
            if updated % 100 == 0:
                print(f"  Traité: {updated}/{count}", end='\r')
                
        except Exception as e:
            errors += 1
            print(f"\n  Erreur sur {obs.get('_id')}: {e}")
    
    print(f"\n  ✅ Mis à jour: {updated}")
    if errors > 0:
        print(f"  ❌ Erreurs: {errors}")
    
    total_updated += updated
    total_errors += errors

# Créer les index
print(f"\n\n{'─' * 100}")
print("CRÉATION DES INDEX")
print(f"{'─' * 100}")

indexes = [
    [("source", 1), ("dataset", 1), ("key", 1), ("timestamp", 1)],
    [("source", 1), ("timestamp", -1)],
    [("dataset", 1), ("timestamp", -1)],
]

for idx in indexes:
    idx_name = db.curated_observations.create_index(idx)
    print(f"  ✅ Index créé: {idx_name}")

# Résumé
print(f"\n\n{'=' * 100}")
print("RÉSUMÉ")
print(f"{'=' * 100}")
print(f"Total observations traitées: {total_updated}")
print(f"Total erreurs: {total_errors}")

# Vérifier le résultat
print(f"\n\nVÉRIFICATION:")
for source in sources:
    count_with_ts = db.curated_observations.count_documents({
        'source': source,
        'timestamp': {'$ne': None}
    })
    count_total = db.curated_observations.count_documents({'source': source})
    print(f"  {source}: {count_with_ts}/{count_total} avec timestamp valide")

client.close()
print("\n✅ Normalisation terminée!")

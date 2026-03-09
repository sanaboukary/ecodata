#!/usr/bin/env python3
"""TEST SIMPLE ENRICHISSEMENT"""
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Import direct du dictionnaire
exec(open("collecter_publications_brvm.py", encoding="utf-8").read().split("class Collecteur")[0])

_, db = get_mongo_db()

print("\n✅ Connexion MongoDB OK")
count = db.curated_observations.count_documents({"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}})
print(f"📊 {count} publications trouvées")

# Test sur 1 publication
pub = db.curated_observations.find_one({"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}})
if pub:
    attrs = pub.get("attrs", {})
    titre = attrs.get("titre", "")
    print(f"\n📰 Exemple : {titre}")
    
    symboles = extraire_symboles(titre)
    type_event = detecter_type_event(titre)
    
    print(f"   Symboles  : {symboles}")
    print(f"   Type      : {type_event}")
    
    if symboles:
        print(f"\n✅ Extraction fonctionne - Prêt pour enrichissement")
    else:
        print(f"\n⚠️  Aucun symbole détecté dans cet exemple")

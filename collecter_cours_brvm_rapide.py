#!/usr/bin/env python3
"""
🚀 COLLECTE RAPIDE COURS BRVM
Collecte les cours actuels des 47 actions BRVM
"""

import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.pipeline import run_ingestion

print("=" * 80)
print("🚀 COLLECTE COURS BRVM")
print("=" * 80)
print()

# Vérifier données existantes
_, db = get_mongo_db()
total_avant = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': {'$ne': 'PUBLICATION'}
})

print(f"📊 Cours en base avant collecte : {total_avant}")
print()

# Lancer ingestion
print("🔄 Lancement de l'ingestion BRVM...")
print()

try:
    result = run_ingestion('brvm')
    
    print()
    print("=" * 80)
    print("✅ COLLECTE TERMINÉE")
    print("=" * 80)
    
    # Compter après
    total_apres = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': {'$ne': 'PUBLICATION'}
    })
    
    nouveaux = total_apres - total_avant
    
    print(f"📊 Cours en base après collecte : {total_apres}")
    print(f"➕ Nouveaux cours ajoutés        : {nouveaux}")
    print()
    
    # Dernières données
    if total_apres > 0:
        latest = db.curated_observations.find_one(
            {'source': 'BRVM', 'dataset': {'$ne': 'PUBLICATION'}},
            sort=[('ts', -1)]
        )
        if latest:
            print(f"📅 Dernière date : {latest.get('ts', 'N/A')[:10]}")
            print(f"📈 Exemple cours : {latest.get('key')} = {latest.get('value')} FCFA")
    
    print()
    print("🔍 Vérifier dashboard : http://127.0.0.1:8000/brvm/")
    print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print("❌ ERREUR LORS DE LA COLLECTE")
    print("=" * 80)
    print(f"Erreur : {e}")
    print()
    print("💡 Solutions :")
    print("   1. Vérifier que MongoDB est démarré")
    print("   2. Vérifier la connexion internet")
    print("   3. Essayer la saisie manuelle : mettre_a_jour_cours_brvm.py")
    print("=" * 80)
    sys.exit(1)

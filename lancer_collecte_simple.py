#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lancement simple de la collecte BRVM"""

import sys
import os

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion
from datetime import datetime

print("\n" + "="*80)
print(f"🚀 LANCEMENT COLLECTE BRVM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

try:
    # Lancer l'ingestion BRVM
    print("📡 Démarrage de la collecte BRVM...")
    result = run_ingestion('brvm')
    
    print(f"\n✅ Collecte terminée avec succès !")
    print(f"📊 Résultat : {result}")
    
    # Vérifier les données collectées
    from plateforme_centralisation.mongo import get_mongo_db
    client, db = get_mongo_db()
    
    today = datetime.now().strftime('%Y-%m-%d')
    count_today = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': today
    })
    
    count_total = db.curated_observations.count_documents({'source': 'BRVM'})
    
    print(f"\n📈 Statistiques :")
    print(f"   - Observations BRVM aujourd'hui : {count_today}")
    print(f"   - Total observations BRVM : {count_total}")
    
    if count_today > 0:
        print(f"\n✨ {count_today} nouvelles observations collectées aujourd'hui !")
    else:
        print(f"\n⚠️  Aucune nouvelle observation aujourd'hui")
    
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ Erreur lors de la collecte : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

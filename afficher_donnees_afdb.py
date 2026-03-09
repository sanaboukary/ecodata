#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Afficher les données de la Banque Africaine de Développement (AfDB)
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def afficher_donnees_afdb():
    """Affiche les données AfDB depuis MongoDB"""
    
    print("=" * 80)
    print("📊 DONNÉES BANQUE AFRICAINE DE DÉVELOPPEMENT (AfDB)")
    print("=" * 80)
    print()
    
    try:
        client, db = get_mongo_db()
        
        # 1. Compter total observations AfDB
        total_afdb = db.curated_observations.count_documents({'source': 'AfDB'})
        print(f"✅ Total observations AfDB : {total_afdb:,}")
        print()
        
        if total_afdb == 0:
            print("⚠️  AUCUNE DONNÉE AfDB TROUVÉE")
            print()
            
            # Vérifier autres sources possibles
            print("Vérification d'autres noms de sources possibles...")
            sources = db.curated_observations.distinct('source')
            afdb_sources = [s for s in sources if 'afdb' in s.lower() or 'bad' in s.lower()]
            
            if afdb_sources:
                print(f"Sources trouvées : {afdb_sources}")
                for source in afdb_sources:
                    count = db.curated_observations.count_documents({'source': source})
                    print(f"  - {source}: {count:,} observations")
            else:
                print("❌ Aucune source AfDB/BAD trouvée")
                print()
                print("Sources disponibles dans la base:")
                for source in sources:
                    count = db.curated_observations.count_documents({'source': source})
                    print(f"  - {source}: {count:,} observations")
            
            return
        
        # 2. Datasets disponibles
        print("📁 Datasets AfDB:")
        datasets = db.curated_observations.distinct('dataset', {'source': 'AfDB'})
        for dataset in sorted(datasets):
            count = db.curated_observations.count_documents({
                'source': 'AfDB',
                'dataset': dataset
            })
            print(f"  - {dataset}: {count:,} observations")
        print()
        
        # 3. Pays couverts
        print("🌍 Pays couverts:")
        keys = db.curated_observations.distinct('key', {'source': 'AfDB'})
        print(f"  Total: {len(keys)} pays")
        for key in sorted(keys)[:20]:  # Afficher max 20
            count = db.curated_observations.count_documents({
                'source': 'AfDB',
                'key': key
            })
            print(f"  - {key}: {count:,} observations")
        
        if len(keys) > 20:
            print(f"  ... et {len(keys) - 20} autres pays")
        print()
        
        # 4. Période couverte
        print("📅 Période couverte:")
        pipeline = [
            {'$match': {'source': 'AfDB'}},
            {'$group': {
                '_id': None,
                'date_min': {'$min': '$ts'},
                'date_max': {'$max': '$ts'}
            }}
        ]
        result = list(db.curated_observations.aggregate(pipeline))
        if result:
            print(f"  De: {result[0]['date_min']}")
            print(f"  À:  {result[0]['date_max']}")
        print()
        
        # 5. Exemples de données (10 dernières)
        print("📋 Exemples de données (10 dernières observations):")
        print("-" * 80)
        
        examples = list(db.curated_observations.find(
            {'source': 'AfDB'}
        ).sort('ts', -1).limit(10))
        
        for i, doc in enumerate(examples, 1):
            print(f"\n{i}. {doc.get('key')} - {doc.get('dataset')} ({doc.get('ts')})")
            print(f"   Valeur: {doc.get('value')}")
            if doc.get('attrs'):
                print(f"   Attributs: {doc.get('attrs')}")
        
        print()
        print("=" * 80)
        
        # 6. Statistiques par dataset
        print("\n📊 STATISTIQUES DÉTAILLÉES PAR DATASET:")
        print("-" * 80)
        
        for dataset in sorted(datasets):
            print(f"\n{dataset}:")
            
            # Compter par pays
            pipeline = [
                {'$match': {'source': 'AfDB', 'dataset': dataset}},
                {'$group': {
                    '_id': '$key',
                    'count': {'$sum': 1},
                    'derniere_date': {'$max': '$ts'}
                }},
                {'$sort': {'count': -1}}
            ]
            
            pays_stats = list(db.curated_observations.aggregate(pipeline))
            
            print(f"  Pays couverts: {len(pays_stats)}")
            print(f"  Top 5 pays (par nombre d'observations):")
            
            for stat in pays_stats[:5]:
                print(f"    - {stat['_id']}: {stat['count']} observations (dernière: {stat['derniere_date']})")
        
        print()
        print("=" * 80)
        print("✅ Affichage terminé")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    afficher_donnees_afdb()

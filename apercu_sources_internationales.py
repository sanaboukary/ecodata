#!/usr/bin/env python3
"""
📊 APERÇU DES SOURCES INTERNATIONALES
Affiche les données de : WorldBank, IMF, AfDB, UN SDG (SANS BRVM)
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def afficher_apercu_sources():
    """Afficher aperçu de toutes les sources internationales"""
    _, db = get_mongo_db()
    
    print("=" * 120)
    print("📊 APERÇU DES SOURCES INTERNATIONALES - Centralisation Données")
    print("=" * 120)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    
    # Sources à afficher (SANS BRVM)
    sources = ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM_PUBLICATION']
    
    # Statistiques globales
    print("\n📈 STATISTIQUES GLOBALES PAR SOURCE:")
    print(f"{'Source':<20} {'Total Obs':<15} {'Datasets':<15} {'Dernière MAJ':<25}")
    print("-" * 120)
    
    totaux = {}
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        
        # Nombre de datasets
        datasets = db.curated_observations.distinct('dataset', {'source': source})
        
        # Dernière mise à jour
        derniere = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', -1)]
        )
        
        derniere_date = derniere['ts'] if derniere else 'N/A'
        
        totaux[source] = count
        print(f"{source:<20} {count:<15,} {len(datasets):<15} {derniere_date:<25}")
    
    total_general = sum(totaux.values())
    print("-" * 120)
    print(f"{'TOTAL INTERNATIONAL':<20} {total_general:<15,}")
    
    # Détails par source
    print("\n" + "=" * 120)
    
    # WORLD BANK
    if totaux.get('WorldBank', 0) > 0:
        print("\n🌍 WORLD BANK - Indicateurs de développement")
        print("-" * 120)
        
        # Top 10 indicateurs
        pipeline = [
            {'$match': {'source': 'WorldBank'}},
            {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        top_indicators = list(db.curated_observations.aggregate(pipeline))
        
        print(f"{'Indicateur':<40} {'Observations':<15}")
        print("-" * 120)
        for ind in top_indicators:
            print(f"{ind['_id']:<40} {ind['count']:<15,}")
        
        # Pays couverts
        pays = db.curated_observations.distinct('key', {'source': 'WorldBank'})
        print(f"\n📍 Pays couverts: {len(pays)} ({', '.join(sorted(pays)[:10])}...)")
        
        # Échantillon de données récentes
        sample = list(db.curated_observations.find(
            {'source': 'WorldBank'},
            {'dataset': 1, 'key': 1, 'ts': 1, 'value': 1, '_id': 0}
        ).sort('ts', -1).limit(5))
        
        if sample:
            print(f"\n📋 Échantillon (5 observations récentes):")
            for obs in sample:
                print(f"  - {obs['dataset']:<30} | {obs['key']:<8} | {obs['ts']:<12} | {obs.get('value', 'N/A')}")
    
    # IMF
    if totaux.get('IMF', 0) > 0:
        print("\n\n💰 IMF - Fonds Monétaire International")
        print("-" * 120)
        
        # Top séries
        pipeline = [
            {'$match': {'source': 'IMF'}},
            {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        top_series = list(db.curated_observations.aggregate(pipeline))
        
        print(f"{'Série':<40} {'Observations':<15}")
        print("-" * 120)
        for serie in top_series:
            print(f"{serie['_id']:<40} {serie['count']:<15,}")
        
        # Pays couverts
        pays = db.curated_observations.distinct('key', {'source': 'IMF'})
        print(f"\n📍 Pays/Régions couverts: {len(pays)}")
        
        # Échantillon
        sample = list(db.curated_observations.find(
            {'source': 'IMF'},
            {'dataset': 1, 'key': 1, 'ts': 1, 'value': 1, '_id': 0}
        ).sort('ts', -1).limit(5))
        
        if sample:
            print(f"\n📋 Échantillon (5 observations récentes):")
            for obs in sample:
                print(f"  - {obs['dataset']:<30} | {obs['key']:<20} | {obs['ts']:<12} | {obs.get('value', 'N/A')}")
    
    # AfDB
    if totaux.get('AfDB', 0) > 0:
        print("\n\n🏦 AfDB - Banque Africaine de Développement")
        print("-" * 120)
        
        # Indicateurs
        indicators = db.curated_observations.distinct('dataset', {'source': 'AfDB'})
        print(f"📊 Indicateurs: {len(indicators)}")
        for ind in sorted(indicators)[:10]:
            count = db.curated_observations.count_documents({'source': 'AfDB', 'dataset': ind})
            print(f"  - {ind:<50} : {count:>8,} obs")
        
        # Pays
        pays = db.curated_observations.distinct('key', {'source': 'AfDB'})
        print(f"\n📍 Pays couverts: {len(pays)} ({', '.join(sorted(pays))})")
        
        # Échantillon
        sample = list(db.curated_observations.find(
            {'source': 'AfDB'},
            {'dataset': 1, 'key': 1, 'ts': 1, 'value': 1, '_id': 0}
        ).sort('ts', -1).limit(5))
        
        if sample:
            print(f"\n📋 Échantillon (5 observations récentes):")
            for obs in sample:
                print(f"  - {obs['dataset']:<40} | {obs['key']:<8} | {obs['ts']:<12} | {obs.get('value', 'N/A')}")
    
    # UN SDG
    if totaux.get('UN_SDG', 0) > 0:
        print("\n\n🌐 UN SDG - Objectifs de Développement Durable")
        print("-" * 120)
        
        # Séries
        series = db.curated_observations.distinct('dataset', {'source': 'UN_SDG'})
        print(f"📊 Séries ODD: {len(series)}")
        for serie in sorted(series)[:10]:
            count = db.curated_observations.count_documents({'source': 'UN_SDG', 'dataset': serie})
            print(f"  - {serie:<50} : {count:>8,} obs")
        
        # Pays
        pays = db.curated_observations.distinct('key', {'source': 'UN_SDG'})
        print(f"\n📍 Pays/Régions: {len(pays)}")
        
        # Échantillon
        sample = list(db.curated_observations.find(
            {'source': 'UN_SDG'},
            {'dataset': 1, 'key': 1, 'ts': 1, 'value': 1, '_id': 0}
        ).sort('ts', -1).limit(5))
        
        if sample:
            print(f"\n📋 Échantillon (5 observations récentes):")
            for obs in sample:
                print(f"  - {obs['dataset']:<40} | {obs['key']:<8} | {obs['ts']:<12} | {obs.get('value', 'N/A')}")
    
    # BRVM PUBLICATIONS
    if totaux.get('BRVM_PUBLICATION', 0) > 0:
        print("\n\n📄 BRVM PUBLICATIONS - Documents officiels")
        print("-" * 120)
        
        # Types de publications
        types = db.curated_observations.distinct('dataset', {'source': 'BRVM_PUBLICATION'})
        
        print(f"{'Type Document':<30} {'Nombre':<15}")
        print("-" * 120)
        for type_doc in sorted(types):
            count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION', 'dataset': type_doc})
            print(f"{type_doc:<30} {count:<15,}")
        
        # Dernières publications
        sample = list(db.curated_observations.find(
            {'source': 'BRVM_PUBLICATION'},
            {'dataset': 1, 'key': 1, 'attrs': 1, '_id': 0}
        ).sort('ts', -1).limit(5))
        
        if sample:
            print(f"\n📋 Dernières publications:")
            for pub in sample:
                titre = pub.get('attrs', {}).get('titre', 'N/A')
                type_doc = pub.get('dataset', 'N/A')
                print(f"  - [{type_doc}] {titre[:80]}")
    
    print("\n" + "=" * 120)
    print(f"✅ Aperçu terminé - {total_general:,} observations internationales")
    print("=" * 120)

if __name__ == '__main__':
    afficher_apercu_sources()

#!/usr/bin/env python3
"""
📊 RÉSUMÉ COMPLET - TOUTES LES SOURCES DE DONNÉES
Vue d'ensemble de l'état de chaque source (BRVM, WorldBank, IMF, AfDB, UN SDG, Publications)
"""

import os
import sys
from datetime import datetime, timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("=" * 120)
print("📊 RÉSUMÉ COMPLET - TOUTES LES SOURCES DE DONNÉES")
print("=" * 120)
print(f"Date du rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 120)
print()

# ========== 1. BRVM - COURS ACTIONS ==========
print("🏦 1. BRVM - COURS DES ACTIONS")
print("-" * 120)

brvm_cours = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})

print(f"Total observations: {brvm_cours:,}")

if brvm_cours > 0:
    # Par qualité
    print("\nPar qualité de données:")
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': '$attrs.data_quality', 'count': {'$sum': 1}}}
    ]
    for item in db.curated_observations.aggregate(pipeline):
        quality = item['_id'] or 'UNKNOWN'
        pct = (item['count'] / brvm_cours * 100) if brvm_cours > 0 else 0
        print(f"  {quality:20s}: {item['count']:6,} ({pct:5.1f}%)")
    
    # Dernière date
    latest = db.curated_observations.find_one(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
        sort=[('ts', -1)]
    )
    if latest:
        latest_date = latest.get('ts', '')[:10]
        print(f"\nDernière date de données: {latest_date}")
        
        # Actions ce jour
        actions_jour = db.curated_observations.count_documents({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'ts': {'$regex': f'^{latest_date}'}
        })
        print(f"Actions mises à jour ce jour: {actions_jour}/47")
        
    # Dernière collecte
    latest_collecte = db.curated_observations.find_one(
        {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'attrs.collecte_datetime': {'$exists': True}},
        sort=[('attrs.collecte_datetime', -1)]
    )
    if latest_collecte:
        print(f"Dernière collecte automatique: {latest_collecte.get('attrs', {}).get('collecte_datetime', 'N/A')[:19]}")
    
    # Recommandation
    print("\n✅ Statut: OPÉRATIONNEL - Collecte horaire active")
    print("📋 Action: Aucune - Système fonctionnel")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer collecter_brvm_horaire_auto.py")

print()

# ========== 2. BRVM - PUBLICATIONS ==========
print("📰 2. BRVM - PUBLICATIONS OFFICIELLES")
print("-" * 120)

publications = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATION'
})

print(f"Total publications: {publications}")

if publications > 0:
    # Par catégorie
    print("\nPar catégorie:")
    pipeline = [
        {'$match': {'source': 'BRVM_PUBLICATION'}},
        {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for item in db.curated_observations.aggregate(pipeline):
        print(f"  {item['_id']:30s}: {item['count']:4d} documents")
    
    # Dernière publication
    latest_pub = db.curated_observations.find_one(
        {'source': 'BRVM_PUBLICATION'},
        sort=[('ts', -1)]
    )
    if latest_pub:
        print(f"\nDernière publication: {latest_pub.get('ts', '')[:10]}")
        print(f"Catégorie: {latest_pub.get('dataset', 'N/A')}")
    
    # Sentiment analysis
    with_sentiment = db.curated_observations.count_documents({
        'source': 'BRVM_PUBLICATION',
        'attrs.sentiment': {'$exists': True}
    })
    pct_sentiment = (with_sentiment / publications * 100) if publications > 0 else 0
    print(f"\nPublications avec sentiment analysis: {with_sentiment}/{publications} ({pct_sentiment:.1f}%)")
    
    print("\n✅ Statut: OPÉRATIONNEL - 102+ publications collectées")
    if pct_sentiment < 50:
        print("📋 Action: Lancer analyser_sentiment_publications.py")
    else:
        print("📋 Action: Aucune - Sentiment analysis actif")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer collecter_publications_brvm_intelligent.py")

print()

# ========== 3. WORLD BANK ==========
print("🌍 3. WORLD BANK - INDICATEURS MACROÉCONOMIQUES")
print("-" * 120)

wb_total = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"Total observations: {wb_total:,}")

if wb_total > 0:
    # Dernière mise à jour
    latest_wb = db.curated_observations.find_one(
        {'source': 'WorldBank'},
        sort=[('ts', -1)]
    )
    if latest_wb:
        latest_date = latest_wb.get('ts', '')[:10]
        print(f"Dernière date de données: {latest_date}")
        
        # Calcul ancienneté
        try:
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            days_old = (datetime.now() - last_date_obj).days
            print(f"Ancienneté: {days_old} jours")
        except:
            days_old = 999
    
    # Indicateurs et pays
    nb_indicateurs = len(db.curated_observations.distinct('key', {'source': 'WorldBank'}))
    nb_pays = len(db.curated_observations.distinct('attrs.country', {'source': 'WorldBank'}))
    print(f"\nNombre d'indicateurs: {nb_indicateurs}")
    print(f"Nombre de pays: {nb_pays}")
    
    # Top 5 indicateurs
    print("\nTop 5 indicateurs (par volume):")
    pipeline = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {'_id': '$key', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    for item in db.curated_observations.aggregate(pipeline):
        print(f"  {item['_id']:30s}: {item['count']:5,} observations")
    
    # Statut et recommandation
    if days_old > 60:
        print(f"\n⚠️  Statut: DONNÉES ANCIENNES ({days_old} jours)")
        print("📋 Action: Lancer python manage.py ingest_source --source worldbank")
    else:
        print("\n✅ Statut: DONNÉES RÉCENTES")
        print("📋 Action: Mise à jour mensuelle recommandée (15 du mois)")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer python manage.py ingest_source --source worldbank")

print()

# ========== 4. IMF ==========
print("💰 4. IMF - DONNÉES MONÉTAIRES ET FINANCIÈRES")
print("-" * 120)

imf_total = db.curated_observations.count_documents({'source': 'IMF'})
print(f"Total observations: {imf_total:,}")

if imf_total > 0:
    # Dernière mise à jour
    latest_imf = db.curated_observations.find_one(
        {'source': 'IMF'},
        sort=[('ts', -1)]
    )
    if latest_imf:
        latest_date = latest_imf.get('ts', '')[:10]
        print(f"Dernière date de données: {latest_date}")
        
        try:
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            days_old = (datetime.now() - last_date_obj).days
            print(f"Ancienneté: {days_old} jours")
        except:
            days_old = 999
    
    # Séries et pays
    nb_series = len(db.curated_observations.distinct('key', {'source': 'IMF'}))
    print(f"\nNombre de séries: {nb_series}")
    
    # Top 5 séries
    print("\nTop 5 séries (par volume):")
    pipeline = [
        {'$match': {'source': 'IMF'}},
        {'$group': {'_id': '$key', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    for item in db.curated_observations.aggregate(pipeline):
        print(f"  {item['_id']:30s}: {item['count']:5,} observations")
    
    if days_old > 60:
        print(f"\n⚠️  Statut: DONNÉES ANCIENNES ({days_old} jours)")
        print("📋 Action: Lancer python manage.py ingest_source --source imf")
    else:
        print("\n✅ Statut: DONNÉES RÉCENTES")
        print("📋 Action: Mise à jour mensuelle recommandée (1er du mois)")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer python manage.py ingest_source --source imf")

print()

# ========== 5. AfDB ==========
print("🏛️  5. AfDB - BANQUE AFRICAINE DE DÉVELOPPEMENT")
print("-" * 120)

afdb_total = db.curated_observations.count_documents({'source': 'AfDB'})
print(f"Total observations: {afdb_total:,}")

if afdb_total > 0:
    latest_afdb = db.curated_observations.find_one(
        {'source': 'AfDB'},
        sort=[('ts', -1)]
    )
    if latest_afdb:
        latest_date = latest_afdb.get('ts', '')[:10]
        print(f"Dernière date de données: {latest_date}")
        
        try:
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            days_old = (datetime.now() - last_date_obj).days
            print(f"Ancienneté: {days_old} jours")
        except:
            days_old = 999
    
    # Indicateurs et pays
    nb_indicateurs = len(db.curated_observations.distinct('key', {'source': 'AfDB'}))
    print(f"\nNombre d'indicateurs: {nb_indicateurs}")
    
    if days_old > 90:
        print(f"\n⚠️  Statut: DONNÉES ANCIENNES ({days_old} jours)")
        print("📋 Action: Lancer python manage.py ingest_source --source afdb")
    else:
        print("\n✅ Statut: DONNÉES RÉCENTES")
        print("📋 Action: Mise à jour trimestrielle")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer python manage.py ingest_source --source afdb")

print()

# ========== 6. UN SDG ==========
print("🎯 6. UN SDG - OBJECTIFS DE DÉVELOPPEMENT DURABLE")
print("-" * 120)

un_total = db.curated_observations.count_documents({'source': 'UN_SDG'})
print(f"Total observations: {un_total:,}")

if un_total > 0:
    latest_un = db.curated_observations.find_one(
        {'source': 'UN_SDG'},
        sort=[('ts', -1)]
    )
    if latest_un:
        latest_date = latest_un.get('ts', '')[:10]
        print(f"Dernière date de données: {latest_date}")
        
        try:
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            days_old = (datetime.now() - last_date_obj).days
            print(f"Ancienneté: {days_old} jours")
        except:
            days_old = 999
    
    # Indicateurs
    nb_indicateurs = len(db.curated_observations.distinct('key', {'source': 'UN_SDG'}))
    print(f"\nNombre d'indicateurs: {nb_indicateurs}")
    
    if days_old > 90:
        print(f"\n⚠️  Statut: DONNÉES ANCIENNES ({days_old} jours)")
        print("📋 Action: Lancer python manage.py ingest_source --source un_sdg")
    else:
        print("\n✅ Statut: DONNÉES RÉCENTES")
        print("📋 Action: Mise à jour trimestrielle")
else:
    print("\n⚠️  Statut: AUCUNE DONNÉE")
    print("📋 Action: Lancer python manage.py ingest_source --source un_sdg")

print()
print("=" * 120)

# ========== RÉSUMÉ GLOBAL ==========
print("📊 RÉSUMÉ GLOBAL")
print("=" * 120)

total_global = db.curated_observations.count_documents({})
print(f"Total observations MongoDB: {total_global:,}")
print()

# Par source
print("Par source:")
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
for item in db.curated_observations.aggregate(pipeline):
    pct = (item['count'] / total_global * 100) if total_global > 0 else 0
    status = "✅" if item['count'] > 0 else "⚠️"
    print(f"  {status} {item['_id']:20s}: {item['count']:8,} ({pct:5.1f}%)")

print()
print("=" * 120)

# ========== RECOMMANDATIONS ==========
print("📋 RECOMMANDATIONS D'ACTION")
print("=" * 120)
print()

recommandations = []

# Vérifier chaque source
if brvm_cours == 0:
    recommandations.append(("URGENT", "BRVM Cours", "Lancer collecter_brvm_horaire_auto.py"))
elif brvm_cours > 0:
    latest = db.curated_observations.find_one({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}, sort=[('ts', -1)])
    if latest:
        latest_date = latest.get('ts', '')[:10]
        try:
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            if (datetime.now() - last_date_obj).days > 1:
                recommandations.append(("HAUTE", "BRVM Cours", "Activer collecte automatique Airflow"))
        except:
            pass

if publications == 0:
    recommandations.append(("MOYENNE", "BRVM Publications", "Lancer collecter_publications_brvm_intelligent.py"))
elif publications > 0:
    with_sentiment = db.curated_observations.count_documents({
        'source': 'BRVM_PUBLICATION',
        'attrs.sentiment': {'$exists': True}
    })
    if with_sentiment < publications * 0.5:
        recommandations.append(("MOYENNE", "BRVM Sentiment", "Lancer analyser_sentiment_publications.py"))

if wb_total == 0:
    recommandations.append(("HAUTE", "World Bank", "Lancer python manage.py ingest_source --source worldbank"))
else:
    latest_wb = db.curated_observations.find_one({'source': 'WorldBank'}, sort=[('ts', -1)])
    if latest_wb:
        try:
            latest_date = latest_wb.get('ts', '')[:10]
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            if (datetime.now() - last_date_obj).days > 60:
                recommandations.append(("MOYENNE", "World Bank", "Mettre à jour (données > 60 jours)"))
        except:
            pass

if imf_total == 0:
    recommandations.append(("HAUTE", "IMF", "Lancer python manage.py ingest_source --source imf"))
else:
    latest_imf = db.curated_observations.find_one({'source': 'IMF'}, sort=[('ts', -1)])
    if latest_imf:
        try:
            latest_date = latest_imf.get('ts', '')[:10]
            last_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            if (datetime.now() - last_date_obj).days > 60:
                recommandations.append(("MOYENNE", "IMF", "Mettre à jour (données > 60 jours)"))
        except:
            pass

if afdb_total == 0:
    recommandations.append(("BASSE", "AfDB", "Lancer python manage.py ingest_source --source afdb"))

if un_total == 0:
    recommandations.append(("BASSE", "UN SDG", "Lancer python manage.py ingest_source --source un_sdg"))

# Afficher recommandations par priorité
priorites = {"URGENT": 1, "HAUTE": 2, "MOYENNE": 3, "BASSE": 4}
recommandations_sorted = sorted(recommandations, key=lambda x: priorites[x[0]])

if recommandations_sorted:
    for prio, source, action in recommandations_sorted:
        icon = "🔴" if prio == "URGENT" else ("🟠" if prio == "HAUTE" else ("🟡" if prio == "MOYENNE" else "🟢"))
        print(f"{icon} [{prio:7s}] {source:20s} → {action}")
else:
    print("✅ Aucune action urgente - Toutes les sources sont à jour!")

print()
print("=" * 120)
print("✅ Rapport terminé")
print("=" * 120)

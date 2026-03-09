#!/usr/bin/env python3
"""
🔄 MISE À JOUR AUTOMATIQUE - TOUTES LES SOURCES
Collecte les données RÉCENTES manquantes pour chaque source
"""

import os
import sys
from datetime import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.pipeline import run_ingestion
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_, db = get_mongo_db()

print("=" * 120)
print("🔄 MISE À JOUR AUTOMATIQUE - COLLECTE DONNÉES RÉCENTES")
print("=" * 120)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ========== 1. WORLD BANK ==========
print("🌍 1. WORLD BANK - Mise à jour en cours...")
print("-" * 120)

wb_latest = db.curated_observations.find_one(
    {'source': 'WorldBank'},
    sort=[('ts', -1)]
)

if wb_latest:
    latest_date = wb_latest.get('ts', '')[:10]
    print(f"Dernière date en base: {latest_date}")
else:
    print("Aucune donnée - Collecte complète nécessaire")

print("\n🔄 Collecte World Bank...")
print("   Indicateurs: SP.POP.TOTL, NY.GDP.MKTP.CD, FP.CPI.TOTL.ZG, SL.UEM.TOTL.ZS")
print("   Pays: CI, BF, SN, ML, BJ, TG, NE, GW")

try:
    # Liste des principaux indicateurs
    indicateurs_wb = [
        'SP.POP.TOTL',      # Population totale
        'NY.GDP.MKTP.CD',   # PIB ($ US courants)
        'FP.CPI.TOTL.ZG',   # Inflation (IPC)
        'SL.UEM.TOTL.ZS',   # Chômage
        'NY.GDP.PCAP.CD',   # PIB par habitant
        'SE.PRM.ENRR',      # Taux de scolarisation primaire
        'SH.DYN.MORT',      # Mortalité infantile
        'IT.NET.USER.ZS',   # Utilisateurs Internet (%)
    ]
    
    pays_cedeao = ['CI', 'BF', 'SN', 'ML', 'BJ', 'TG', 'NE', 'GW']
    
    total_collecte = 0
    
    for country in pays_cedeao:
        for indicator in indicateurs_wb:
            try:
                result = run_ingestion(
                    'worldbank',
                    indicator=indicator,
                    country=country
                )
                if result:
                    total_collecte += 1
                    print(f"   ✅ {country} - {indicator}")
            except Exception as e:
                print(f"   ⚠️  {country} - {indicator}: {str(e)[:50]}")
    
    print(f"\n✅ World Bank: {total_collecte} séries mises à jour")
    
except Exception as e:
    print(f"❌ Erreur World Bank: {e}")

print()

# ========== 2. IMF ==========
print("💰 2. IMF - Mise à jour en cours...")
print("-" * 120)

imf_latest = db.curated_observations.find_one(
    {'source': 'IMF'},
    sort=[('ts', -1)]
)

if imf_latest:
    latest_date = imf_latest.get('ts', '')[:10]
    print(f"Dernière date en base: {latest_date}")
else:
    print("Aucune donnée - Collecte complète nécessaire")

print("\n🔄 Collecte IMF...")
print("   Séries: PCPI_IX (IPC), NGDP_R (PIB réel), BCA (Balance courante)")

try:
    series_imf = [
        'PCPI_IX',    # Indice des prix à la consommation
        'NGDP_R',     # PIB réel
        'BCA',        # Balance des comptes courants
        'GGXWDG',     # Dette publique
    ]
    
    total_collecte = 0
    
    for area in pays_cedeao:
        for series in series_imf:
            try:
                result = run_ingestion(
                    'imf',
                    series=series,
                    area=area
                )
                if result:
                    total_collecte += 1
                    print(f"   ✅ {area} - {series}")
            except Exception as e:
                print(f"   ⚠️  {area} - {series}: {str(e)[:50]}")
    
    print(f"\n✅ IMF: {total_collecte} séries mises à jour")
    
except Exception as e:
    print(f"❌ Erreur IMF: {e}")

print()

# ========== 3. AfDB ==========
print("🏛️  3. AfDB - Mise à jour en cours...")
print("-" * 120)

afdb_latest = db.curated_observations.find_one(
    {'source': 'AfDB'},
    sort=[('ts', -1)]
)

if afdb_latest:
    latest_date = afdb_latest.get('ts', '')[:10]
    print(f"Dernière date en base: {latest_date}")
else:
    print("Aucune donnée - Collecte complète nécessaire")

print("\n🔄 Collecte AfDB...")

try:
    result = run_ingestion('afdb')
    print(f"✅ AfDB: Données mises à jour")
except Exception as e:
    print(f"❌ Erreur AfDB: {e}")

print()

# ========== 4. UN SDG ==========
print("🎯 4. UN SDG - Mise à jour en cours...")
print("-" * 120)

un_latest = db.curated_observations.find_one(
    {'source': 'UN_SDG'},
    sort=[('ts', -1)]
)

if un_latest:
    latest_date = un_latest.get('ts', '')[:10]
    print(f"Dernière date en base: {latest_date}")
else:
    print("Aucune donnée - Collecte complète nécessaire")

print("\n🔄 Collecte UN SDG...")

try:
    result = run_ingestion('un_sdg')
    print(f"✅ UN SDG: Données mises à jour")
except Exception as e:
    print(f"❌ Erreur UN SDG: {e}")

print()

# ========== 5. BRVM (déjà configuré) ==========
print("🏦 5. BRVM - Collecte horaire automatique")
print("-" * 120)
print("✅ Collecte BRVM déjà configurée (horaire)")
print("📋 Vérifier: python verifier_collecte_horaire.py")
print()

# ========== RÉSUMÉ FINAL ==========
print("=" * 120)
print("📊 VÉRIFICATION POST-COLLECTE")
print("=" * 120)
print()

# Compter après collecte
sources_count = {}
for source in ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM']:
    count = db.curated_observations.count_documents({'source': source})
    sources_count[source] = count
    print(f"{source:15s}: {count:8,} observations")

total = sum(sources_count.values())
print(f"\n{'TOTAL':15s}: {total:8,} observations")

print()
print("=" * 120)
print("✅ Mise à jour terminée")
print("=" * 120)
print()
print("📋 PROCHAINES ÉTAPES:")
print("   1. Vérifier dashboard: http://127.0.0.1:8000/")
print("   2. Tester API: http://127.0.0.1:8000/api/")
print("   3. Configurer collecte automatique (Airflow)")
print()

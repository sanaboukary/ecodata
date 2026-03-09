#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC DONNÉES DE PRIX - BRVM
====================================
Vérifie où sont stockées les données et leur qualité
"""
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "=" * 80)
print("🔍 DIAGNOSTIC DONNÉES DE PRIX - BRVM")
print("=" * 80 + "\n")

# 1. Vérifier collections disponibles
collections = db.list_collection_names()
prix_collections = [c for c in collections if 'price' in c.lower() or 'brvm' in c.lower()]

print("📊 Collections liées aux prix détectées :")
for col in prix_collections:
    count = db[col].count_documents({})
    print(f"   {col:30s} : {count:6d} documents")

# 2. Vérifier prices_weekly
print("\n" + "=" * 80)
print("📈 PRICES_WEEKLY (données hebdomadaires)")
print("=" * 80)

count_weekly = db.prices_weekly.count_documents({})
print(f"Total documents : {count_weekly}")

if count_weekly > 0:
    symboles_weekly = db.prices_weekly.distinct("symbol")
    print(f"Symboles uniques : {len(symboles_weekly)}")
    print(f"Symboles : {sorted(symboles_weekly)[:10]}..." if len(symboles_weekly) > 10 else f"Symboles : {sorted(symboles_weekly)}")
    
    # Exemple de document
    exemple = db.prices_weekly.find_one()
    print(f"\nExemple de document :")
    print(f"   {exemple}")
    
    # Données par symbole
    print(f"\n📊 Top 10 symboles par nombre de semaines :")
    pipeline = [
        {"$group": {"_id": "$symbol", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_symbols = list(db.prices_weekly.aggregate(pipeline))
    for s in top_symbols:
        print(f"   {s['_id']:10s} : {s['count']:3d} semaines")
else:
    print("⚠️  Collection VIDE")

# 3. Vérifier prices_daily
print("\n" + "=" * 80)
print("📈 PRICES_DAILY (données quotidiennes)")
print("=" * 80)

count_daily = db.prices_daily.count_documents({})
print(f"Total documents : {count_daily}")

if count_daily > 0:
    symboles_daily = db.prices_daily.distinct("symbol")
    print(f"Symboles uniques : {len(symboles_daily)}")
    print(f"Symboles : {sorted(symboles_daily)[:10]}..." if len(symboles_daily) > 10 else f"Symboles : {sorted(symboles_daily)}")
    
    # Exemple de document
    exemple = db.prices_daily.find_one()
    print(f"\nExemple de document :")
    print(f"   {exemple}")
    
    # Données par symbole
    print(f"\n📊 Top 10 symboles par nombre de jours :")
    pipeline = [
        {"$group": {"_id": "$symbol", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_symbols = list(db.prices_daily.aggregate(pipeline))
    for s in top_symbols:
        print(f"   {s['_id']:10s} : {s['count']:3d} jours")
else:
    print("⚠️  Collection VIDE")

# 4. Vérifier curated_observations pour prix
print("\n" + "=" * 80)
print("📈 CURATED_OBSERVATIONS (ancien système)")
print("=" * 80)

count_prix_obs = db.curated_observations.count_documents({
    "dataset": {"$regex": "BRVM|PRIX|PRICE", "$options": "i"}
})
print(f"Documents avec prix : {count_prix_obs}")

if count_prix_obs > 0:
    datasets = db.curated_observations.distinct("dataset", {
        "dataset": {"$regex": "BRVM|PRIX|PRICE", "$options": "i"}
    })
    print(f"Datasets : {datasets}")

print("\n" + "=" * 80)
print("💡 DIAGNOSTIC")
print("=" * 80)

if count_weekly == 0 and count_daily == 0:
    print("\n❌ PROBLÈME IDENTIFIÉ : Aucune donnée dans prices_weekly ni prices_daily")
    print("\n🔧 SOLUTION :")
    print("   Les données de prix doivent être dans prices_weekly ou prices_daily")
    print("   Vérifiez le script de collecte des prix (collecter_brvm_complet_maintenant.py)")
elif count_weekly > 0:
    print(f"\n✅ Données hebdomadaires OK : {len(symboles_weekly)} symboles")
    if len(symboles_weekly) > 47:
        print(f"⚠️  Attention : {len(symboles_weekly)} symboles au lieu de 47")
        print("   → Il y a probablement des doublons ou symboles invalides")
elif count_daily > 0:
    print(f"\n✅ Données quotidiennes OK : {len(symboles_daily)} symboles")
    print("⚠️  Le pipeline utilise prices_weekly, pas prices_daily")
    print("   → Il faut soit :")
    print("      1. Agréger prices_daily en prices_weekly")
    print("      2. Modifier analyse_ia_simple.py pour utiliser prices_daily")

print()

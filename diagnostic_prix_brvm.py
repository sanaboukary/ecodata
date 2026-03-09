"""Diagnostic et correction des prix BRVM"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("=" * 90)
print("🔍 DIAGNOSTIC DES PRIX BRVM")
print("=" * 90)

# 1. Vérifier TOUTES les données Sonatel
print("\n1️⃣ Historique complet Sonatel (SNTS):")
snts_all = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'SNTS'
}).sort('ts', -1))

print(f"   Total observations SNTS: {len(snts_all)}")
print("\n   📋 Dernières observations:")
for i, obs in enumerate(snts_all[:10], 1):
    date = obs.get('ts', 'N/A')
    price = obs.get('value', 0)
    quality = obs.get('attrs', {}).get('data_quality', 'N/A')
    dataset = obs.get('dataset', 'N/A')
    
    status = "❌ FAUX" if price in [3475, 3405] else ("✅ CORRECT" if price == 25500 else "⚠️")
    print(f"   {i:2d}. {date} | {price:>10,.0f} FCFA | Dataset: {dataset:15s} | Qualité: {quality:20s} | {status}")

# 2. Vérifier la date d'aujourd'hui
aujourdhui = datetime.now().strftime('%Y-%m-%d')
print(f"\n2️⃣ Données d'aujourd'hui ({aujourdhui}):")

actions_aujourdhui = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': aujourdhui
}).sort('key', 1))

if actions_aujourdhui:
    print(f"   ✅ {len(actions_aujourdhui)} observations trouvées pour aujourd'hui")
    for obs in actions_aujourdhui[:10]:
        symbol = obs.get('key', 'N/A')
        price = obs.get('value', 0)
        quality = obs.get('attrs', {}).get('data_quality', 'N/A')
        print(f"   - {symbol}: {price:,.0f} FCFA ({quality})")
else:
    print(f"   ❌ AUCUNE donnée pour aujourd'hui!")
    
    # Chercher la date la plus récente
    latest = db.curated_observations.find_one(
        {'source': 'BRVM'},
        sort=[('ts', -1)]
    )
    if latest:
        latest_date = latest.get('ts', 'N/A')
        print(f"   ℹ️ Date la plus récente dans la base: {latest_date}")

# 3. Le problème : que retourne la requête du dashboard ?
print(f"\n3️⃣ Ce que le dashboard va afficher (requête identique):")
dashboard_query = db.curated_observations.find({
    'source': 'BRVM'
}).sort('ts', -1).limit(10)

for obs in dashboard_query:
    symbol = obs.get('key', 'N/A')
    price = obs.get('value', 0)
    date = obs.get('ts', 'N/A')
    print(f"   - {symbol}: {price:,.0f} FCFA (Date: {date})")

print("\n" + "=" * 90)
print("🎯 SOLUTION:")
print("=" * 90)

# Vérifier si on doit créer les données d'aujourd'hui
if not actions_aujourdhui:
    print("\n⚠️ Aucune donnée pour aujourd'hui!")
    print("\n💡 Vous devez collecter les données d'aujourd'hui:")
    print("   Option 1: Double-cliquez sur mettre_a_jour_prix_reels_brvm.py")
    print("   Option 2: Lancez le scraper: python scripts/connectors/brvm_scraper_production.py")
    print("   Option 3: Saisie manuelle guidée")
else:
    # Vérifier si Sonatel a le bon prix
    snts_today = next((o for o in actions_aujourdhui if o.get('key') == 'SNTS'), None)
    if snts_today:
        snts_price = snts_today.get('value', 0)
        if snts_price != 25500:
            print(f"\n⚠️ Sonatel aujourd'hui = {snts_price:,.0f} FCFA (devrait être 25 500)")
            print("\n💡 Corrigez le prix:")
            print("   python mettre_a_jour_prix_reels_brvm.py")
        else:
            print("\n✅ Sonatel a le bon prix aujourd'hui!")
            print("⚠️ Mais le dashboard affiche peut-être une ancienne donnée")
            print("\n💡 Supprimez les anciennes données fausses:")
            print("   Je vais les supprimer maintenant...")
            
            # Supprimer les observations avec faux prix
            result = db.curated_observations.delete_many({
                'source': 'BRVM',
                'key': 'SNTS',
                'value': {'$in': [3475, 3405]},
                'ts': {'$ne': aujourdhui}
            })
            print(f"   ✅ {result.deleted_count} anciennes observations supprimées")
    else:
        print("\n⚠️ Pas de données Sonatel pour aujourd'hui!")
        print("💡 Ajoutez-les avec: python mettre_a_jour_prix_reels_brvm.py")

print("\n" + "=" * 90)

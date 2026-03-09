"""Vérifier et corriger le prix de Sonatel (SNTS)"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# 1. Vérifier le prix actuel dans la DB
print("🔍 Vérification du prix SNTS dans MongoDB...")
snts_data = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'SNTS'
}).sort('ts', -1).limit(5))

print(f"\n📊 Données actuelles pour SNTS:")
for data in snts_data:
    print(f"  Date: {data.get('ts', 'N/A')}")
    print(f"  Prix: {data.get('value', 'N/A')} FCFA")
    print(f"  Data Quality: {data.get('attrs', {}).get('data_quality', 'N/A')}")
    print()

# 2. Mettre à jour avec le vrai prix
vrai_prix = 25500  # Prix réel de Sonatel
date_aujourdhui = datetime.now().strftime('%Y-%m-%d')

print(f"✅ Mise à jour avec le VRAI prix: {vrai_prix} FCFA")

# Données complètes de Sonatel avec le vrai prix
sonatel_update = {
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'key': 'SNTS',
    'ts': date_aujourdhui,
    'value': vrai_prix,
    'attrs': {
        'symbol': 'SNTS',
        'name': 'Sonatel',
        'sector': 'Télécommunications',
        'country': 'SN',
        'currency': 'FCFA',
        'open': vrai_prix,
        'high': vrai_prix,
        'low': vrai_prix,
        'close': vrai_prix,
        'volume': 0,
        'data_quality': 'REAL_MANUAL',  # Saisie manuelle confirmée
        'last_update': datetime.now().isoformat(),
        'source_type': 'MANUAL_CORRECTION'
    }
}

# Upsert dans MongoDB
result = db.curated_observations.update_one(
    {
        'source': 'BRVM',
        'key': 'SNTS',
        'ts': date_aujourdhui
    },
    {'$set': sonatel_update},
    upsert=True
)

if result.upserted_id:
    print(f"✅ Nouvelle observation créée: {result.upserted_id}")
elif result.modified_count > 0:
    print(f"✅ Observation mise à jour")
else:
    print(f"ℹ️ Aucun changement nécessaire")

# 3. Vérifier que la mise à jour a fonctionné
print(f"\n🔍 Vérification après mise à jour:")
snts_updated = db.curated_observations.find_one({
    'source': 'BRVM',
    'key': 'SNTS',
    'ts': date_aujourdhui
})

if snts_updated:
    print(f"  ✅ Prix SNTS: {snts_updated.get('value')} FCFA")
    print(f"  ✅ Qualité: {snts_updated.get('attrs', {}).get('data_quality')}")
    print(f"\n🎉 Prix de Sonatel corrigé avec succès!")
else:
    print(f"  ❌ Erreur: données non trouvées après mise à jour")

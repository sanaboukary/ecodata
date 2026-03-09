"""Vérifier les prix BRVM actuels dans le dashboard"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

client, db = get_mongo_db()

# Récupérer les derniers prix de toutes les actions
print("=" * 80)
print("📊 PRIX BRVM ACTUELS DANS LE SYSTÈME")
print("=" * 80)

# Date la plus récente
date_recente = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

actions = db.curated_observations.find({
    'source': 'BRVM',
    'ts': {'$gte': date_recente}
}).sort([('key', 1), ('ts', -1)])

actions_dict = {}
for action in actions:
    symbol = action.get('key')
    if symbol not in actions_dict:
        actions_dict[symbol] = action

print(f"\n📅 Données depuis: {date_recente}")
print(f"🔢 Nombre d'actions: {len(actions_dict)}\n")

for symbol, data in sorted(actions_dict.items()):
    name = data.get('attrs', {}).get('name', 'N/A')
    price = data.get('value', 0)
    date = data.get('ts', 'N/A')
    quality = data.get('attrs', {}).get('data_quality', 'N/A')
    
    # Marquer Sonatel en vert si prix correct
    if symbol == 'SNTS':
        if price == 25500:
            print(f"✅ {symbol:8s} | {name:30s} | {price:>10,} FCFA | {date} | {quality}")
        else:
            print(f"❌ {symbol:8s} | {name:30s} | {price:>10,} FCFA | {date} | ⚠️ PRIX INCORRECT")
    else:
        print(f"   {symbol:8s} | {name:30s} | {price:>10,} FCFA | {date} | {quality}")

print("\n" + "=" * 80)

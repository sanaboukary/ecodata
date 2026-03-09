#!/usr/bin/env python3
"""
🔄 MIGRATION CURATED_OBSERVATIONS → PRICES_DAILY

Migre les données historiques de curated_observations vers prices_daily
"""
import os, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("🔄 MIGRATION CURATED_OBSERVATIONS → PRICES_DAILY")
print("="*80)

# 1. Lire curated_observations
print("\n📥 Lecture curated_observations...")
cursor = db.curated_observations.find({'dataset': 'STOCK_PRICE'})
data = list(cursor)
print(f"   Trouvé : {len(data)} observations")

# 2. Grouper par (symbol, date)
print("\n📊 Groupement par (symbol, date)...")
grouped = defaultdict(list)

for doc in data:
    symbol = doc.get('key', '').split('_')[0] if doc.get('key') else None
    if not symbol or not symbol.isupper():
        continue
    
    # Extraire date
    ts = doc.get('ts')
    if isinstance(ts, datetime):
        date_str = ts.strftime('%Y-%m-%d')
    elif isinstance(ts, str):
        try:
            date_str = ts.split('T')[0]
        except:
            continue
    else:
        continue
    
    value = doc.get('value')
    if value is None:
        continue
    
    grouped[(symbol, date_str)].append({
        'value': float(value),
        'source': doc.get('source', 'CURATED'),
        'ts': ts
    })

print(f"   Groupes (symbol, date) : {len(grouped)}")

# 3. Créer DAILY pour chaque groupe
print("\n🟢 Création DAILY...")
created = 0
updated = 0
skipped = 0

for (symbol, date_str), values in grouped.items():
    if not values:
        skipped += 1
        continue
    
    # Extraire OHLC
    prices = [v['value'] for v in values]
    
    if len(prices) == 1:
        # Si 1 seule valeur, close = open = high = low
        open_price = close_price = high_price = low_price = prices[0]
    else:
        # Simuler OHLC (on n'a que des closes dans curated)
        open_price = prices[0]
        high_price = max(prices)
        low_price = min(prices)
        close_price = prices[-1]
    
    # Variation
    variation_pct = None
    if open_price and close_price and open_price > 0:
        variation_pct = ((close_price - open_price) / open_price) * 100
    
    # Document DAILY
    daily_doc = {
        'symbol': symbol,
        'date': date_str,
        'source': 'MIGRATION_CURATED',
        'updated_at': datetime.now(),
        
        # OHLC
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': 0,  # Pas de volume dans curated
        'variation_pct': variation_pct,
        
        # Métadonnées
        'nb_observations_raw': len(values),
        'first_datetime': values[0]['ts'],
        'last_datetime': values[-1]['ts'],
        
        # FLAGS
        'level': 'DAILY',
        'is_complete': True,
        'used_for_weekly': False,
        'indicators_computed': False
    }
    
    # Upsert
    result = db.prices_daily.update_one(
        {'symbol': symbol, 'date': date_str},
        {'$set': daily_doc},
        upsert=True
    )
    
    if result.upserted_id:
        created += 1
    else:
        updated += 1
    
    if (created + updated) % 100 == 0:
        print(f"   Traité : {created + updated}...")

print(f"\n✅ Créés : {created}")
print(f"🔄 Mis à jour : {updated}")
print(f"⏭️  Skippés : {skipped}")

# 4. Stats finales
print("\n"+ "="*80)
print("📊 STATS FINALES")
print("="*80)

total_daily = db.prices_daily.count_documents({})
dates = list(db.prices_daily.distinct('date'))
symbols = list(db.prices_daily.distinct('symbol'))

print(f"DAILY total : {total_daily}")
print(f"Dates : {len(dates)}")
if dates:
    print(f"Première : {min(dates)}")
    print(f"Dernière : {max(dates)}")
print(f"Symboles : {len(symbols)}")

print("\n✅ MIGRATION TERMINÉE")
print("="*80)
print("\n🎯 Prochaine étape : python brvm_pipeline/pipeline_weekly.py --rebuild\n")

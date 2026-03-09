#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agrégation des collectes intra-journalières 9h-16h
Calcule le VRAI high/low quotidien à partir des collectes multiples
"""

from pymongo import MongoClient
from datetime import datetime
from collections import defaultdict

print("="*70)
print("AGRÉGATION COLLECTES INTRA-JOURNALIÈRES - PRÉCISION MAXIMALE")
print("="*70)

db = MongoClient()['centralisation_db']

# 1. Récupérer TOUTES les collectes daily
all_docs = list(db.prices_daily.find({}, {
    'symbol': 1, 
    'date': 1, 
    'close': 1, 
    'open': 1,
    'high': 1, 
    'low': 1, 
    'volume': 1,
    'created_at': 1
}).sort([('symbol', 1), ('date', 1), ('created_at', 1)]))

print(f"\nTotal collectes: {len(all_docs)}")

# 2. Grouper par (symbol, date) pour trouver les multiples collectes
grouped = defaultdict(list)
for doc in all_docs:
    # Extraire date seule (sans heure)
    date_str = doc['date']
    if isinstance(date_str, datetime):
        date_only = date_str.strftime('%Y-%m-%d')
    else:
        date_only = date_str.split('T')[0] if 'T' in date_str else date_str
    
    key = (doc['symbol'], date_only)
    grouped[key].append(doc)

# 3. Identifier les jours avec collectes multiples
multi_collections = {k: v for k, v in grouped.items() if len(v) > 1}
print(f"Jours avec collectes multiples: {len(multi_collections)}")

# 4. Agréger pour calculer VRAI high/low
aggregated = 0
improved = 0

for (symbol, date), docs in multi_collections.items():
    # Trier par created_at
    docs_sorted = sorted(docs, key=lambda x: x.get('created_at', datetime.min))
    
    # VRAI high = MAX de tous les prix (high, close, open)
    all_prices = []
    for d in docs_sorted:
        all_prices.extend([
            d.get('high', 0), 
            d.get('low', 0),
            d.get('open', 0), 
            d.get('close', 0)
        ])
    
    all_prices = [p for p in all_prices if p > 0]
    
    if not all_prices:
        continue
    
    true_high = max(all_prices)
    true_low = min(all_prices)
    
    # Ouverture = première collecte, Clôture = dernière collecte
    open_price = docs_sorted[0].get('open', docs_sorted[0].get('close', 0))
    close_price = docs_sorted[-1].get('close', 0)
    
    # Volume = somme (si disponible) ou max
    volumes = [d.get('volume', 0) for d in docs_sorted]
    total_volume = sum(volumes) if any(v > 0 for v in volumes) else 0
    
    # Vérifier si on améliore la précision
    current_high = docs_sorted[-1].get('high', 0)
    current_low = docs_sorted[-1].get('low', 0)
    
    range_improvement = False
    if current_high > 0 and current_low > 0:
        old_range = (current_high - current_low) / close_price * 100
        new_range = (true_high - true_low) / close_price * 100
        if new_range > old_range * 1.1:  # Au moins 10% d'amélioration
            range_improvement = True
            improved += 1
    
    # Mettre à jour le dernier document (le plus récent)
    last_doc = docs_sorted[-1]
    
    update = {
        'open': open_price,
        'high': true_high,
        'low': true_low,
        'close': close_price,
        'volume': total_volume,
        'intraday_aggregated': True,
        'intraday_collections': len(docs_sorted),
        'aggregated_at': datetime.now()
    }
    
    result = db.prices_daily.update_one(
        {'_id': last_doc['_id']},
        {'$set': update}
    )
    
    if result.modified_count > 0:
        aggregated += 1
        
        if aggregated <= 5 or range_improvement:  # Afficher premiers + améliorations
            status = "🎯" if range_improvement else "✅"
            print(f"{status} {symbol} {date} | {len(docs_sorted)} collectes | "
                  f"Range: {true_low:.0f}-{true_high:.0f} ({new_range:.1f}%)")
    
    # Supprimer les anciennes collectes (garder la dernière agrégée)
    if len(docs_sorted) > 1:
        old_ids = [d['_id'] for d in docs_sorted[:-1]]
        db.prices_daily.delete_many({'_id': {'$in': old_ids}})

print(f"\n{'='*70}")
print(f"✅ {aggregated} jours agrégés")
print(f"🎯 {improved} avec amélioration significative du range (>10%)")
print(f"{'='*70}")

# 5. Statistiques finales
total_after = db.prices_daily.count_documents({})
with_aggregation = db.prices_daily.count_documents({'intraday_aggregated': True})

print(f"\nDocuments daily après agrégation: {total_after}")
print(f"Avec agrégation intra-jour: {with_aggregation}")

if with_aggregation > 0:
    print(f"\n✅ Collectes intra-journalières exploitées")
    print(f"➡️  Lancer rebuild_weekly_direct.py pour recalculer avec précision")
else:
    print(f"\nℹ️  Aucune collecte multiple détectée")
    print(f"   (Normal si vous venez de commencer les collectes 9h-16h)")

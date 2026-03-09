from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime

db = MongoClient()['centralisation_db']
print("Récupération données...")

# Récupérer tous les docs
docs = list(db.prices_daily.find({}, {'symbol': 1, 'date': 1, 'high': 1, 'low': 1, 'open': 1, 'close': 1, 'volume': 1, 'created_at': 1}))
print(f"Total: {len(docs)}")

# Grouper
grouped = defaultdict(list)
for d in docs:
    date_str = d['date']
    if isinstance(date_str, datetime):
        date_only = date_str.strftime('%Y-%m-%d')
    else:
        date_only = date_str.split('T')[0] if 'T' in date_str else date_str
    key = (d['symbol'], date_only)
    grouped[key].append(d)

multi = [(k,v) for k,v in grouped.items() if len(v) > 1]
print(f"Collectes multiples: {len(multi)}")

if len(multi) == 0:
    print("Aucune collecte multi - Les données sont déjà uniques par jour")
    print("Passons direct au rebuild weekly avec ATR précis!")
else:
    print(f"Agrégation de {len(multi)} jours...")
    
for (sym, date), docs_list in multi[:100]:  # Max 100 pour test
    docs_sorted = sorted(docs_list, key=lambda x: x.get('created_at', datetime.min))
    
    all_prices = []
    for d in docs_sorted:
        all_prices.extend([d.get('high', 0), d.get('low', 0), d.get('open', 0), d.get('close', 0)])
    all_prices = [p for p in all_prices if p > 0]
    
    if not all_prices:
        continue
    
    true_high = max(all_prices)
    true_low = min(all_prices)
    open_price = docs_sorted[0].get('open', docs_sorted[0].get('close', 0))
    close_price = docs_sorted[-1].get('close', 0)
    total_volume = sum([d.get('volume', 0) for d in docs_sorted])
    
    # Update dernier doc
    last_doc = docs_sorted[-1]
    db.prices_daily.update_one(
        {'_id': last_doc['_id']},
        {'$set': {
            'open': open_price,
            'high': true_high,
            'low': true_low,
            'close': close_price,
            'volume': total_volume,
            'intraday_aggregated': True,
            'intraday_collections': len(docs_sorted)
        }}
    )
    
    # Supprimer anciens
    if len(docs_sorted) > 1:
        old_ids = [d['_id'] for d in docs_sorted[:-1]]
        db.prices_daily.delete_many({'_id': {'$in': old_ids}})
    
    print(f"✅ {sym} {date}: {len(docs_sorted)} → 1")

print(f"\n✅ Terminé - Total final: {db.prices_daily.count_documents({})}")

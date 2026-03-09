from pymongo import MongoClient
from datetime import datetime

print("="*70)
print("CALCUL RSI MANUEL - W06")
print("="*70)

db = MongoClient()['centralisation_db']
WEEK = '2026-W06'

week_actions = list(db.prices_weekly.find({'week': WEEK}))
print(f"Actions W06: {len(week_actions)}")

updated = 0

for obs in week_actions:
    symbol = obs['symbol']
    
    history = list(db.prices_weekly.find(
        {'symbol': symbol},
        {'week': 1, 'close': 1, 'high': 1, 'low': 1, 'volume': 1}
    ).sort('week', 1))
    
    if len(history) < 7:
        continue
    
    closes = [h.get('close', 0) for h in history]
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < 7:
        continue
    
    period = min(14, len(gains))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = round(100 - (100 / (1 + rs)), 2)
    
    if len(closes) >= 10:
        sma5 = round(sum(closes[-5:]) / 5, 2)
        sma10 = round(sum(closes[-10:]) / 10, 2)
    elif len(closes) >= 5:
        sma5 = round(sum(closes[-5:]) / 5, 2)
        sma10 = None
    else:
        sma5 = None
        sma10 = None
    
    volumes = [h.get('volume', 0) for h in history]
    current_vol = obs.get('volume', 0)
    
    if len(volumes) >= 8:
        avg_vol = sum(volumes[-8:]) / 8
        vol_ratio = round(current_vol / avg_vol, 2) if avg_vol > 0 else 0
    else:
        vol_ratio = 0
    
    result = db.prices_weekly.update_one(
        {'_id': obs['_id']},
        {'$set': {
            'rsi': rsi,
            'sma5': sma5,
            'sma10': sma10,
            'volume_ratio': vol_ratio,
            'indicators_computed': True,
            'updated_at': datetime.now()
        }}
    )
    
    if result.modified_count > 0:
        updated += 1
        print(f"  OK {symbol:6} | RSI:{rsi:5.1f} | SMA5:{sma5 or 0:8.0f}")

print(f"\n{'='*70}")
print(f"OK {updated} actions MAJ")
print(f"{'='*70}")

with_rsi = db.prices_weekly.count_documents({'week': WEEK, 'rsi': {'$exists': True, '$ne': None}})
print(f"Total RSI W06: {with_rsi}")

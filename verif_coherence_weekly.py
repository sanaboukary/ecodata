#!/usr/bin/env python3
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

print('=== VÉRIFICATION COHÉRENCE APRÈS RECALCUL ===\n')

for symbol in ['ETIT', 'NEIC', 'SIBC', 'FTSC', 'SOGC', 'STAC']:
    # Daily récent
    daily = db.prices_daily.find_one({'symbol': symbol}, sort=[('date', -1)])
    # Weekly récent
    weekly = db.prices_weekly.find_one({'symbol': symbol}, sort=[('week', -1)])
    
    if daily and weekly:
        prix_d = daily.get('close', 0)
        prix_w = weekly.get('close', 0)
        ratio = prix_w / prix_d if prix_d > 0 else 0
        status = '✓' if 0.7 <= ratio <= 1.3 else '⚠️'
        
        print(f'[{symbol}]')
        print(f'  Daily: {prix_d:,.0f} FCFA ({daily.get("date")})')
        print(f'  Weekly: {prix_w:,.0f} FCFA ({weekly.get("week")}) - Ratio: {ratio:.2f} {status}')
        print()

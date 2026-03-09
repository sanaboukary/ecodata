#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecter données aberrantes dans prices_weekly"""

from plateforme_centralisation.mongo import get_mongo_db
from collections import defaultdict

_, db = get_mongo_db()

print('=' * 80)
print('DÉTECTION DONNÉES ABERRANTES PRICES_WEEKLY')
print('=' * 80)

# Pour chaque action, comparer weekly vs daily récent
symbols_to_check = ['ETIT', 'NEIC', 'SIBC', 'FTSC', 'SOGC', 'STAC']

for symbol in symbols_to_check:
    # Prix daily récent (réel)
    daily = db.prices_daily.find_one(
        {'symbol': symbol},
        sort=[('date', -1)]
    )
    
    if not daily:
        continue
        
    prix_actuel = daily.get('close', 0)
    date_actuel = daily.get('date', 'N/A')
    
    # Prix weekly dernières 4 semaines
    weeklies = list(db.prices_weekly.find(
        {'symbol': symbol}
    ).sort('week', -1).limit(4))
    
    print(f'\n[{symbol}]')
    print(f'  Prix actuel (daily): {prix_actuel:,.0f} FCFA ({date_actuel})')
    print(f'  Historique weekly (4 dernières semaines):')
    
    aberrant = False
    for w in weeklies:
        week = w.get('week', 'N/A')
        close = w.get('close', 0)
        high = w.get('high', 0)
        low = w.get('low', 0)
        
        # Détecter aberration: high > 10x prix actuel OU close > 5x prix actuel
        ratio_high = high / prix_actuel if prix_actuel > 0 else 0
        ratio_close = close / prix_actuel if prix_actuel > 0 else 0
        
        flag = ''
        if ratio_high > 10 or ratio_close > 5:
            flag = ' ⚠️ ABERRANT!'
            aberrant = True
        
        print(f'    {week}: close={close:,.0f}, high={high:,.0f}, low={low:,.0f}{flag}')
    
    if aberrant:
        print(f'  → ACTION REQUISE: Nettoyer données weekly pour {symbol}')

print('\n' + '=' * 80)
print('RECOMMANDATION:')
print('  1. Supprimer prices_weekly et recalculer depuis prices_daily')
print('  2. OU remplacer valeurs aberrantes par médiane des 4 dernières semaines')
print('=' * 80)

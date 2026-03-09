#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier prices_weekly pour données aberrantes
"""

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print('=' * 80)
print('VERIFICATION PRICES_WEEKLY - ETIT & NEIC')
print('=' * 80)

# ETIT (prix actuel 27 FCFA vs max_3w 11985)
print('\n[ETIT] Dernières 5 semaines:')
prices_etit = list(db.prices_weekly.find(
    {'symbol': 'ETIT'}
).sort('week', -1).limit(5))

for p in prices_etit:
    week = p.get('week', 'N/A')
    close = p.get('close', 0)
    high = p.get('high', 0)
    low = p.get('low', 0)
    print(f"  {week}: close={close:,.0f}, high={high:,.0f}, low={low:,.0f}")

# NEIC (prix actuel 1320 vs max_3w 8846)
print('\n[NEIC] Dernières 5 semaines:')
prices_neic = list(db.prices_weekly.find(
    {'symbol': 'NEIC'}
).sort('week', -1).limit(5))

for p in prices_neic:
    week = p.get('week', 'N/A')
    close = p.get('close', 0)
    high = p.get('high', 0)
    low = p.get('low', 0)
    print(f"  {week}: close={close:,.0f}, high={high:,.0f}, low={low:,.0f}")

# SIBC (prix actuel 6850 vs max_3w 12610)
print('\n[SIBC] Dernières 5 semaines:')
prices_sibc = list(db.prices_weekly.find(
    {'symbol': 'SIBC'}
).sort('week', -1).limit(5))

for p in prices_sibc:
    week = p.get('week', 'N/A')
    close = p.get('close', 0)
    high = p.get('high', 0)
    low = p.get('low', 0)
    print(f"  {week}: close={close:,.0f}, high={high:,.0f}, low={low:,.0f}")

# Comparer avec prices_daily
print('\n' + '=' * 80)
print('COMPARAISON AVEC PRICES_DAILY (prix actuels)')
print('=' * 80)

for symbol in ['ETIT', 'NEIC', 'SIBC']:
    daily = db.prices_daily.find_one(
        {'symbol': symbol},
        sort=[('date', -1)]
    )
    if daily:
        print(f"  {symbol}: {daily.get('close', 0):,.0f} FCFA ({daily.get('date')})")

print('\n[CONCLUSION]')
print('Si prices_weekly.high >> prices_daily.close :')
print('  → Données weekly corrompues (anciens tests/simulations)')
print('  → Nettoyer prices_weekly ou désactiver filtre BREAKOUT temporairement')

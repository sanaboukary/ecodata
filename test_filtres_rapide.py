#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

# Dernière semaine
weeks = sorted(db.prices_weekly.distinct('week'))
last = weeks[-1] if weeks else None

if not last:
    print("Aucune semaine")
    exit(0)

print(f"Semaine: {last}")

# Données
obs = list(db.prices_weekly.find({'week': last}))
print(f"Total obs: {len(obs)}")

# Avec indicateurs
with_ind = [o for o in obs if o.get('rsi') and o.get('atr_pct')]
print(f"Avec indicateurs: {len(with_ind)}")

# Tradables
tradable = [o for o in with_ind if 6 <= (o.get('atr_pct') or 0) <= 25]
print(f"Tradables (ATR 6-25%): {len(tradable)}\n")

if tradable:
    print("Actions tradables:")
    for o in sorted(tradable, key=lambda x: x.get('atr_pct', 0))[:10]:
        print(f"  {o['symbol']:6} ATR={o.get('atr_pct'):6.2f}% RSI={o.get('rsi'):5.1f}")

# Filtres WOS
print(f"\n🎯 Simulation filtres EXPERT:")

passed_wos = []
for o in tradable:
    # Check basique RSI
    rsi = o.get('rsi', 50)
    if not (25 <= rsi <= 55):
        continue
    
    # Check volume
    volume_ratio = o.get('volume_ratio', 0)
    if volume_ratio < 1.1:
        continue
    
    passed_wos.append(o)

print(f"  Passent RSI 25-55: {len([o for o in tradable if 25 <= o.get('rsi', 50) <= 55])}")
print(f"  Passent tous filtres: {len(passed_wos)}")

if passed_wos:
    print(f"\n✅ Candidats estimés: {len(passed_wos)}")
    for o in passed_wos[:5]:
        print(f"  {o['symbol']:6} ATR={o.get('atr_pct'):6.2f}% RSI={o.get('rsi'):5.1f}")
else:
    print(f"\n⚠️  Aucun candidat après filtres (TOLÉRANCE ZÉRO)")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient

db = MongoClient()['centralisation_db']
weeks = sorted(db.prices_weekly.distinct('week'))
print(f"\n{len(weeks)} semaines:\n{weeks}\n")

# Dernière semaine
last_week = weeks[-1] if weeks else None
if last_week:
    obs = list(db.prices_weekly.find({'week': last_week}))
    print(f"Dernière semaine {last_week}: {len(obs)} obs")
    
    with_atr = [o for o in obs if (o.get('atr_pct') or 0) > 0]
    print(f"Avec ATR: {len(with_atr)}")
    
    for o in with_atr[:10]:
        atr = o.get('atr_pct') or 0
        print(f"  {o.get('symbol'):6} ATR={atr:6.2f}%")

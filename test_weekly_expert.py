#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST RAPIDE MOTEUR EXPERT BRVM
"""
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

# Verifier decisions generees
decisions = list(db.decisions_brvm_weekly.find({'mode': 'EXPERT_BRVM'}).sort('ranking_score', -1))

print(f"Decisions EXPERT BRVM: {len(decisions)}\n")

if decisions:
    print(f"{'Symb':<6} {'Classe':<7} {'Rank':<6} {'WOS':<6} {'RR':<6} {'ER%':<6} {'ATR%':<6}")
    print("-"*60)
    
    for d in decisions:
        print(
            f"{d['symbol']:<6} "
            f"{d['classe']:<7} "
            f"{d.get('ranking_score', 0):<6.1f} "
            f"{d.get('wos', 0):<6.1f} "
            f"{d.get('risk_reward', 0):<6.2f} "
            f"{d.get('expected_return', 0):<6.1f} "
            f"{d.get('atr_pct', 0):<6.1f}"
        )
else:
    print("Aucune decision generee")
    print("\nVerification donnees weekly...")
    
    # Verifier prix weekly
    weekly_count = db.prices_weekly.count_documents({'week': '2026-W07'})
    print(f"  Semaine 2026-W07: {weekly_count} observations")
    
    # Verifier indicateurs
    with_indicators = db.prices_weekly.count_documents({
        'week': '2026-W07',
        'rsi': {'$exists': True},
        'atr_pct': {'$exists': True}
    })
    print(f"  Avec indicateurs: {with_indicators}")
    
    # Verifier tradable
    tradable = db.prices_weekly.count_documents({
        'week': '2026-W07',
        'tradable': True
    })
    print(f"  Tradables (ATR 6-25%): {tradable}")

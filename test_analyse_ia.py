#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test rapide de l'analyse IA"""
import os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from analyse_ia_simple import RecommendationEngine

_, db = get_mongo_db()

print("\n" + "="*80)
print("TEST ANALYSE IA - Avec nouvelles collections")
print("="*80 + "\n")

# Liste des symboles disponibles
symbols = db.prices_weekly.distinct("symbol")
print(f"Symboles disponibles dans prices_weekly: {len(symbols)}")
print(f"Exemples: {', '.join(sorted(symbols)[:10])}\n")

# Tester l'analyse sur quelques actions
engine = RecommendationEngine(db)

print("TEST sur 5 premières actions:\n")
print(f"{'Symbole':<10} {'Signal':<6} {'Score':>6} {'RSI':>6} {'Trend':<10}")
print("-"*60)

for symbol in sorted(symbols)[:5]:
    result = engine.analyser_une_action(symbol)
    if result:
        rsi = result.get('rsi', 0)
        print(f"{symbol:<10} {result['signal']:<6} {result['score']:>6.1f} {rsi:>6.1f} {result.get('trend', 'N/A'):<10}")
        if result.get('details'):
            for detail in result['details'][:3]:
                print(f"  - {detail}")
    else:
        print(f"{symbol:<10} SKIP (données insuffisantes)")

print("\n" + "="*80 + "\n")

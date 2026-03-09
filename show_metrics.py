#!/usr/bin/env python
# -*- coding: utf-8 -*-
print("[1/5] Import modules...")
import os
import sys
from collections import defaultdict, Counter

print("[2/5] Setup Django...")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

print("[3/5] Connection MongoDB...")
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

print("[4/5] Recuperation decisions...")
decisions = list(db.decisions_finales_brvm.find({
    "horizon": "SEMAINE",
    "week": {"$exists": True, "$ne": None}
}))

print(f"[5/5] Analyse {len(decisions)} decisions...\n")

if len(decisions) == 0:
    print("[INFO] Aucune decision avec 'week' - Lancer pipeline d'abord\n")
    sys.exit(0)

# Grouper par semaine
by_week = defaultdict(list)
for dec in decisions:
    week = dec.get("week")
    if week:
        by_week[week].append(dec)

# Affichage
print("="*80)
print(" METRIQUES PERFORMANCE BRVM")
print("="*80)
print(f"\nDecisions totales: {len(decisions)}")
print(f"Semaines uniques:  {len(by_week)}")
print(f"\nPremiere semaine:  {min(by_week.keys())}")
print(f"Derniere semaine:  {max(by_week.keys())}")

print("\n" + "-"*80)
print(" ANALYSE PAR SEMAINE")
print("-"*80)
print(f"{'Semaine':<12} {'Nb':>4} {'BUY':>4} {'SELL':>5} {'ALPHA moy':>10}")
print("-"*80)

total_buy = 0
total_sell = 0
all_alphas = []

for week in sorted(by_week.keys()):
    decs = by_week[week]
    nb_buy = sum(1 for d in decs if d.get("decision") == "BUY")
    nb_sell = sum(1 for d in decs if d.get("decision") == "SELL")
    
    alphas = [d.get("alpha_score", d.get("wos", 50)) for d in decs]
    avg_alpha = sum(alphas) / len(alphas) if alphas else 0
    
    print(f"{week:<12} {len(decs):>4} {nb_buy:>4} {nb_sell:>5} {avg_alpha:>9.1f}")
    
    total_buy += nb_buy
    total_sell += nb_sell
    all_alphas.extend(alphas)

print("-"*80)
print(f"{'TOTAL':<12} {len(decisions):>4} {total_buy:>4} {total_sell:>5} {sum(all_alphas)/len(all_alphas):>9.1f}")
print("="*80)

# Top symboles
print("\n" + "-"*80)
print(" TOP 10 SYMBOLES")
print("-"*80)
symbols = [d.get("symbol") for d in decisions if d.get("symbol")]
for symbol, count in Counter(symbols).most_common(10):
    print(f"{symbol:<8} {count:>3}x")

print("\n" + "="*80)
print("\n[OK] Metriques calculees - Pour win rate reel, besoin prix sortie\n")

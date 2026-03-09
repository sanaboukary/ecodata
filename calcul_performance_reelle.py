#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CALCUL PERFORMANCE REELLE - Recherche retroactive prix sortie
"""

print("[1/6] Import...")
import os, sys, django
from datetime import datetime, timedelta
from statistics import mean, stdev

print("[2/6] Setup Django...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
django.setup()

print("[3/6] MongoDB...")
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

def get_week_dates(week_str):
    """Convertir 2026-W07 en dates Lundi-Vendredi"""
    year, week = week_str.split("-W")
    year, week = int(year), int(week)
    
    # ISO: Week 1 contient 4 Janvier
    jan4 = datetime(year, 1, 4)
    monday = jan4 + timedelta(weeks=week-1, days=-jan4.weekday())
    friday = monday + timedelta(days=4)
    
    return monday, friday

def find_exit_price(db, symbol, entry_date, friday):
    """Trouve prix sortie (Vendredi ou dernier prix disponible)"""
    # Chercher prix Vendredi
    friday_str = friday.strftime("%Y-%m-%d")
    
    friday_price = db.prices_daily.find_one({
        "symbol": symbol,
        "date": friday_str
    })
    
    if friday_price:
        return friday_price.get("close") or friday_price.get("prix_actuel")
    
    # Fallback: Dernier prix après entry_date
    last_price = db.prices_daily.find_one({
        "symbol": symbol,
        "date": {"$gte": entry_date, "$lte": friday_str}
    }, sort=[("date", -1)])
    
    if last_price:
        return last_price.get("close") or last_price.get("prix_actuel")
    
    return None

print("[4/6] Recuperation decisions...")
decisions = list(db.decisions_finales_brvm.find({
    "horizon": "SEMAINE",
    "week": {"$exists": True, "$ne": None},
    "decision": "BUY"
}).sort("week", 1))

print(f"[5/6] Calcul performance {len(decisions)} trades...\n")

results = []
missing_exit = 0

for dec in decisions:
    symbol = dec.get("symbol")
    week = dec.get("week")
    prix_entree = dec.get("prix_entree")
    prix_cible = dec.get("prix_cible")
    stop = dec.get("stop")
    
    if not (symbol and week and prix_entree):
        continue
    
    # Dates semaine
    monday, friday = get_week_dates(week)
    entry_date = monday.strftime("%Y-%m-%d")
    
    # Chercher prix sortie
    prix_sortie = find_exit_price(db, symbol, entry_date, friday)
    
    if not prix_sortie:
        missing_exit += 1
        continue
    
    # Calculer performance
    perf = (prix_sortie - prix_entree) / prix_entree * 100
    
    # Status
    if prix_sortie >= prix_cible:
        status = "TARGET"
    elif prix_sortie <= stop:
        status = "STOP"
    elif perf > 0:
        status = "WIN"
    else:
        status = "LOSS"
    
    results.append({
        "week": week,
        "symbol": symbol,
        "prix_entree": prix_entree,
        "prix_sortie": prix_sortie,
        "prix_cible": prix_cible,
        "stop": stop,
        "performance": perf,
        "status": status,
        "alpha": dec.get("alpha_score", dec.get("wos", 50))
    })

print("[6/6] Analyse resultats...\n")

if not results:
    print("[ERROR] Aucune performance calculable - Prices manquants\n")
    sys.exit(1)

# Statistiques
wins = [r for r in results if r["performance"] > 0]
losses = [r for r in results if r["performance"] <= 0]

win_rate = len(wins) / len(results) * 100
avg_gain = mean([r["performance"] for r in wins]) if wins else 0
avg_loss = mean([r["performance"] for r in losses]) if losses else 0

cum_perf = sum(r["performance"] for r in results)
best = max(results, key=lambda r: r["performance"])
worst = min(results, key=lambda r: r["performance"])

# Affichage
print("="*80)
print(" PERFORMANCE REELLE - BACKTEST 8 SEMAINES")
print("="*80)
print(f"\nTrades analyses:  {len(results)}")
print(f"Prix manquants:   {missing_exit}")

print("\n" + "-"*80)
print(" STATISTIQUES GLOBALES")
print("-"*80)
print(f"Win Rate:          {win_rate:.1f}% ({len(wins)} wins / {len(losses)} losses)")
print(f"Gain moyen:        +{avg_gain:.2f}%")
print(f"Perte moyenne:     {avg_loss:.2f}%")
print(f"Ratio G/P:         {abs(avg_gain/avg_loss) if avg_loss != 0 else float('inf'):.2f}")

print(f"\nPerf cumulee:      {cum_perf:+.2f}%")
print(f"Perf moyenne:      {cum_perf/len(results):+.2f}%")

if len(results) > 1:
    volatility = stdev([r["performance"] for r in results])
    print(f"Volatilite:        {volatility:.2f}%")

print(f"\nMeilleur trade:    {best['symbol']} {best['week']} ({best['performance']:+.2f}%)")
print(f"Pire trade:        {worst['symbol']} {worst['week']} ({worst['performance']:+.2f}%)")

# Targets/Stops
targets_hit = sum(1 for r in results if r["status"] == "TARGET")
stops_hit = sum(1 for r in results if r["status"] == "STOP")

print(f"\nTargets atteints:  {targets_hit} ({targets_hit/len(results)*100:.1f}%)")
print(f"Stops touches:     {stops_hit} ({stops_hit/len(results)*100:.1f}%)")

print("\n" + "-"*80)
print(" DETAIL PAR SEMAINE")
print("-"*80)
print(f"{'Semaine':<12} {'Symbol':<8} {'Entree':>8} {'Sortie':>8} {'Perf':>7} {'Status':<8}")
print("-"*80)

for r in results:
    print(f"{r['week']:<12} {r['symbol']:<8} {r['prix_entree']:>8.0f} "
          f"{r['prix_sortie']:>8.0f} {r['performance']:>6.2f}% {r['status']:<8}")

print("="*80)

# Diagnostic institutionnel
print("\n" + "-"*80)
print(" DIAGNOSTIC INSTITUTIONNEL")
print("-"*80)

if win_rate >= 60:
    verdict = "EXCELLENT - Win rate institutionnel valide"
elif win_rate >= 50:
    verdict = "BON - Systeme genere alpha positif"
elif win_rate >= 40:
    verdict = "MOYEN - A surveiller, ameliorations possibles"
else:
    verdict = "FAIBLE - Optimisation requise"

print(f"Verdict:    {verdict}")
print(f"Win rate:   {win_rate:.1f}% (objectif SGI: 60%+)")
print(f"Perf/trade: {cum_perf/len(results):+.2f}% (objectif: +2%+)")

if len(results) < 30:
    print(f"\n[ATTENTION] Seulement {len(results)} trades - Besoin 30+ pour statistiques robustes")
    print(f"            Attendre {30 - len(results)} trades supplementaires ({math.ceil((30-len(results))/5)} semaines)")
else:
    print("\n[OK] Taille echantillon suffisante pour conclusions preliminaires")

print("\n" + "="*80)
print("\n[TERMINE] Performance reelle calculee\n")

# Sauvegarder dans MongoDB
for r in results:
    db.decisions_finales_brvm.update_one(
        {"symbol": r["symbol"], "week": r["week"]},
        {"$set": {
            "prix_sortie": r["prix_sortie"],
            "performance_reelle": r["performance"],
            "status_sortie": r["status"]
        }}
    )

print("[SAUVEGARDE] Prix sortie + performances -> decisions_finales_brvm\n")

import math

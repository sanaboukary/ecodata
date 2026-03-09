#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyse historique 4 mois - Identifier la régression
Comprendre pourquoi ça fonctionnait avant et plus maintenant
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict

print("="*80)
print("ANALYSE HISTORIQUE 4 MOIS - DIAGNOSTIC RÉGRESSION")
print("="*80)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Stats globales
daily = list(db.prices_daily.find())
print(f"\n📊 DONNÉES DAILY TOTALES: {len(daily)} observations")

if len(daily) == 0:
    print("❌ AUCUNE donnée daily ! Base vide ?")
    exit(1)

# Analyser par période
by_month = defaultdict(list)
ohlc_complet_par_mois = defaultdict(int)
volume_present_par_mois = defaultdict(int)

for obs in daily:
    date = obs.get('date')
    if not date:
        continue
    
    # Grouper par mois
    month_key = date.strftime('%Y-%m') if isinstance(date, datetime) else str(date)[:7]
    by_month[month_key].append(obs)
    
    # Vérifier qualité OHLC
    high = obs.get('high', 0)
    low = obs.get('low', 0)
    close = obs.get('close', 0)
    volume = obs.get('volume', 0)
    
    if high > 0 and low > 0 and close > 0:
        ohlc_complet_par_mois[month_key] += 1
    
    if volume > 0:
        volume_present_par_mois[month_key] += 1

print(f"\n📅 RÉPARTITION PAR MOIS:")
print("-" * 80)
print(f"{'Mois':<12} {'Total':>8} {'OHLC OK':>10} {'Volume>0':>10} {'% OHLC':>8} {'% Vol':>8}")
print("-" * 80)

mois_sorted = sorted(by_month.keys())
for mois in mois_sorted:
    total = len(by_month[mois])
    ohlc_ok = ohlc_complet_par_mois[mois]
    vol_ok = volume_present_par_mois[mois]
    pct_ohlc = (ohlc_ok / total * 100) if total > 0 else 0
    pct_vol = (vol_ok / total * 100) if total > 0 else 0
    
    status = "✅" if pct_ohlc > 95 else "⚠️" if pct_ohlc > 50 else "❌"
    print(f"{mois:<12} {total:>8} {ohlc_ok:>10} {vol_ok:>10} {pct_ohlc:>7.1f}% {pct_vol:>7.1f}% {status}")

# Analyser période récente vs ancienne
print(f"\n🔍 ANALYSE QUALITÉ PAR PÉRIODE:")
print("-" * 80)

# Derniers 7 jours
now = datetime.now()
week_ago = now - timedelta(days=7)
recent = [obs for obs in daily if obs.get('date') and obs['date'] >= week_ago]

print(f"\n📌 DERNIERS 7 JOURS ({len(recent)} obs):")
if recent:
    ohlc_ok_recent = sum(1 for obs in recent if obs.get('high', 0) > 0 and obs.get('low', 0) > 0 and obs.get('close', 0) > 0)
    vol_ok_recent = sum(1 for obs in recent if obs.get('volume', 0) > 0)
    print(f"  OHLC complet: {ohlc_ok_recent}/{len(recent)} ({ohlc_ok_recent/len(recent)*100:.1f}%)")
    print(f"  Volume > 0  : {vol_ok_recent}/{len(recent)} ({vol_ok_recent/len(recent)*100:.1f}%)")
    
    # Exemple d'observation récente
    sample = recent[0]
    print(f"\n  Exemple récent ({sample.get('date')}):")
    print(f"    Symbol: {sample.get('symbol')}")
    print(f"    High  : {sample.get('high', 0)}")
    print(f"    Low   : {sample.get('low', 0)}")
    print(f"    Close : {sample.get('close', 0)}")
    print(f"    Volume: {sample.get('volume', 0)}")

# Mois le plus ancien
month_ago_30 = now - timedelta(days=30)
month_ago_60 = now - timedelta(days=60)
old_data = [obs for obs in daily if obs.get('date') and month_ago_60 <= obs['date'] < month_ago_30]

print(f"\n📌 IL Y A 1-2 MOIS ({len(old_data)} obs):")
if old_data:
    ohlc_ok_old = sum(1 for obs in old_data if obs.get('high', 0) > 0 and obs.get('low', 0) > 0 and obs.get('close', 0) > 0)
    vol_ok_old = sum(1 for obs in old_data if obs.get('volume', 0) > 0)
    print(f"  OHLC complet: {ohlc_ok_old}/{len(old_data)} ({ohlc_ok_old/len(old_data)*100:.1f}%)")
    print(f"  Volume > 0  : {vol_ok_old}/{len(old_data)} ({vol_ok_old/len(old_data)*100:.1f}%)")
    
    # Exemple ancien
    sample = old_data[0]
    print(f"\n  Exemple ancien ({sample.get('date')}):")
    print(f"    Symbol: {sample.get('symbol')}")
    print(f"    High  : {sample.get('high', 0)}")
    print(f"    Low   : {sample.get('low', 0)}")
    print(f"    Close : {sample.get('close', 0)}")
    print(f"    Volume: {sample.get('volume', 0)}")

# Vérifier weekly
print(f"\n📊 DONNÉES WEEKLY:")
weekly = list(db.prices_weekly.find())
print(f"  Total observations: {len(weekly)}")

if len(weekly) > 0:
    with_atr = sum(1 for w in weekly if w.get('atr_pct', 0) > 0)
    with_ind = sum(1 for w in weekly if w.get('rsi'))
    print(f"  Avec ATR      : {with_atr}/{len(weekly)} ({with_atr/len(weekly)*100:.1f}%)")
    print(f"  Avec indicateurs: {with_ind}/{len(weekly)} ({with_ind/len(weekly)*100:.1f}%)")
    
    # Date du dernier weekly
    latest_week = max([w.get('week_id', '') for w in weekly])
    print(f"  Dernière semaine: {latest_week}")

# Vérification anciennes décisions
decisions = list(db.decisions_brvm_weekly.find().sort('created_at', -1).limit(10))
print(f"\n📋 DÉCISIONS HISTORIQUES:")
print(f"  Total décisions: {len(decisions)}")

if decisions:
    print(f"\n  Dernières décisions:")
    for dec in decisions[:5]:
        date = dec.get('created_at', 'N/A')
        symbol = dec.get('symbol', 'N/A')
        classe = dec.get('classe', 'N/A')
        wos = dec.get('wos', 0)
        rr = dec.get('rr', 0)
        print(f"    {date} | {symbol:6} | Classe {classe} | WOS:{wos:5.1f} | RR:{rr:.2f}")

print("\n" + "="*80)
print("DIAGNOSTIC:")
print("="*80)

# Synthèse
if len(recent) > 0 and len(old_data) > 0:
    ohlc_recent_pct = ohlc_ok_recent/len(recent)*100 if len(recent) > 0 else 0
    ohlc_old_pct = ohlc_ok_old/len(old_data)*100 if len(old_data) > 0 else 0
    
    if ohlc_recent_pct < 50 and ohlc_old_pct > 90:
        print("❌ RÉGRESSION IDENTIFIÉE:")
        print(f"   Avant (1-2 mois): {ohlc_old_pct:.1f}% OHLC complet")
        print(f"   Maintenant      : {ohlc_recent_pct:.1f}% OHLC complet")
        print("\n💡 CAUSE: Le collector BRVM a changé - ne remplit plus high/low")
        print("   SOLUTION: Corriger collecter_brvm_complet_maintenant.py")
    elif ohlc_recent_pct > 90:
        print("✅ Données daily OHLC bonnes (>90%)")
        print("⚠️  Mais weekly ATR = 0 → problème dans pipeline weekly")
    else:
        print(f"⚠️  Qualité OHLC moyenne: {ohlc_recent_pct:.1f}%")

print("="*80)

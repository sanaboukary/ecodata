#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calcul manuel indicateurs pour W06
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

print("="*70)
print("CALCUL MANUEL INDICATEURS - TOLÉRANCE ZÉRO")
print("="*70)

db = MongoClient()['centralisation_db']

# Semaine cible
WEEK = '2026-W06'

# Chercher dates de la semaine
week_obs = db.prices_weekly.find_one({'week': WEEK})
if not week_obs:
    print(f"Erreur: Semaine {WEEK} introuvable")
    exit(1)

week_start = week_obs.get('week_start')
week_end = week_obs.get('week_end')

if not week_start or not week_end:
    print("Erreur: Dates semaine manquantes")
    exit(1)

print(f"\nSemaine {WEEK}: {week_start} → {week_end}")

# Pour chaque action de la semaine
week_actions = list(db.prices_weekly.find({'week': WEEK}))
print(f"Actions à traiter: {len(week_actions)}\n")

updated = 0

for obs in week_actions:
    symbol = obs['symbol']
    
    #Récupérer historique weekly pour cette action
    history = list(db.prices_weekly.find(
        {'symbol': symbol},
        {'week': 1, 'close': 1, 'high': 1, 'low': 1, 'volume': 1}
    ).sort('week', 1))
    
    if len(history) < 14:
        print(f"  {symbol:6} - Historique insuffisant ({len(history)} semaines)")
        continue
    
    # Calculer RSI (14 périodes)
    closes = [h.get('close', 0) for h in history]
    
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    # RSI adaptatif: au moins 7 variations
    if len(gains) < 7:
        print(f"  {symbol:6} - Pas assez de variations ({len(gains)})")
        continue
    
    # RSI: utiliser min(14, disponible)
    period = min(14, len(gains))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = round(100 - (100 / (1 + rs)), 2)
    
    # SMA5 et SMA10
    if len(closes) >= 10:
        sma5 = round(sum(closes[-5:]) / 5, 2)
        sma10 = round(sum(closes[-10:]) / 10, 2)
    elif len(closes) >= 5:
        sma5 = round(sum(closes[-5:]) / 5, 2)
        sma10 = None
    else:
        sma5 = None
        sma10 = None
    
    # Volume ratio
    volumes = [h.get('volume', 0) for h in history]
    current_vol = obs.get('volume', 0)
    
    if len(volumes) >= 8:
        avg_vol = sum(volumes[-8:]) / 8
        vol_ratio = round(current_vol / avg_vol, 2) if avg_vol > 0 else 0
    else:
        vol_ratio = 0
    
    # Update MongoDB
    update = {
        'rsi': rsi,
        'sma5': sma5,
        'sma10': sma10,
        'volume_ratio': vol_ratio,
        'indicators_computed': True,
        'updated_at': datetime.now()
    }
    
    result = db.prices_weekly.update_one(
        {'_id': obs['_id']},
        {'$set': update}
    )
    
    if result.modified_count > 0:
        updated += 1
        status = "✅" if rsi and sma5 else "⚠️ "
        print(f"  {status} {symbol:6} | RSI:{rsi:5.1f} | SMA5:{sma5 or 0:8.0f} | Vol ratio:{vol_ratio:.2f}")

print(f"\n{'='*70}")
print(f"✅ {updated}/{len(week_actions)} actions mises à jour")
print(f"{'='*70}\n")

# Vérification
with_rsi = db.prices_weekly.count_documents({'week': WEEK, 'rsi': {'$exists': True, '$ne': None}})
print(f"Vérification: {with_rsi} actions avec RSI pour {WEEK}")

if with_rsi > 0:
    print("\n✅ Indicateurs calculés - Prêt pour recommandations")
else:
    print("\n⚠️  Problème: RSI toujours manquant")

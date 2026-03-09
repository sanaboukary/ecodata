#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOSION 7-10 JOURS - VERSION SIMPLE
Détection opportuniste TOP 5 hausses hebdos
"""

from pymongo import MongoClient
from statistics import mean, stdev
from datetime import datetime
import sys

# MongoDB
client = MongoClient('localhost', 27017)
db = client['centralisation_db']

print("\n" + "="*80)
print("🔥 SYSTÈME EXPLOSION 7-10 JOURS - BRVM")
print("="*80)
print("Objectif: Détecter TOP 5 hausses hebdomadaires")
print("Horizon: 7-10 jours maximum")
print("Positions: MAX 1-2")
print("="*80 + "\n")

# Paramètres
week_str = sys.argv[1] if len(sys.argv) > 1 else '2026-W06'

print(f"📅 Semaine analysée: {week_str}\n")

# Récupérer tous les symboles pour cette semaine
symbols = db.prices_weekly.distinct('symbol', {'week': week_str})
print(f"📊 Actions disponibles: {len(symbols)}\n")

candidates = []

for symbol in symbols:
    # Ignorer indices
    if symbol in ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']:
        continue
    
    # Données semaine courante
    doc = db.prices_weekly.find_one({'symbol': symbol, 'week': week_str})
    if not doc:
        continue
    
    close = doc.get('close', 0)
    atr_pct = doc.get('atr_pct')
    rsi = doc.get('rsi', 50)
    volume = doc.get('volume', 0)
    volume_zscore = doc.get('volume_zscore')
    acceleration = doc.get('acceleration')
    variation_pct = doc.get('variation_pct', 0)
    
    if not close or close == 0:
        continue
    
    # FILTRES DE BASE
    # ATR entre 5% et 30%
    if not atr_pct or atr_pct < 5 or atr_pct > 30:
        continue
    
    # RSI pas trop extrême
    if rsi and (rsi < 20 or rsi > 80):
        continue
    
    # ==============================================================
    # CALCUL SCORE EXPLOSION
    # ==============================================================
    
    score_explosion = 0
    details = []
    
    # 1. BREAKOUT SCORE (30%)
    # Détecter compression puis rupture
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'close': 1, 'atr_pct': 1, 'high': 1, 'volume': 1}
    ).sort('week', -1).limit(4))
    
    breakout_score = 0
    if len(history) >= 3:
        current = history[0]
        past_3w = history[1:4]
        
        # Compression ATR
        past_atrs = [h.get('atr_pct', 0) for h in past_3w if h.get('atr_pct')]
        if past_atrs:
            avg_atr = mean(past_atrs)
            if atr_pct < avg_atr * 0.85:
                breakout_score += 15
                details.append("Compression ATR")
        
        # Rupture prix
        past_highs = [h.get('high', 0) for h in past_3w]
        max_high = max(past_highs) if past_highs else 0
        if close > max_high and max_high > 0:
            breakout_score += 25
            details.append("🚀 Breakout prix")
        
        # Volume confirmation
        past_vols = [h.get('volume', 0) for h in past_3w if h.get('volume', 0) > 0]
        if past_vols:
            avg_vol = mean(past_vols)
            if volume > avg_vol * 1.8:
                breakout_score += 10
                details.append("Volume explosion")
    
    breakout_score = min(breakout_score, 100)
    score_explosion += breakout_score * 0.30
    
    # 2. VOLUME Z-SCORE (25%)
    volume_score = 0
    if volume_zscore and volume_zscore >= 2.0:
        volume_score = 100
        details.append(f"📊 Volume Z={volume_zscore:+.1f} FORT")
    elif volume_zscore and volume_zscore >= 1.5:
        volume_score = 70
        details.append(f"Volume Z={volume_zscore:+.1f}")
    elif volume_zscore and volume_zscore >= 1.0:
        volume_score = 40
    
    score_explosion += volume_score * 0.25
    
    # 3. ACCELERATION (20%)
    accel_score = 0
    if acceleration and acceleration >= 5:
        accel_score = 100
        details.append(f"⚡ Accel {acceleration:+.1f}% FORTE")
    elif acceleration and acceleration >= 3:
        accel_score = 70
        details.append(f"Accel {acceleration:+.1f}%")
    elif acceleration and acceleration >= 1:
        accel_score = 40
    
    score_explosion += accel_score * 0.20
    
    # 4. ATR ZONE (15%)
    atr_score = 0
    if 6 <= atr_pct <= 12:  # Zone idéale BRVM
        atr_score = 100
    elif 5 <= atr_pct <= 18:
        atr_score = 60
    else:
        atr_score = 30
    
    score_explosion += atr_score * 0.15
    
    # 5. VARIATION POSITIVE (10%)
    var_score = 0
    if variation_pct >= 5:
        var_score = 100
        details.append(f"📈 Var {variation_pct:+.1f}%")
    elif variation_pct >= 2:
        var_score = 60
    elif variation_pct >= 0:
        var_score = 30
    
    score_explosion += var_score * 0.10
    
    # FILTRE SCORE MINIMUM
    if score_explosion < 60:
        continue
    
    # ==============================================================
    # CANDIDAT VALIDÉ
    # ==============================================================
    
    # Stop/Target
    stop_pct = 0.8 * atr_pct
    target_pct = 1.8 * atr_pct
    risk_reward = round(target_pct / stop_pct, 1) if stop_pct > 0 else 0
    
    candidates.append({
        'symbol': symbol,
        'score': round(score_explosion, 1),
        'close': close,
        'atr_pct': atr_pct,
        'rsi': rsi,
        'volume_zscore': volume_zscore,
        'acceleration': acceleration,
        'variation_pct': variation_pct,
        'breakout_score': breakout_score,
        'stop_pct': stop_pct,
        'target_pct': target_pct,
        'risk_reward': risk_reward,
        'details': ' | '.join(details) if details else 'Setup standard'
    })

# Tri par score
candidates.sort(key=lambda x: x['score'], reverse=True)

# Limiter à 2 positions
candidates = candidates[:2]

print("="*80)
print(f"🔥 RECOMMANDATIONS EXPLOSION 7-10 JOURS - {week_str}")
print("="*80 + "\n")

if not candidates:
    print("⚠️  AUCUNE OPPORTUNITÉ DÉTECTÉE")
    print("\nC'est normal - le système est très sélectif.")
    print("Il ne recommande que les explosions potentielles les plus fortes.")
    print("\n💡 Critères:")
    print("   - Score EXPLOSION ≥ 60/100")
    print("   - Breakout confirmé (compression → rupture)")
    print("   - Volume anormal (Z-score ≥ 1.5)")
    print("   - Momentum accéléré (≥ +3%)")
    print("   - ATR dans zone 5-30%")
    print("\n" + "="*80 + "\n")
else:
    for i, cand in enumerate(candidates, 1):
        print(f"{'='*80}")
        print(f"#{i} - {cand['symbol']} - SCORE EXPLOSION: {cand['score']}/100")
        print(f"{'='*80}")
        print(f"\n💰 PRIX: {cand['close']:.0f} FCFA")
        print(f"🎯 TARGET: +{cand['target_pct']:.1f}% ({cand['close'] * (1 + cand['target_pct']/100):.0f} FCFA)")
        print(f"🛑 STOP: -{cand['stop_pct']:.1f}% ({cand['close'] * (1 - cand['stop_pct']/100):.0f} FCFA)")
        print(f"⚖️  RISK/REWARD: {cand['risk_reward']}")
        print(f"⏱️  HORIZON: 7-10 jours MAX")
        
        print(f"\n📊 INDICATEURS:")
        print(f"   ATR: {cand['atr_pct']:.1f}%")
        print(f"   RSI: {cand['rsi']:.0f}")
        print(f"   Variation semaine: {cand['variation_pct']:+.1f}%")
        if cand['volume_zscore']:
            print(f"   Volume Z-score: {cand['volume_zscore']:+.1f}")
        if cand['acceleration']:
            print(f"   Accélération: {cand['acceleration']:+.1f}%")
        
        print(f"\n🔥 DÉTECTION:")
        print(f"   Breakout Score: {cand['breakout_score']}/100")
        print(f"   {cand['details']}")
        
        print(f"\n💡 STRATÉGIE:")
        print(f"   Position: 15-20% capital (concentration)")
        print(f"   Sortie: 7-10 jours MAX (rotation rapide)")
        print(f"   Suivi: QUOTIDIEN (volatilité court terme)")
        print()
    
    # Sauvegarder dans MongoDB
    db.decisions_explosion_7j.delete_many({'week': week_str})
    
    for rank, cand in enumerate(candidates, 1):
        decision = {
            'week': week_str,
            'rank': rank,
            'symbol': cand['symbol'],
            'signal': 'BUY_EXPLOSION_7J',
            'explosion_score': cand['score'],
            'close': cand['close'],
            'stop_pct': cand['stop_pct'],
            'target_pct': cand['target_pct'],
            'risk_reward': cand['risk_reward'],
            'atr_pct': cand['atr_pct'],
            'rsi': cand['rsi'],
            'volume_zscore': cand['volume_zscore'],
            'acceleration': cand['acceleration'],
            'variation_pct': cand['variation_pct'],
            'breakout_score': cand['breakout_score'],
            'details': cand['details'],
            'horizon': '7-10 jours',
            'generated_at': datetime.now()
        }
        db.decisions_explosion_7j.insert_one(decision)
    
    print("="*80)
    print(f"✅ {len(candidates)} POSITION(S) SAUVEGARDÉE(S)")
    print("="*80 + "\n")
    
    print("💾 Collection MongoDB: decisions_explosion_7j")
    print("\n🚀 ALLOCATION CAPITAL:")
    print("   60% → WOS STABLE (3-6 positions, 2-8 semaines)")
    print(f"   {len(candidates) * 15}% → EXPLOSION 7J ({len(candidates)} position(s), 7-10 jours)")
    print(f"   {40 - len(candidates) * 15}% → Cash réserve")

print("\n" + "="*80)
print("📊 SYSTÈME DUAL MOTOR ACTIVÉ")
print("="*80)
print("\nCommandes utiles:")
print("  python comparer_dual_motor.py  → Comparer WOS vs EXPLOSION")
print("  python afficher_toutes_recommandations.py  → Voir toutes recos")
print("\n" + "="*80 + "\n")

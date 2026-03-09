#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCUL COMPLET INDICATEURS TECHNIQUES - MODE PRO 30 ANS EXPERIENCE BRVM
========================================================================

Recalcule TOUS les indicateurs techniques pour TOUS les documents prices_weekly
avec les calibrations d'expert BRVM (30 ans d'experience marche)

INDICATEURS CALCULES:
---------------------
1. RSI (14 periodes) - Calibre BRVM: oversold=40, overbought=65
2. ATR% (5 periodes) - Zone tradable: 6-25%, mort <6%, excessif >25%
3. SMA 5/10 semaines - Detection tendance
4. Volume Ratio (8 semaines) - Anomalies volume
5. Volume Z-Score (8 semaines) - Detection statistique
6. Volatilite (12 semaines) - Mesure risque
7. Acceleration Momentum - Momentum accelere
8. Trend Signal - BULLISH/BEARISH/NEUTRAL
9. RSI Signal - OVERSOLD/OVERBOUGHT/NEUTRAL
10. ATR Signal - DEAD/NORMAL/VOLATILE/EXCESSIVE

EXECUTION:
----------
python calculer_tous_indicateurs_pro.py

DUREE: ~3-5 min pour 668 documents (14 semaines x 47 actions)
"""

import os, sys
from pathlib import Path
from datetime import datetime
from statistics import mean, stdev
import math

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION EXPERT BRVM (30 ANS EXPERIENCE)
# ============================================================================

# RSI - Calibration BRVM
RSI_PERIOD = 14
RSI_OVERSOLD = 40   # BRVM specifique (vs 30 standard)
RSI_OVERBOUGHT = 65  # BRVM specifique (vs 70 standard)

# ATR - Calibration BRVM
ATR_PERIOD = 5       # Weekly optimise pour BRVM
ATR_DEAD_MARKET = 6.0    # < 6% = marche mort
ATR_MIN_TRADE = 6.0      # Minimum pour trader
ATR_MAX_TRADE = 25.0     # Maximum zone tradable
ATR_EXCESSIVE = 25.0     # > 25% = excessif

# SMA - Detection tendance
SMA_FAST = 5
SMA_SLOW = 10

# Volume - Analyse statistique
VOLUME_PERIOD = 8        # Moyenne volume
VOLUME_ZSCORE_PERIOD = 8 # Z-score historique

# Volatilite - Mesure risque
VOLATILITY_PERIOD = 12

# Acceleration - Momentum
ACCEL_MIN_WEEKS = 3

print("=" * 80)
print("CALCUL COMPLET INDICATEURS TECHNIQUES - MODE PRO BRVM")
print("=" * 80)
print(f"\nConfiguration Expert (30 ans experience):")
print(f"  RSI: {RSI_PERIOD} periodes (oversold={RSI_OVERSOLD}, overbought={RSI_OVERBOUGHT})")
print(f"  ATR: {ATR_PERIOD} periodes (zone tradable: {ATR_MIN_TRADE}-{ATR_MAX_TRADE}%)")
print(f"  SMA: {SMA_FAST}/{SMA_SLOW} semaines")
print(f"  Volume: {VOLUME_PERIOD} semaines (Z-score: {VOLUME_ZSCORE_PERIOD})")
print(f"  Volatilite: {VOLATILITY_PERIOD} semaines")
print("=" * 80)

# ============================================================================
# FONCTIONS CALCUL INDICATEURS
# ============================================================================

def calculate_rsi(closes, period=14):
    """RSI calibre BRVM"""
    if len(closes) < period + 1:
        # Mode adaptatif: minimum 7 periodes
        if len(closes) < 8:
            return None
        period = min(period, len(closes) - 1)
    
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
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def calculate_atr_pct(weekly_history, period=5):
    """
    ATR% BRVM PRO - Calibration 30 ans experience
    Filtre semaines mortes automatiquement
    """
    if len(weekly_history) < period + 1:
        return None
    
    # Filtrer semaines actives (volume > 0 OU variation > 0.5%)
    active_weeks = []
    for w in weekly_history:
        close = w.get('close', 0)
        volume = w.get('volume', 0)
        open_price = w.get('open', close)
        
        variation_pct = abs((close - open_price) / open_price * 100) if open_price > 0 else 0
        
        if volume > 0 or variation_pct > 0.5:
            active_weeks.append(w)
    
    # Besoin minimum 4 semaines actives
    if len(active_weeks) < max(4, period):
        # Fallback: utiliser toutes les semaines
        if len(weekly_history) >= 4:
            active_weeks = weekly_history
        else:
            return None
    
    # Calculer True Range sur semaines actives
    true_ranges = []
    
    for i in range(1, len(active_weeks)):
        current = active_weeks[i]
        previous = active_weeks[i-1]
        
        high = current.get('high', current.get('close', 0))
        low = current.get('low', current.get('close', 0))
        prev_close = previous.get('close', 0)
        
        if prev_close > 0:
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    # ATR = moyenne des TR
    atr = sum(true_ranges[-period:]) / len(true_ranges[-period:])
    
    # Current price
    current_price = active_weeks[-1].get('close', 0)
    
    if current_price <= 0:
        return None
    
    # ATR%
    atr_pct = (atr / current_price) * 100
    
    return round(atr_pct, 2)

def calculate_sma(closes, period):
    """Simple Moving Average"""
    if len(closes) < period:
        return None
    
    sma = sum(closes[-period:]) / period
    return round(sma, 2)

def calculate_volatility(weekly_history, period=12):
    """Volatilite hebdomadaire (ecart-type rendements)"""
    if len(weekly_history) < period:
        return None
    
    closes = [w.get('close', 0) for w in weekly_history[-period:] if w.get('close', 0) > 0]
    
    if len(closes) < 4:
        return None
    
    returns = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0:
            ret = (closes[i] - closes[i-1]) / closes[i-1]
            returns.append(ret)
    
    if len(returns) < 3:
        return None
    
    variance = sum((r - (sum(returns)/len(returns)))**2 for r in returns) / len(returns)
    volatility = math.sqrt(variance)
    
    return round(volatility * 100, 2)

def calculate_volume_zscore(symbol, week_str, history_weeks=8):
    """Volume Z-Score - Detection anomalies statistiques"""
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'volume': 1}
    ).sort('week', -1).limit(history_weeks + 1))
    
    if len(history) < 4:
        return None
    
    current = history[0]
    past = history[1:]
    
    volumes = [h.get('volume', 0) for h in past if h.get('volume', 0) > 0]
    
    if len(volumes) < 3:
        return None
    
    vol_mean = mean(volumes)
    vol_std = stdev(volumes) if len(volumes) > 1 else 0
    
    current_vol = current.get('volume', 0)
    
    if vol_std > 0 and current_vol > 0:
        z_score = (current_vol - vol_mean) / vol_std
        return round(z_score, 2)
    
    return 0.0

def calculate_acceleration(symbol, week_str):
    """Acceleration Momentum - Momentum accelere"""
    history = list(db.prices_weekly.find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'close': 1}
    ).sort('week', -1).limit(3))
    
    if len(history) < 3:
        return None
    
    close_0 = history[0].get('close', 0)
    close_1 = history[1].get('close', 0)
    close_2 = history[2].get('close', 0)
    
    if close_1 <= 0 or close_2 <= 0:
        return None
    
    var_1 = ((close_0 - close_1) / close_1) * 100
    var_2 = ((close_1 - close_2) / close_2) * 100
    
    acceleration = var_1 - var_2
    
    return round(acceleration, 2)

# ============================================================================
# CALCUL COMPLET POUR UN DOCUMENT
# ============================================================================

def compute_all_indicators_for_document(doc):
    """
    Calcule TOUS les indicateurs pour un document prices_weekly
    Returns: dict with all indicators or None if insufficient data
    """
    symbol = doc['symbol']
    week_str = doc['week']
    
    # Recuperer historique complet pour ce symbole
    weekly_history = list(db.prices_weekly.find({
        'symbol': symbol,
        'week': {'$lte': week_str}
    }).sort('week', 1))
    
    # Minimum absolu: 5 semaines pour demarrage
    if len(weekly_history) < 5:
        return None
    
    # Extraire closes
    closes = [w.get('close', 0) for w in weekly_history if w.get('close', 0) > 0]
    
    if len(closes) < 5:
        return None
    
    # ========================================================================
    # CALCUL INDICATEURS
    # ========================================================================
    
    # 1. RSI (adaptatif)
    rsi = calculate_rsi(closes, RSI_PERIOD)
    
    # 2. ATR% BRVM PRO
    atr_pct = calculate_atr_pct(weekly_history, ATR_PERIOD)
    
    # 3. SMA 5/10
    sma5 = calculate_sma(closes, SMA_FAST)
    sma10 = calculate_sma(closes, SMA_SLOW)
    
    # 4. Volatilite
    volatility = calculate_volatility(weekly_history, VOLATILITY_PERIOD)
    
    # 5. Volume ratio
    volumes = [w.get('volume', 0) for w in weekly_history[-VOLUME_PERIOD:]]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    current_volume = doc.get('volume', 0)
    volume_ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 0.0
    
    # 6. Volume Z-Score
    volume_zscore = calculate_volume_zscore(symbol, week_str, VOLUME_ZSCORE_PERIOD)
    
    # 7. Acceleration
    acceleration = calculate_acceleration(symbol, week_str)
    
    # ========================================================================
    # SIGNAUX ET DETECTION
    # ========================================================================
    
    # Signal RSI (calibre BRVM)
    rsi_signal = 'NEUTRAL'
    if rsi:
        if rsi < RSI_OVERSOLD:
            rsi_signal = 'OVERSOLD'
        elif rsi > RSI_OVERBOUGHT:
            rsi_signal = 'OVERBOUGHT'
    
    # Signal ATR (calibre BRVM)
    atr_signal = 'NORMAL'
    tradable = True
    
    if atr_pct:
        if atr_pct < ATR_DEAD_MARKET:
            atr_signal = 'DEAD'
            tradable = False
        elif atr_pct > ATR_EXCESSIVE:
            atr_signal = 'EXCESSIVE'
            tradable = False
        elif atr_pct > ATR_MAX_TRADE:
            atr_signal = 'VOLATILE'
    
    # Trend (SMA crossover)
    trend = 'NEUTRAL'
    if sma5 and sma10:
        if sma5 > sma10 * 1.02:  # +2% minimum
            trend = 'BULLISH'
        elif sma5 < sma10 * 0.98:  # -2% minimum
            trend = 'BEARISH'
    
    # ========================================================================
    # RETOUR COMPLET
    # ========================================================================
    
    return {
        # Indicateurs techniques
        'rsi': rsi,
        'atr_pct': atr_pct,
        'sma5': sma5,
        'sma10': sma10,
        'volatility': volatility,
        'volume_ratio': volume_ratio,
        'volume_zscore': volume_zscore,
        'acceleration': acceleration,
        
        # Signaux
        'rsi_signal': rsi_signal,
        'atr_signal': atr_signal,
        'trend': trend,
        'tradable': tradable,
        
        # Metadata
        'indicators_computed': True,
        'indicators_updated_at': datetime.now()
    }

# ============================================================================
# EXECUTION PRINCIPALE
# ============================================================================

def main():
    print("\n[1] RECUPERATION DOCUMENTS...")
    
    # Recuperer TOUS les documents prices_weekly
    all_docs = list(db.prices_weekly.find().sort('week', 1))
    
    print(f"  Total documents: {len(all_docs)}")
    
    # Statistiques avant
    before_with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    print(f"  Avec indicateurs AVANT: {before_with_indicators}/{len(all_docs)} ({100*before_with_indicators/len(all_docs):.1f}%)")
    
    print("\n[2] CALCUL INDICATEURS...")
    print("  (Mode adaptatif: minimum 5 semaines, optimise si 14+ semaines)\n")
    
    success_count = 0
    skip_count = 0
    update_count = 0
    error_count = 0
    
    # Grouper par semaine pour affichage
    weeks_processed = set()
    
    for i, doc in enumerate(all_docs, 1):
        symbol = doc['symbol']
        week = doc['week']
        
        # Affichage progression par semaine
        if week not in weeks_processed:
            weeks_processed.add(week)
            print(f"\n  Semaine {week}:")
        
        try:
            # Calculer indicateurs
            indicators = compute_all_indicators_for_document(doc)
            
            if indicators:
                # Mettre a jour MongoDB
                result = db.prices_weekly.update_one(
                    {'_id': doc['_id']},
                    {'$set': indicators}
                )
                
                if result.modified_count > 0:
                    update_count += 1
                    print(f"    {symbol:10s} [OK]", end='')
                    
                    # Afficher quelques indicateurs cles
                    if indicators.get('rsi'):
                        print(f" RSI={indicators['rsi']:.1f}", end='')
                    if indicators.get('atr_pct'):
                        print(f" ATR={indicators['atr_pct']:.1f}%", end='')
                    if indicators.get('trend'):
                        print(f" {indicators['trend']}", end='')
                    print()
                    
                success_count += 1
            else:
                skip_count += 1
                # Afficher seulement les skips interessants (debut de donnees)
                if week in ['2025-W38', '2025-W39', '2025-W40']:
                    print(f"    {symbol:10s} [SKIP] historique insuffisant")
        
        except Exception as e:
            error_count += 1
            print(f"    {symbol:10s} [ERROR] {str(e)[:50]}")
    
    # Statistiques apres
    after_with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    
    print("\n" + "=" * 80)
    print("RESULTAT")
    print("=" * 80)
    print(f"  Documents traites       : {len(all_docs)}")
    print(f"  Indicateurs calcules    : {success_count}")
    print(f"  Mis a jour MongoDB      : {update_count}")
    print(f"  Skippes (< 5 semaines)  : {skip_count}")
    print(f"  Erreurs                 : {error_count}")
    print()
    print(f"  AVANT: {before_with_indicators}/{len(all_docs)} ({100*before_with_indicators/len(all_docs):.1f}%)")
    print(f"  APRES: {after_with_indicators}/{len(all_docs)} ({100*after_with_indicators/len(all_docs):.1f}%)")
    print()
    
    if after_with_indicators >= len(all_docs) * 0.9:
        print("  [OK] 90%+ des documents ont leurs indicateurs")
    elif after_with_indicators >= len(all_docs) * 0.7:
        print("  [!!] 70%+ OK mais certaines actions manquent d'historique")
    else:
        print("  [!] Moins de 70% - verifier la collecte de donnees")
    
    print("\n" + "=" * 80)
    print("ETAPE SUIVANTE")
    print("=" * 80)
    print("  Executer le pipeline complet:")
    print("    python pipeline_brvm.py")
    print()
    print("  Ou executer l'analyse IA directement:")
    print("    python analyse_ia_simple.py")
    print("=" * 80)

if __name__ == "__main__":
    main()

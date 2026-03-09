#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOSION 7-10 JOURS DETECTOR
Détection opportuniste TOP 5 hausses hebdomadaires BRVM

PHILOSOPHIE:
- Horizon court terme : 7-10 jours
- Objectif : TOP 5 hausses hebdo
- Max 1-2 positions simultanées
- Rotation rapide du capital

INNOVATION:
- Breakout detector (compression → explosion)
- Volume Z-score (anomalies statistiques)
- Momentum accéléré (variations croissantes)
- Retard réaction (news décalées)
- EXPLOSION_SCORE (≠ WOS)

DIFFÉRENCE vs WOS_STABLE:
WOS = Stable 2-8 semaines, qualité > quantité
EXPLOSION = Opportuniste 7-10j, timing > scoring
"""

import os, sys
from pathlib import Path
from datetime import datetime, timedelta
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
# CONFIGURATION EXPLOSION 7-10 JOURS
# ============================================================================

COLLECTION_WEEKLY = "prices_weekly"
COLLECTION_SEMANTIC = "AGREGATION_SEMANTIQUE_ACTION"
COLLECTION_DECISIONS = "decisions_explosion_7j"
COLLECTION_TRACK_RECORD = "track_record_explosion_7j"

# Seuils détection explosion
EXPLOSION_CONFIG = {
    # Breakout
    'breakout_compression_factor': 0.85,  # ATR < 85% moyenne
    'breakout_volume_min': 1.8,           # Volume ratio ≥ 1.8
    'breakout_range_weeks': 3,            # Rupture vs 3 dernières semaines
    
    # Volume anormal
    'volume_zscore_threshold': 2.0,       # Z-score ≥ 2 = anormal
    'volume_history_weeks': 8,            # Historique pour calcul
    
    # Momentum accéléré
    'acceleration_positive_threshold': 3, # Accélération ≥ 3%
    
    # Retard réaction
    'reaction_lag_weeks': 1,              # Décalage news → mouvement
    
    # Score explosion
    'explosion_min_score': 60,            # Score minimum pour reco
    
    # Stop/Target court terme
    'stop_multiplier': 0.8,               # Stop = 0.8× ATR
    'target_multiplier': 1.8,             # Target = 1.8× ATR
    
    # Positions
    'max_positions': 2,                   # MAX 1-2 positions
    
    # Régime marché
    'market_bullish_multiplier': 1.1,
    'market_bearish_multiplier': 0.85,
}

# Poids EXPLOSION_SCORE
WEIGHTS = {
    'breakout': 0.30,
    'volume_zscore': 0.25,
    'acceleration': 0.20,
    'atr_zone': 0.15,
    'sentiment': 0.10
}

# ============================================================================
# MODULE 1: BREAKOUT DETECTOR
# ============================================================================

def detect_breakout(symbol, week_str):
    """
    Détecte compression puis rupture brutale
    
    Condition A - Compression:
      ATR_pct < moyenne_ATR_6_semaines
      ET range resserré sur 2 semaines
      
    Condition B - Rupture:
      Close > max(3 dernières semaines)
      ET volume_ratio ≥ 1.8
      
    Retour: (score 0-100, détails)
    """
    # Récupérer historique
    history = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'high': 1, 'low': 1, 'close': 1, 'atr_pct': 1, 'volume_ratio': 1}
    ).sort('week', -1).limit(6))
    
    if len(history) < 4:
        return 0, "Historique insuffisant"
    
    current = history[0]
    
    # ========================================================================
    # CONDITION A: COMPRESSION
    # ========================================================================
    
    # ATR moyen 6 semaines
    atr_values = [h.get('atr_pct', 0) for h in history if h.get('atr_pct')]
    if len(atr_values) < 3:
        return 0, "ATR insuffisant"
    
    atr_mean = mean(atr_values)
    current_atr = current.get('atr_pct', 0)
    
    compression = current_atr < (atr_mean * EXPLOSION_CONFIG['breakout_compression_factor'])
    
    # Range resserré 2 dernières semaines
    recent_ranges = []
    for h in history[:2]:
        high = h.get('high', 0)
        low = h.get('low', 0)
        close = h.get('close', 1)
        if close > 0:
            range_pct = ((high - low) / close) * 100
            recent_ranges.append(range_pct)
    
    range_compressed = False
    if recent_ranges:
        avg_range = mean(recent_ranges)
        range_compressed = avg_range < (atr_mean * 0.9)
    
    # ========================================================================
    # CONDITION B: RUPTURE
    # ========================================================================
    
    # Close > max(3 dernières semaines)
    last_3_highs = [h.get('high', 0) for h in history[1:4]]
    max_high_3w = max(last_3_highs) if last_3_highs else 0
    
    current_close = current.get('close', 0)
    breakout_price = current_close > max_high_3w
    
    # Volume ratio ≥ 1.8
    volume_ratio = current.get('volume_ratio', 0)
    breakout_volume = volume_ratio >= EXPLOSION_CONFIG['breakout_volume_min']
    
    # ========================================================================
    # SCORING
    # ========================================================================
    
    score = 0
    details = []
    
    # Compression détectée
    if compression:
        score += 30
        details.append(f"Compression ATR ({current_atr:.1f}% < {atr_mean:.1f}%)")
    
    if range_compressed:
        score += 20
        details.append("Range resserré 2 semaines")
    
    # Rupture brutale
    if breakout_price and breakout_volume:
        score += 50  # SIGNAL FORT
        details.append(f"RUPTURE: Close {current_close:.0f} > Max3W {max_high_3w:.0f}, Vol {volume_ratio:.1f}x")
    elif breakout_price:
        score += 25
        details.append(f"Rupture prix sans volume")
    elif breakout_volume:
        score += 15
        details.append(f"Volume élevé ({volume_ratio:.1f}x) sans rupture prix")
    
    # Bonus si compression → rupture (pattern classique)
    if (compression or range_compressed) and (breakout_price and breakout_volume):
        score = min(100, score + 20)
        details.append("⚡ PATTERN COMPRESSION→EXPLOSION")
    
    return score, " | ".join(details)

# ============================================================================
# MODULE 2: VOLUME ANORMAL (Z-SCORE)
# ============================================================================

def calculate_volume_zscore(symbol, week_str):
    """
    Calcule Z-score du volume (détection anomalies statistiques)
    
    Z-score = (volume_current - mean) / std
    
    Z ≥ 2.0 = anomalie forte (top 2.5%)
    Z ≥ 1.5 = anomalie modérée
    
    Retour: (z_score, score 0-100, détails)
    """
    # Récupérer historique volume
    history = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'volume': 1}
    ).sort('week', -1).limit(EXPLOSION_CONFIG['volume_history_weeks'] + 1))
    
    if len(history) < 4:
        return 0, 0, "Historique volume insuffisant"
    
    current = history[0]
    past = history[1:]
    
    # Volumes historiques
    volumes = [h.get('volume', 0) for h in past]
    volumes = [v for v in volumes if v > 0]  # Filtrer 0
    
    if len(volumes) < 3:
        return 0, 0, "Pas assez de semaines avec volume"
    
    # Statistiques
    vol_mean = mean(volumes)
    vol_std = stdev(volumes) if len(volumes) > 1 else 0
    
    current_vol = current.get('volume', 0)
    
    # Z-score
    if vol_std > 0:
        z_score = (current_vol - vol_mean) / vol_std
    else:
        z_score = 0
    
    # Scoring
    if z_score >= EXPLOSION_CONFIG['volume_zscore_threshold']:
        score = 100
        detail = f"⚡ VOLUME ANORMAL: Z={z_score:.2f} (top 2.5%)"
    elif z_score >= 1.5:
        score = 70
        detail = f"Volume élevé: Z={z_score:.2f}"
    elif z_score >= 1.0:
        score = 40
        detail = f"Volume supérieur: Z={z_score:.2f}"
    elif z_score >= 0.5:
        score = 20
        detail = f"Volume normal+: Z={z_score:.2f}"
    else:
        score = 0
        detail = f"Volume normal/faible: Z={z_score:.2f}"
    
    return z_score, score, detail

# ============================================================================
# MODULE 3: MOMENTUM ACCÉLÉRÉ
# ============================================================================

def calculate_acceleration(symbol, week_str):
    """
    Détecte accélération momentum (variations croissantes)
    
    Accélération = Variation(week) - Variation(week-1)
    
    Exemple détection:
      S-2: -3%
      S-1: +2%  → Accélération = +2 - (-3) = +5%
      S0:  +6%  → Accélération = +6 - (+2) = +4%
      
    Accélération positive forte → TOP 5 potentiel
    
    Retour: (acceleration, score 0-100, détails)
    """
    # Récupérer 3 dernières semaines
    history = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'variation_pct': 1}
    ).sort('week', -1).limit(3))
    
    if len(history) < 3:
        return 0, 0, "Historique insuffisant"
    
    # Variations
    var_0 = history[0].get('variation_pct', 0)  # Cette semaine
    var_1 = history[1].get('variation_pct', 0)  # Semaine -1
    var_2 = history[2].get('variation_pct', 0)  # Semaine -2
    
    # Accélération
    accel = var_0 - var_1
    
    # Scoring
    score = 0
    details = []
    
    # Accélération forte positive
    if accel >= EXPLOSION_CONFIG['acceleration_positive_threshold']:
        score = 100
        details.append(f"⚡ ACCÉLÉRATION FORTE: +{accel:.1f}%")
    elif accel >= 2:
        score = 70
        details.append(f"Accélération modérée: +{accel:.1f}%")
    elif accel >= 1:
        score = 40
        details.append(f"Accélération faible: +{accel:.1f}%")
    elif accel > 0:
        score = 20
        details.append(f"Momentum positif: +{accel:.1f}%")
    else:
        score = 0
        details.append(f"Décélération: {accel:.1f}%")
    
    # Bonus pattern retournement
    if var_2 < 0 and var_1 > 0 and var_0 > var_1:
        score = min(100, score + 20)
        details.append(f"Pattern retournement ({var_2:.1f}% → {var_1:.1f}% → {var_0:.1f}%)")
    
    details_str = " | ".join(details)
    
    return accel, score, details_str

# ============================================================================
# MODULE 4: RETARD RÉACTION
# ============================================================================

def detect_reaction_lag(symbol, week_str):
    """
    Détecte retard réaction BRVM (news N-1, mouvement N)
    
    Pattern BRVM typique:
    - News positive semaine N-1
    - Absence hausse semaine N-1 (prix inerte)
    - Début hausse semaine N (réaction décalée)
    
    Retour: (score 0-100, détails)
    """
    # Chercher sentiment semaine N-1
    history = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'week': 1, 'variation_pct': 1}
    ).sort('week', -1).limit(2))
    
    if len(history) < 2:
        return 0, "Historique insuffisant"
    
    current = history[0]
    previous = history[1]
    
    # Variations
    var_current = current.get('variation_pct', 0)
    var_previous = previous.get('variation_pct', 0)
    
    # Chercher sentiment semaine N-1
    prev_week = previous['week']
    semantic_prev = db[COLLECTION_SEMANTIC].find_one({
        'ticker': symbol,
        'semaine': prev_week
    })
    
    score = 0
    details = []
    
    # News positive N-1
    sentiment_prev = None
    if semantic_prev:
        sentiment_prev = semantic_prev.get('sentiment_general', 'NEUTRAL')
    
    # Pattern retard
    if sentiment_prev == 'POSITIVE' and var_previous < 2 and var_current > 3:
        score = 100
        details.append(f"⚡ RETARD CLASSIQUE: News+ S-1, Inerte ({var_previous:.1f}%), Explosion S0 ({var_current:.1f}%)")
    elif sentiment_prev == 'POSITIVE' and var_current > var_previous + 3:
        score = 60
        details.append(f"Retard modéré: News+ décalée, +{var_current - var_previous:.1f}% cette semaine")
    elif var_previous < 1 and var_current > 5:
        score = 40
        details.append(f"Réveil après latence: {var_previous:.1f}% → {var_current:.1f}%")
    else:
        details.append("Pas de pattern retard détecté")
    
    return score, " | ".join(details)

# ============================================================================
# MODULE 5: EXPLOSION_SCORE
# ============================================================================

def calculate_explosion_score(symbol, week_str):
    """
    Score EXPLOSION 7-10 jours (≠ WOS)
    
    EXPLOSION_SCORE = 
      0.30 × Breakout +
      0.25 × Volume_zscore +
      0.20 × Acceleration +
      0.15 × ATR_zone +
      0.10 × Sentiment
    
    Retour: (score, détails dict)
    """
    # Récupérer données weekly
    weekly = db[COLLECTION_WEEKLY].find_one({
        'symbol': symbol,
        'week': week_str
    })
    
    if not weekly:
        return 0, {'error': 'Pas de données weekly'}
    
    # ========================================================================
    # 1. BREAKOUT (30%)
    # ========================================================================
    
    breakout_score, breakout_details = detect_breakout(symbol, week_str)
    
    # ========================================================================
    # 2. VOLUME Z-SCORE (25%)
    # ========================================================================
    
    z_score, volume_zscore_score, volume_details = calculate_volume_zscore(symbol, week_str)
    
    # ========================================================================
    # 3. ACCELERATION (20%)
    # ========================================================================
    
    accel, accel_score, accel_details = calculate_acceleration(symbol, week_str)
    
    # ========================================================================
    # 4. ATR ZONE (15%)
    # ========================================================================
    
    atr_pct = weekly.get('atr_pct', 0)
    
    # Zone idéale explosion court terme: 8-18%
    if 8 <= atr_pct <= 18:
        atr_zone_score = 100
    elif 6 <= atr_pct < 8:
        atr_zone_score = 60
    elif 18 < atr_pct <= 25:
        atr_zone_score = 60
    else:
        atr_zone_score = 0
    
    # ========================================================================
    # 5. SENTIMENT (10%)
    # ========================================================================
    
    semantic = db[COLLECTION_SEMANTIC].find_one({
        'ticker': symbol,
        'semaine': week_str
    })
    
    if semantic:
        sentiment = semantic.get('sentiment_general', 'NEUTRAL')
        if sentiment == 'POSITIVE':
            sentiment_score = 100
        elif sentiment == 'NEUTRAL':
            sentiment_score = 50
        elif sentiment == 'NEGATIVE':
            sentiment_score = 20
        else:
            sentiment_score = 0
    else:
        sentiment_score = 50  # Neutre par défaut
        sentiment = 'NEUTRAL'
    
    # ========================================================================
    # SCORE FINAL
    # ========================================================================
    
    explosion_score = (
        WEIGHTS['breakout'] * breakout_score +
        WEIGHTS['volume_zscore'] * volume_zscore_score +
        WEIGHTS['acceleration'] * accel_score +
        WEIGHTS['atr_zone'] * atr_zone_score +
        WEIGHTS['sentiment'] * sentiment_score
    )
    
    details = {
        'explosion_score': round(explosion_score, 1),
        'breakout_score': round(breakout_score, 1),
        'breakout_details': breakout_details,
        'volume_zscore_score': round(volume_zscore_score, 1),
        'volume_zscore': round(z_score, 2),
        'volume_details': volume_details,
        'acceleration_score': round(accel_score, 1),
        'acceleration': round(accel, 2),
        'acceleration_details': accel_details,
        'atr_zone_score': round(atr_zone_score, 1),
        'atr_pct': round(atr_pct, 2),
        'sentiment_score': round(sentiment_score, 1),
        'sentiment': sentiment
    }
    
    # ========================================================================
    # MODULE 4: RETARD RÉACTION (bonus)
    # ========================================================================
    
    lag_score, lag_details = detect_reaction_lag(symbol, week_str)
    details['lag_score'] = lag_score
    details['lag_details'] = lag_details
    
    # Bonus retard (max +10 points)
    if lag_score > 0:
        explosion_score = min(100, explosion_score + (lag_score * 0.1))
        details['explosion_score'] = round(explosion_score, 1)
    
    return explosion_score, details

# ============================================================================
# MODULE 6: STOP/TARGET 7-10 JOURS
# ============================================================================

def calculate_stop_target_7j(atr_pct):
    """
    Stop/Target adaptés 7-10 jours
    
    Stop   = 0.8 × ATR  (vs 1.0× stable)
    Target = 1.8 × ATR  (vs 2.6× stable)
    
    → Sortie rapide, rotation capital
    """
    stop_pct = EXPLOSION_CONFIG['stop_multiplier'] * atr_pct
    target_pct = EXPLOSION_CONFIG['target_multiplier'] * atr_pct
    
    # Stop minimum absolu
    stop_pct = max(stop_pct, 3.0)
    
    rr = round(target_pct / stop_pct, 2) if stop_pct > 0 else 0
    
    return {
        'stop_pct': round(stop_pct, 2),
        'target_pct': round(target_pct, 2),
        'risk_reward': rr
    }

# ============================================================================
# MODULE 8: PROBABILITÉ TOP5
# ============================================================================

def calculate_prob_top5(symbol):
    """
    Calcule probabilité historique d'apparition dans TOP 5
    
    prob_top5 = fréquence_top5 / 14_semaines
    
    Exemple: SAFC 3× top5 sur 14 semaines → 21%
    """
    # Récupérer historique 14 semaines
    history = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol},
        {'week': 1, 'variation_pct': 1}
    ).sort('week', -1).limit(14))
    
    if len(history) < 8:
        return 0, "Historique insuffisant"
    
    # Pour chaque semaine, trouver top 5
    top5_count = 0
    
    for h in history:
        week = h['week']
        
        # Trouver top 5 cette semaine
        top5 = list(db[COLLECTION_WEEKLY].find(
            {'week': week},
            {'symbol': 1, 'variation_pct': 1}
        ).sort('variation_pct', -1).limit(5))
        
        top5_symbols = [t['symbol'] for t in top5]
        
        if symbol in top5_symbols:
            top5_count += 1
    
    prob_top5 = (top5_count / len(history)) * 100
    
    return prob_top5, f"{top5_count}/{len(history)} semaines en TOP5"

# ============================================================================
# MODULE 9: RÉGIME MARCHÉ
# ============================================================================

def get_market_regime(week_str):
    """
    Détermine régime marché BRVM (haussier/baissier)
    
    Calcul: Moyenne variations toutes actions cette semaine
    
    Si moyenne > 1% → BULLISH
    Si moyenne < -1% → BEARISH
    Sinon → NEUTRAL
    """
    all_actions = list(db[COLLECTION_WEEKLY].find(
        {'week': week_str},
        {'variation_pct': 1}
    ))
    
    if not all_actions:
        return 'NEUTRAL', 1.0
    
    variations = [a.get('variation_pct', 0) for a in all_actions]
    avg_var = mean(variations)
    
    if avg_var > 1:
        regime = 'BULLISH'
        multiplier = EXPLOSION_CONFIG['market_bullish_multiplier']
    elif avg_var < -1:
        regime = 'BEARISH'
        multiplier = EXPLOSION_CONFIG['market_bearish_multiplier']
    else:
        regime = 'NEUTRAL'
        multiplier = 1.0
    
    return regime, multiplier

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def generate_explosion_7j(week_str=None):
    """
    Génère recommandations EXPLOSION 7-10 jours
    
    MAX 1-2 positions
    Score EXPLOSION ≥ 60
    """
    if not week_str:
        week_str = datetime.now().strftime("%Y-W%V")
    
    print("\n" + "="*80)
    print(f"DÉTECTION EXPLOSION 7-10 JOURS - {week_str}")
    print("="*80)
    print("\nOBJECTIF: Identifier actions TOP 5 hausses hebdo")
    print("HORIZON: 7-10 jours")
    print("POSITIONS: MAX 1-2")
    print("\n" + "="*80 + "\n")
    
    # Régime marché
    market_regime, market_multiplier = get_market_regime(week_str)
    print(f"Régime marché: {market_regime} (multiplier: {market_multiplier}x)")
    print("="*80 + "\n")
    
    # Tous les symboles
    symbols = db[COLLECTION_WEEKLY].distinct('symbol', {'week': week_str})
    
    print(f"Analyse de {len(symbols)} actions...\n")
    
    candidates = []
    
    for symbol in symbols:
        # Récupérer données
        weekly = db[COLLECTION_WEEKLY].find_one({
            'symbol': symbol,
            'week': week_str
        })
        
        if not weekly:
            continue
        
        # Filtres de base (moins stricts que WOS)
        atr_pct = weekly.get('atr_pct')
        if not atr_pct or atr_pct < 5 or atr_pct > 30:
            continue  # ATR hors zone
        
        rsi = weekly.get('rsi')
        if rsi and (rsi < 20 or rsi > 80):
            continue  # RSI extrême
        
        # ====================================================================
        # CALCUL EXPLOSION_SCORE
        # ====================================================================
        
        explosion_score, details = calculate_explosion_score(symbol, week_str)
        
        # Ajuster par régime marché
        explosion_score_adjusted = explosion_score * market_multiplier
        
        # Filtre score minimum
        if explosion_score_adjusted < EXPLOSION_CONFIG['explosion_min_score']:
            continue
        
        # ====================================================================
        # STOP/TARGET 7-10 JOURS
        # ====================================================================
        
        st = calculate_stop_target_7j(atr_pct)
        
        # ====================================================================
        # PROBABILITÉ TOP5
        # ====================================================================
        
        prob_top5, prob_details = calculate_prob_top5(symbol)
        
        # ====================================================================
        # CANDIDAT VALIDÉ
        # ====================================================================
        
        close = weekly.get('close', 0)
        
        candidate = {
            'symbol': symbol,
            'week': week_str,
            'signal': 'BUY_EXPLOSION_7J',
            
            # Scores
            'explosion_score': round(explosion_score_adjusted, 1),
            'explosion_score_raw': round(explosion_score, 1),
            'market_regime': market_regime,
            'market_multiplier': market_multiplier,
            
            # Détails explosion
            'breakout_score': details['breakout_score'],
            'breakout_details': details['breakout_details'],
            'volume_zscore': details['volume_zscore'],
            'volume_zscore_score': details['volume_zscore_score'],
            'acceleration': details['acceleration'],
            'acceleration_score': details['acceleration_score'],
            'lag_score': details['lag_score'],
            'sentiment': details['sentiment'],
            
            # Stop/Target
            'stop_pct': st['stop_pct'],
            'target_pct': st['target_pct'],
            'risk_reward': st['risk_reward'],
            
            # Probabilité
            'prob_top5': round(prob_top5, 1),
            'prob_details': prob_details,
            
            # Data
            'close': close,
            'atr_pct': atr_pct,
            'rsi': rsi,
            
            # Metadata
            'generated_at': datetime.now(),
            'horizon': '7-10 jours',
            'mode': 'EXPLOSION_7J'
        }
        
        candidates.append(candidate)
    
    # ========================================================================
    # TRI PAR EXPLOSION_SCORE DÉCROISSANT
    # ========================================================================
    
    candidates.sort(key=lambda x: x['explosion_score'], reverse=True)
    
    # ========================================================================
    # LIMITATION 1-2 POSITIONS
    # ========================================================================
    
    max_positions = EXPLOSION_CONFIG['max_positions']
    candidates = candidates[:max_positions]
    
    # ========================================================================
    # SAUVEGARDE MONGODB
    # ========================================================================
    
    db[COLLECTION_DECISIONS].delete_many({'week': week_str})
    
    if candidates:
        for rank, cand in enumerate(candidates, 1):
            cand['rank'] = rank
            db[COLLECTION_DECISIONS].insert_one(cand)
    
    # ========================================================================
    # AFFICHAGE
    # ========================================================================
    
    print("="*80)
    print(f"RECOMMANDATIONS EXPLOSION 7-10J - {week_str}")
    print("="*80)
    
    if not candidates:
        print("\n⚠️  Aucune opportunité détectée cette semaine")
        print("(Normal - Le système est sélectif pour court terme)\n")
        print("="*80 + "\n")
        return []
    
    for cand in candidates:
        print(f"\n{'='*80}")
        print(f"#{cand['rank']} - {cand['symbol']} - Score: {cand['explosion_score']:.1f}/100")
        print(f"{'='*80}")
        print(f"Prix: {cand['close']:.0f} FCFA")
        print(f"Stop: -{cand['stop_pct']:.1f}% | Target: +{cand['target_pct']:.1f}% | RR: {cand['risk_reward']}")
        print(f"Horizon: {cand['horizon']}")
        print(f"\nDÉTECTEURS:")
        print(f"  🔥 Breakout: {cand['breakout_score']}/100")
        print(f"     {cand['breakout_details']}")
        print(f"  📊 Volume Z-score: {cand['volume_zscore_score']}/100 (Z={cand['volume_zscore']})")
        print(f"  ⚡ Accélération: {cand['acceleration_score']}/100 ({cand['acceleration']:+.1f}%)")
        print(f"  🔄 Retard réaction: {cand['lag_score']}/100")
        print(f"  💬 Sentiment: {cand['sentiment']}")
        print(f"\nHISTORIQUE:")
        print(f"  📈 Probabilité TOP5: {cand['prob_top5']:.1f}% ({cand['prob_details']})")
        print(f"\nTECHNIQUE:")
        print(f"  ATR: {cand['atr_pct']:.1f}% | RSI: {cand['rsi'] or 'N/A'}")
    
    print(f"\n{'='*80}")
    print(f"✅ {len(candidates)} position(s) recommandée(s)")
    print(f"{'='*80}\n")
    
    print("⚠️  RAPPEL EXPLOSION 7-10 JOURS:")
    print("  - Horizon court: 7-10 jours MAX")
    print("  - Sortie rapide à target ou stop")
    print("  - Rotation capital fréquente")
    print("  - Risque > WOS_STABLE")
    print(f"  - Régime marché: {market_regime}")
    print("\n" + "="*80 + "\n")
    
    return candidates

# ============================================================================
# TRACK RECORD
# ============================================================================

def save_track_record(week_str, recommendations):
    """
    Sauvegarde recommandations pour track record
    """
    for reco in recommendations:
        track = {
            'week': week_str,
            'symbol': reco['symbol'],
            'entry_price': reco['close'],
            'stop_pct': reco['stop_pct'],
            'target_pct': reco['target_pct'],
            'explosion_score': reco['explosion_score'],
            'generated_at': datetime.now(),
            'status': 'OPEN',
            'result': None,
            'exit_price': None,
            'gain_pct': None,
            'closed_at': None
        }
        
        db[COLLECTION_TRACK_RECORD].insert_one(track)

def update_track_record(symbol, week_str, exit_price, result):
    """
    Met à jour track record avec résultat
    """
    track = db[COLLECTION_TRACK_RECORD].find_one({
        'symbol': symbol,
        'week': week_str,
        'status': 'OPEN'
    })
    
    if track:
        entry_price = track['entry_price']
        gain_pct = ((exit_price - entry_price) / entry_price) * 100
        
        db[COLLECTION_TRACK_RECORD].update_one(
            {'_id': track['_id']},
            {'$set': {
                'status': result,
                'exit_price': exit_price,
                'gain_pct': round(gain_pct, 2),
                'closed_at': datetime.now()
            }}
        )

def display_track_record():
    """
    Affiche track record complet
    """
    records = list(db[COLLECTION_TRACK_RECORD].find().sort('week', -1))
    
    if not records:
        print("Aucun track record disponible")
        return
    
    print("\n" + "="*80)
    print("TRACK RECORD EXPLOSION 7-10 JOURS")
    print("="*80)
    print(f"\n{'SEMAINE':<10} {'SYMBOL':<8} {'ENTRÉE':<8} {'SORTIE':<8} {'GAIN%':<8} {'STATUT':<10}")
    print("-"*80)
    
    total_trades = 0
    closed_trades = 0
    gains = []
    
    for r in records:
        week = r['week']
        symbol = r['symbol']
        entry = r['entry_price']
        exit_p = r.get('exit_price', 0)
        gain = r.get('gain_pct', 0)
        status = r['status']
        
        print(f"{week:<10} {symbol:<8} {entry:<8.0f} {exit_p:<8.0f} {gain:+7.1f}% {status:<10}")
        
        total_trades += 1
        if status in ['WIN', 'LOSS']:
            closed_trades += 1
            gains.append(gain)
    
    print("-"*80)
    
    if gains:
        avg_gain = mean(gains)
        win_count = len([g for g in gains if g > 0])
        winrate = (win_count / len(gains)) * 100
        cumul = sum(gains)
        
        print(f"\nSTATISTIQUES:")
        print(f"  Trades total: {total_trades}")
        print(f"  Trades clos: {closed_trades}")
        print(f"  Winrate: {winrate:.1f}%")
        print(f"  Gain moyen: {avg_gain:+.1f}%")
        print(f"  Cumul: {cumul:+.1f}%")
    
    print("\n" + "="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EXPLOSION 7-10 JOURS DETECTOR')
    parser.add_argument('--week', help='Semaine (YYYY-Www)')
    parser.add_argument('--track-record', action='store_true', help='Afficher track record')
    
    args = parser.parse_args()
    
    if args.track_record:
        display_track_record()
    else:
        recos = generate_explosion_7j(args.week)
        if recos:
            save_track_record(args.week or datetime.now().strftime("%Y-W%V"), recos)

if __name__ == "__main__":
    main()

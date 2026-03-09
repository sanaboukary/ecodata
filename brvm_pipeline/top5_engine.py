#!/usr/bin/env python3
"""
###############################################################################
# DEPRECATED — NE PAS UTILISER EN PRODUCTION
###############################################################################
# Ce fichier est la version MODULAIRE du TOP5 engine (formule Expected_Return
# + Volume_Acceleration + Semantic + WOS + Risk_Reward).
# Il a été remplacé par top5_engine_final.py (V2.5+) qui est la source de
# vérité unique pour toutes les recommandations en production.
#
# Différence critique avec top5_engine_final.py :
#   - Formule différente : 0.30 × Expected_Return vs 0.55 × MF_score
#   - Pas de stop ATR réel, pas de vol targeting, pas de circuit breaker
#   - Pas de filtre corrélation ni blacklist dynamique
#
# Ce fichier est conservé UNIQUEMENT pour la modularité Django (brvm_pipeline).
# Toute nouvelle fonctionnalité doit être ajoutée dans top5_engine_final.py.
###############################################################################

⭐ TOP5 ENGINE - STOCK PICKING HEBDOMADAIRE BRVM

OBJECTIF UNIQUE :
Être dans les 5 plus fortes hausses officielles de la semaine BRVM

FORMULE TOP5_SCORE :
= 0.30 × Expected_Return          (gain potentiel)
+ 0.25 × Volume_Acceleration      (liquidité soudaine)
+ 0.20 × Semantic_Score           (annonces/publications)
+ 0.15 × WOS_Setup                (setup technique)
+ 0.10 × Risk_Reward              (ratio risque/rendement)

👉 PRINCIPE : La surprise > la perfection
👉 OUTPUT : 5 actions BUY uniquement
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
import math
import warnings
warnings.warn(
    "brvm_pipeline/top5_engine.py (MODULAIRE LEGACY) — utiliser top5_engine_final.py en production.",
    DeprecationWarning, stacklevel=2
)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION
# ============================================================================

COLLECTION_WEEKLY = "prices_weekly"
COLLECTION_SEMANTIC = "AGREGATION_SEMANTIQUE_ACTION"
COLLECTION_TOP5 = "top5_weekly_brvm"

# Poids FINAUX (ajustables par auto-learning)
WEIGHTS = {
    'expected_return': 0.30,
    'volume_acceleration': 0.25,
    'semantic_score': 0.20,
    'wos_setup': 0.15,
    'risk_reward': 0.10
}

# ============================================================================
# COMPOSANTES DU SCORE
# ============================================================================

def calculate_expected_return(weekly_data, symbol):
    """
    Expected Return (0-100)
    
    Basé sur :
    - Momentum récent (3 semaines)
    - Breakout potentiel (SMA)
    - Volatilité contrôlée
    
    👉 Plus c'est haut, plus le gain potentiel est élevé
    """
    if not weekly_data or len(weekly_data) < 3:
        return 0
    
    score = 0
    
    # 1. Momentum 3 semaines (40 points)
    momentum_3w = 0
    for i in range(-3, 0):
        if i < -len(weekly_data):
            continue
        var = weekly_data[i].get('variation_pct', 0)
        momentum_3w += var
    
    # Normaliser : +15% en 3 semaines = 40 points
    score += min(40, (momentum_3w / 15) * 40)
    
    # 2. Position vs SMA (30 points)
    current_price = weekly_data[-1].get('close', 0)
    sma5 = weekly_data[-1].get('sma5')
    sma10 = weekly_data[-1].get('sma10')
    
    if current_price and sma5 and sma10:
        # Prix > SMA5 > SMA10 = max points
        if current_price > sma5 > sma10:
            score += 30
        elif current_price > sma5:
            score += 20
        elif current_price > sma10:
            score += 10
    
    # 3. Volatilité contrôlée (30 points)
    volatility = weekly_data[-1].get('volatility', 0)
    atr_pct = weekly_data[-1].get('atr_pct', 0)
    
    # Volatilité optimale : 10-20% (BRVM)
    if 10 <= volatility <= 20 and 8 <= atr_pct <= 25:
        score += 30
    elif volatility < 25:
        score += 15
    
    return min(100, max(0, score))

def calculate_volume_acceleration(weekly_data, symbol):
    """
    Volume Acceleration (0-100)
    
    👉 Détecte les ruptures de liquidité
    👉 Les plus fortes hausses BRVM viennent souvent avec volume soudain
    """
    if not weekly_data or len(weekly_data) < 2:
        return 0
    
    current_volume = weekly_data[-1].get('volume', 0)
    volume_ratio = weekly_data[-1].get('volume_ratio', 1)
    
    score = 0
    
    # 1. Ratio vs moyenne 8 semaines (60 points)
    # >2x = excellent, >1.5x = bon
    if volume_ratio > 2:
        score += 60
    elif volume_ratio > 1.5:
        score += 40
    elif volume_ratio > 1.2:
        score += 20
    
    # 2. Accélération sur 2 semaines (40 points)
    if len(weekly_data) >= 2:
        prev_volume = weekly_data[-2].get('volume', 1)
        if prev_volume > 0:
            accel = (current_volume / prev_volume - 1) * 100
            if accel > 50:
                score += 40
            elif accel > 25:
                score += 25
            elif accel > 10:
                score += 10
    
    return min(100, max(0, score))

def calculate_semantic_score(symbol, week_str):
    """
    Semantic Score (0-100)
    
    Basé sur les publications/annonces récentes :
    - Résultats financiers
    - Dividendes
    - Alertes
    - Sentiment général
    
    👉 Les plus fortes hausses BRVM suivent souvent des annonces
    """
    # Chercher analyse sémantique récente
    semantic = db[COLLECTION_SEMANTIC].find_one({
        'ticker': symbol,
        'semaine': week_str
    })
    
    if not semantic:
        return 50  # Neutre par défaut
    
    score = 50  # Base neutre
    
    # 1. Score publications (30 points)
    pub_score = semantic.get('score_publications', 0)
    score += (pub_score / 65) * 30  # Normaliser sur 65 max
    
    # 2. Score sentiment (40 points)
    sentiment_score = semantic.get('score_sentiment', 0)
    score += (sentiment_score / 40) * 40  # Normaliser sur 40 max
    
    # 3. Événements majeurs (30 points)
    events = semantic.get('evenements', [])
    if any('resultat' in e.lower() for e in events):
        score += 15
    if any('dividende' in e.lower() for e in events):
        score += 15
    
    return min(100, max(0, score))

def calculate_wos_setup(weekly_data, symbol):
    """
    WOS Setup - Week Of Success (0-100)
    
    Setup technique calibré BRVM :
    - RSI dans zone favorable (40-60)
    - Trend haussier (SMA)
    - Breakout potentiel
    - ATR normal (8-25%)
    
    👉 Pas la perfection, mais un setup solide
    """
    if not weekly_data:
        return 0
    
    current = weekly_data[-1]
    
    score = 0
    
    # 1. RSI favorable (30 points)
    rsi = current.get('rsi')
    if rsi:
        if 45 <= rsi <= 55:
            score += 30  # Zone neutre → potentiel hausse
        elif 40 <= rsi <= 60:
            score += 20
        elif rsi < 40:
            score += 10  # Oversold (peut rebondir)
    
    # 2. Trend (40 points)
    trend = current.get('trend', 'NEUTRAL')
    if trend == 'BULLISH':
        score += 40
    elif trend == 'NEUTRAL':
        score += 20
    
    # 3. ATR contrôlé (30 points)
    atr_signal = current.get('atr_signal', 'NORMAL')
    if atr_signal == 'NORMAL':
        score += 30
    elif atr_signal == 'LOW_VOLATILITY':
        score += 15  # Peut exploser
    
    return min(100, max(0, score))

def calculate_risk_reward(weekly_data, symbol):
    """
    Risk/Reward Ratio (0-100)
    
    Basé sur :
    - Distance au plus haut récent
    - Distance au plus bas récent
    - Volatilité contrôlée
    
    👉 Cherche l'asymétrie : risque limité, gain potentiel élevé
    """
    if not weekly_data or len(weekly_data) < 4:
        return 50  # Neutre
    
    current_price = weekly_data[-1].get('close', 0)
    
    # Plus haut/bas sur 4 semaines
    highs = [w.get('high', 0) for w in weekly_data[-4:]]
    lows = [w.get('low', 0) for w in weekly_data[-4:]]
    
    max_high = max(highs) if highs else current_price
    min_low = min(lows) if lows else current_price
    
    if current_price == 0:
        return 50
    
    # Distance au plus haut (potentiel hausse)
    upside = ((max_high - current_price) / current_price * 100) if current_price > 0 else 0
    
    # Distance au plus bas (risque baisse)
    downside = ((current_price - min_low) / current_price * 100) if current_price > 0 else 0
    
    # Ratio R/R
    rr_ratio = (upside / downside) if downside > 0 else 1
    
    # Score
    score = 50  # Base
    
    if rr_ratio > 2:     # Risque 1, Gain 2+
        score += 50
    elif rr_ratio > 1.5:
        score += 30
    elif rr_ratio > 1:
        score += 10
    
    return min(100, max(0, score))

# ============================================================================
# CALCUL TOP5 SCORE
# ============================================================================

def calculate_top5_score(symbol, week_str):
    """
    Calculer le TOP5_SCORE final
    
    Returns:
        dict: {
            'symbol': str,
            'week': str,
            'top5_score': float,
            'components': dict,
            'decision': 'BUY' | 'HOLD' | 'SELL'
        }
    """
    # Récupérer données weekly
    weekly_data = list(db[COLLECTION_WEEKLY].find({
        'symbol': symbol,
        'week': {'$lte': week_str}
    }).sort('week', 1))
    
    if not weekly_data or len(weekly_data) < 4:
        return None  # Pas assez d'historique
    
    # Calculer composantes
    er = calculate_expected_return(weekly_data, symbol)
    va = calculate_volume_acceleration(weekly_data, symbol)
    ss = calculate_semantic_score(symbol, week_str)
    wos = calculate_wos_setup(weekly_data, symbol)
    rr = calculate_risk_reward(weekly_data, symbol)
    
    # Score final
    top5_score = (
        WEIGHTS['expected_return'] * er +
        WEIGHTS['volume_acceleration'] * va +
        WEIGHTS['semantic_score'] * ss +
        WEIGHTS['wos_setup'] * wos +
        WEIGHTS['risk_reward'] * rr
    )
    
    # Décision
    decision = 'HOLD'
    if top5_score >= 70:
        decision = 'BUY'
    elif top5_score < 40:
        decision = 'SELL'
    
    return {
        'symbol': symbol,
        'week': week_str,
        'top5_score': round(top5_score, 2),
        'components': {
            'expected_return': round(er, 2),
            'volume_acceleration': round(va, 2),
            'semantic_score': round(ss, 2),
            'wos_setup': round(wos, 2),
            'risk_reward': round(rr, 2)
        },
        'weights': WEIGHTS,
        'decision': decision,
        'computed_at': datetime.now(),
        
        # Données de référence
        'current_price': weekly_data[-1].get('close'),
        'variation_pct': weekly_data[-1].get('variation_pct'),
        'volume': weekly_data[-1].get('volume'),
        'rsi': weekly_data[-1].get('rsi'),
        'trend': weekly_data[-1].get('trend'),
    }

# ============================================================================
# GÉNÉRATION TOP5
# ============================================================================

def generate_top5(week_str=None):
    """
    Générer le TOP5 de la semaine
    
    👉 Classer UNIQUEMENT les BUY
    👉 Trier par TOP5_SCORE décroissant
    👉 Afficher seulement 5
    """
    if not week_str:
        # Semaine en cours
        week_str = datetime.now().strftime("%Y-W%V")
    
    print("\n" + "="*80)
    print(f"⭐ GÉNÉRATION TOP5 - {week_str}")
    print("="*80 + "\n")
    
    # Tous les symboles avec données weekly
    symbols = db[COLLECTION_WEEKLY].distinct('symbol', {'week': week_str})
    
    print(f"📊 {len(symbols)} actions à analyser\n")
    
    all_scores = []
    
    for symbol in symbols:
        score_data = calculate_top5_score(symbol, week_str)
        if score_data:
            all_scores.append(score_data)
    
    # Filtrer : UNIQUEMENT les BUY
    buy_only = [s for s in all_scores if s['decision'] == 'BUY']
    
    print(f"✅ {len(buy_only)} actions en BUY")
    
    # Trier par TOP5_SCORE décroissant
    buy_only.sort(key=lambda x: x['top5_score'], reverse=True)
    
    # Prendre TOP 5
    top5 = buy_only[:5]
    
    # Sauvegarder
    db[COLLECTION_TOP5].delete_many({'week': week_str})  # Nettoyer ancienne version
    
    for rank, item in enumerate(top5, 1):
        item['rank'] = rank
        item['week'] = week_str
        db[COLLECTION_TOP5].insert_one(item)
    
    # Afficher
    print("\n" + "="*80)
    print(f"🏆 TOP 5 WEEKLY - {week_str}")
    print("="*80 + "\n")
    
    if not top5:
        print("❌ Aucune action en BUY cette semaine")
        return
    
    print(f"{'#':<3} {'TICKER':<8} {'SCORE':<8} {'ER':<6} {'VA':<6} {'SS':<6} {'WOS':<6} {'RR':<6} {'PRIX':<10} {'VAR%':<8}")
    print("-"*80)
    
    for item in top5:
        comp = item['components']
        print(
            f"{item['rank']:<3} "
            f"{item['symbol']:<8} "
            f"{item['top5_score']:<8.1f} "
            f"{comp['expected_return']:<6.1f} "
            f"{comp['volume_acceleration']:<6.1f} "
            f"{comp['semantic_score']:<6.1f} "
            f"{comp['wos_setup']:<6.1f} "
            f"{comp['risk_reward']:<6.1f} "
            f"{item.get('current_price', 0):<10.0f} "
            f"{item.get('variation_pct', 0):>+7.2f}%"
        )
    
    print("\n" + "="*80)
    print("✅ TOP5 sauvegardé dans MongoDB (collection: top5_weekly_brvm)")
    print("="*80 + "\n")
    
    return top5

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TOP5 Engine')
    parser.add_argument('--week', help='Semaine (YYYY-Www)')
    
    args = parser.parse_args()
    
    generate_top5(args.week)

if __name__ == "__main__":
    main()

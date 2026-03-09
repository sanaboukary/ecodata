#!/usr/bin/env python3
"""
🔴 OPPORTUNITY ENGINE - DÉTECTION PRÉCOCE BRVM

OBJECTIF : Détecter AVANT les autres (J+1 à J+7)
⚠️  Ne PAS confondre avec TOP5 Engine (performance publique hebdomadaire)

PRINCIPE :
Une opportunité n'est PAS toujours un bon trade.
Mais tous les grands trades commencent par une opportunité.

4 DÉTECTEURS :
1. NEWS SILENCIEUSE (marché n'a pas encore réagi)
2. VOLUME ANORMAL SANS PRIX (accumulation)
3. RUPTURE DE SOMMEIL (volatilité qui se réveille)
4. RETARD DE RÉACTION AU SECTEUR

FORMULE OPPORTUNITY_SCORE :
= 0.35 × Volume_Acceleration
+ 0.30 × Semantic_Impact
+ 0.20 × Volatility_Expansion
+ 0.15 × Sector_Momentum

SEUILS :
- ≥ 70 : OPPORTUNITÉ FORTE
- 55-70 : Observation
- < 55 : Ignorer
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import math

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

COLLECTION_DAILY = "prices_daily"
COLLECTION_WEEKLY = "prices_weekly"
COLLECTION_SEMANTIC = "AGREGATION_SEMANTIQUE_ACTION"
COLLECTION_OPPORTUNITIES = "opportunities_brvm"

# Poids OPPORTUNITY_SCORE
WEIGHTS = {
    'volume_acceleration': 0.35,
    'semantic_impact': 0.30,
    'volatility_expansion': 0.20,
    'sector_momentum': 0.15
}

# Seuils détection
THRESHOLDS = {
    'strong_opportunity': 70,    # ≥ 70 = FORTE
    'weak_opportunity': 55,      # 55-70 = Observation
    'volume_factor': 2.0,        # Volume × 2
    'volatility_factor': 1.8,    # ATR × 1.8
    'price_change_silent': 2.0,  # < +2% pour news silencieuse
    'sector_threshold': 15.0     # Secteur > +15%
}

# Secteurs BRVM
SECTORS = {
    'BANQUE': ['ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS', 'CABC', 'CBIBF', 'SGBC', 'SIBC', 'SLBC', 'SMBC'],
    'INDUSTRIE': ['NEIC', 'PALC', 'PRSC', 'SAFC', 'SCRC', 'SICC', 'SMBC', 'SNTS', 'SOGC', 'SPHC', 'TTLC', 'TTLS', 'UNLC', 'UNXC'],
    'DISTRIBUTION': ['CFAC', 'SDCC', 'SDSC', 'SHEC', 'SOGB', 'STAC', 'STBC'],
    'TRANSPORT': ['BOAN', 'ETIT', 'ORGT', 'SEMC', 'SIVC'],
    'SERVICES': ['CIEC', 'ECOC', 'FTSC', 'LNBB', 'NSBC', 'NTLC', 'ONTBF', 'ORAC']
}

# ============================================================================
# DÉTECTEUR 1 : NEWS SILENCIEUSE
# ============================================================================

def detect_silent_news(symbol, date=None):
    """
    DÉTECTEUR 1 - NEWS SILENCIEUSE
    
    Signal fort : Publication officielle AVANT réaction du prix
    
    Conditions :
    - semantic_score > 0 (news positive)
    - price_change < +2% (marché n'a pas réagi)
    - volume_today ≤ volume_avg (pas encore d'afflux)
    
    Returns:
        dict: {detected: bool, score: float, reason: str}
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 1. Récupérer données daily
    daily = db[COLLECTION_DAILY].find_one({'symbol': symbol, 'date': date})
    
    if not daily:
        return {'detected': False, 'score': 0, 'reason': 'No daily data'}
    
    # 2. Récupérer semantic score
    week = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-W%V")
    semantic = db[COLLECTION_SEMANTIC].find_one({'ticker': symbol, 'semaine': week})
    
    semantic_score = 0
    if semantic:
        pub_score = semantic.get('score_publications', 0)
        sentiment_score = semantic.get('score_sentiment', 0)
        semantic_score = pub_score + sentiment_score
    
    # 3. Variation prix du jour
    variation_pct = daily.get('variation_pct', 0)
    
    # 4. Volume vs moyenne
    # Calculer moyenne volume 20 jours
    prev_days = list(db[COLLECTION_DAILY].find({
        'symbol': symbol,
        'date': {'$lt': date}
    }).sort('date', -1).limit(20))
    
    if len(prev_days) < 5:
        return {'detected': False, 'score': 0, 'reason': 'Insufficient history'}
    
    avg_volume = sum(d.get('volume', 0) for d in prev_days) / len(prev_days)
    current_volume = daily.get('volume', 0)
    volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0
    
    # CONDITIONS DÉTECTION
    has_news = semantic_score > 0
    price_calm = abs(variation_pct) < THRESHOLDS['price_change_silent']
    volume_calm = volume_ratio <= 1.0
    
    detected = has_news and price_calm and volume_calm
    
    # Score (0-100)
    score = 0
    if detected:
        # Plus le semantic est fort ET le prix calme, meilleur c'est
        score += min(50, semantic_score)  # Max 50 pts pour news
        score += (THRESHOLDS['price_change_silent'] - abs(variation_pct)) / THRESHOLDS['price_change_silent'] * 30  # 30 pts max
        score += (1.0 - volume_ratio) * 20 if volume_ratio < 1.0 else 0  # 20 pts max
    
    return {
        'detected': detected,
        'score': round(score, 2),
        'reason': f"News:{semantic_score:.0f} Prix:{variation_pct:+.1f}% Vol:{volume_ratio:.2f}x" if detected else 'No signal',
        'semantic_score': semantic_score,
        'price_change': variation_pct,
        'volume_ratio': volume_ratio
    }

# ============================================================================
# DÉTECTEUR 2 : VOLUME ANORMAL SANS PRIX (ACCUMULATION)
# ============================================================================

def detect_volume_accumulation(symbol, date=None):
    """
    DÉTECTEUR 2 - VOLUME ANORMAL SANS PRIX
    
    Typique BRVM : Quelqu'un accumule, le prix viendra après
    
    Conditions :
    - volume_today ≥ 2 × volume_moyen_20j
    - variation_prix ∈ [-1%, +2%]
    
    Returns:
        dict: {detected: bool, score: float, reason: str}
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Données daily
    daily = db[COLLECTION_DAILY].find_one({'symbol': symbol, 'date': date})
    
    if not daily:
        return {'detected': False, 'score': 0, 'reason': 'No daily data'}
    
    # Historique volume
    prev_days = list(db[COLLECTION_DAILY].find({
        'symbol': symbol,
        'date': {'$lt': date}
    }).sort('date', -1).limit(20))
    
    if len(prev_days) < 10:
        return {'detected': False, 'score': 0, 'reason': 'Insufficient history'}
    
    avg_volume = sum(d.get('volume', 0) for d in prev_days) / len(prev_days)
    current_volume = daily.get('volume', 0)
    volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0
    
    variation_pct = daily.get('variation_pct', 0)
    
    # CONDITIONS
    volume_spike = volume_ratio >= THRESHOLDS['volume_factor']
    price_stable = -1.0 <= variation_pct <= 2.0
    
    detected = volume_spike and price_stable
    
    # Score (0-100)
    score = 0
    if detected:
        # Plus le volume est anormal ET le prix stable, meilleur
        volume_excess = volume_ratio - THRESHOLDS['volume_factor']
        score += min(60, volume_excess * 30)  # 60 pts max pour volume
        
        # Stabilité prix (idéal = 0%)
        price_stability = 1.0 - (abs(variation_pct) / 2.0)
        score += price_stability * 40  # 40 pts max
    
    return {
        'detected': detected,
        'score': round(score, 2),
        'reason': f"Vol:{volume_ratio:.1f}x Prix:{variation_pct:+.1f}%" if detected else 'No spike',
        'volume_ratio': volume_ratio,
        'price_change': variation_pct
    }

# ============================================================================
# DÉTECTEUR 3 : RUPTURE DE SOMMEIL (VOLATILITÉ SE RÉVEILLE)
# ============================================================================

def detect_volatility_awakening(symbol, date=None):
    """
    DÉTECTEUR 3 - RUPTURE DE SOMMEIL
    
    Action morte qui se réveille = souvent futur TOP5
    
    Conditions :
    - ATR%_7j > 1.8 × ATR%_30j
    - volume en hausse progressive
    
    Returns:
        dict: {detected: bool, score: float, reason: str}
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Historique 30 jours
    days = list(db[COLLECTION_DAILY].find({
        'symbol': symbol,
        'date': {'$lte': date}
    }).sort('date', -1).limit(30))
    
    if len(days) < 30:
        return {'detected': False, 'score': 0, 'reason': 'Insufficient history'}
    
    # Calculer ATR 7j
    atr_7d = calculate_atr_daily(days[:7])
    
    # Calculer ATR 30j
    atr_30d = calculate_atr_daily(days)
    
    if not atr_7d or not atr_30d or atr_30d == 0:
        return {'detected': False, 'score': 0, 'reason': 'Cannot calculate ATR'}
    
    atr_ratio = atr_7d / atr_30d
    
    # Volume progression (comparer 7j vs 30j)
    vol_7d = sum(d.get('volume', 0) for d in days[:7]) / 7
    vol_30d = sum(d.get('volume', 0) for d in days) / 30
    volume_trend = (vol_7d / vol_30d) if vol_30d > 0 else 1.0
    
    # CONDITIONS
    volatility_expanding = atr_ratio > THRESHOLDS['volatility_factor']
    volume_rising = volume_trend > 1.1  # +10% minimum
    
    detected = volatility_expanding and volume_rising
    
    # Score (0-100)
    score = 0
    if detected:
        # Plus l'expansion est forte, meilleur
        expansion_excess = atr_ratio - THRESHOLDS['volatility_factor']
        score += min(60, expansion_excess * 100)  # 60 pts max
        
        # Volume montant
        volume_boost = (volume_trend - 1.0) * 100
        score += min(40, volume_boost)  # 40 pts max
    
    return {
        'detected': detected,
        'score': round(score, 2),
        'reason': f"ATR:{atr_ratio:.2f}x Vol:{volume_trend:.2f}x" if detected else 'No awakening',
        'atr_ratio': round(atr_ratio, 2),
        'volume_trend': round(volume_trend, 2)
    }

def calculate_atr_daily(days):
    """Calculer ATR sur données daily"""
    if len(days) < 2:
        return None
    
    true_ranges = []
    for i in range(1, len(days)):
        high = days[i-1].get('high', 0)
        low = days[i-1].get('low', 0)
        prev_close = days[i].get('close', 0)
        
        if not all([high, low, prev_close]):
            continue
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if not true_ranges:
        return None
    
    atr = sum(true_ranges) / len(true_ranges)
    
    # Normaliser en % du prix actuel
    current_price = days[0].get('close', 0)
    if current_price == 0:
        return None
    
    return (atr / current_price) * 100

# ============================================================================
# DÉTECTEUR 4 : RETARD DE RÉACTION AU SECTEUR
# ============================================================================

def detect_sector_lag(symbol, date=None):
    """
    DÉTECTEUR 4 - RETARD SECTEUR
    
    Secteur entier monte, une action n'a pas suivi = rattrapage à venir
    
    Conditions :
    - sector_score > +15%
    - action_score < sector_avg
    - volume commence à monter
    
    Returns:
        dict: {detected: bool, score: float, reason: str}
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Trouver secteur de l'action
    sector_name = None
    for name, symbols in SECTORS.items():
        if symbol in symbols:
            sector_name = name
            break
    
    if not sector_name:
        return {'detected': False, 'score': 0, 'reason': 'Sector unknown'}
    
    # Performance secteur (moyenne 5 jours)
    sector_symbols = SECTORS[sector_name]
    
    sector_performances = []
    for sym in sector_symbols:
        days = list(db[COLLECTION_DAILY].find({
            'symbol': sym,
            'date': {'$lte': date}
        }).sort('date', -1).limit(5))
        
        if len(days) >= 5:
            perf_5d = sum(d.get('variation_pct', 0) for d in days)
            sector_performances.append(perf_5d)
    
    if len(sector_performances) < 3:
        return {'detected': False, 'score': 0, 'reason': 'Insufficient sector data'}
    
    avg_sector_perf = sum(sector_performances) / len(sector_performances)
    
    # Performance de l'action
    action_days = list(db[COLLECTION_DAILY].find({
        'symbol': symbol,
        'date': {'$lte': date}
    }).sort('date', -1).limit(5))
    
    if len(action_days) < 5:
        return {'detected': False, 'score': 0, 'reason': 'Insufficient action data'}
    
    action_perf_5d = sum(d.get('variation_pct', 0) for d in action_days)
    
    # Volume montant ?
    vol_current = action_days[0].get('volume', 0)
    vol_avg = sum(d.get('volume', 0) for d in action_days) / len(action_days)
    volume_rising = (vol_current / vol_avg) > 1.0 if vol_avg > 0 else False
    
    # CONDITIONS
    sector_strong = avg_sector_perf > THRESHOLDS['sector_threshold']
    action_lagging = action_perf_5d < avg_sector_perf
    
    detected = sector_strong and action_lagging and volume_rising
    
    # Score (0-100)
    score = 0
    if detected:
        # Gap à rattraper
        gap = avg_sector_perf - action_perf_5d
        score += min(60, gap * 2)  # 60 pts max
        
        # Force du secteur
        sector_strength = (avg_sector_perf - THRESHOLDS['sector_threshold']) / THRESHOLDS['sector_threshold'] * 100
        score += min(40, sector_strength)  # 40 pts max
    
    return {
        'detected': detected,
        'score': round(score, 2),
        'reason': f"Secteur:{avg_sector_perf:+.1f}% Action:{action_perf_5d:+.1f}%" if detected else 'No lag',
        'sector_name': sector_name,
        'sector_perf': round(avg_sector_perf, 2),
        'action_perf': round(action_perf_5d, 2),
        'gap': round(avg_sector_perf - action_perf_5d, 2)
    }

# ============================================================================
# CALCUL OPPORTUNITY_SCORE
# ============================================================================

def calculate_opportunity_score(symbol, date=None):
    """
    Calculer OPPORTUNITY_SCORE final
    
    = 0.35 × Volume_Acceleration
    + 0.30 × Semantic_Impact
    + 0.20 × Volatility_Expansion
    + 0.15 × Sector_Momentum
    
    Returns:
        dict: {
            'symbol': str,
            'date': str,
            'opportunity_score': float,
            'level': 'FORTE' | 'OBSERVATION' | 'NONE',
            'detectors': dict,
            'components': dict
        }
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Exécuter les 4 détecteurs
    news = detect_silent_news(symbol, date)
    volume = detect_volume_accumulation(symbol, date)
    volatility = detect_volatility_awakening(symbol, date)
    sector = detect_sector_lag(symbol, date)
    
    # Composantes du score
    components = {
        'volume_acceleration': volume['score'],
        'semantic_impact': news['score'],
        'volatility_expansion': volatility['score'],
        'sector_momentum': sector['score']
    }
    
    # Score final
    opportunity_score = (
        WEIGHTS['volume_acceleration'] * components['volume_acceleration'] +
        WEIGHTS['semantic_impact'] * components['semantic_impact'] +
        WEIGHTS['volatility_expansion'] * components['volatility_expansion'] +
        WEIGHTS['sector_momentum'] * components['sector_momentum']
    )
    
    # Niveau
    if opportunity_score >= THRESHOLDS['strong_opportunity']:
        level = 'FORTE'
    elif opportunity_score >= THRESHOLDS['weak_opportunity']:
        level = 'OBSERVATION'
    else:
        level = 'NONE'
    
    # Prix actuel
    daily = db[COLLECTION_DAILY].find_one({'symbol': symbol, 'date': date})
    current_price = daily.get('close', 0) if daily else 0
    
    return {
        'symbol': symbol,
        'date': date,
        'opportunity_score': round(opportunity_score, 2),
        'level': level,
        'components': components,
        'detectors': {
            'news_silent': news,
            'volume_accumulation': volume,
            'volatility_awakening': volatility,
            'sector_lag': sector
        },
        'current_price': current_price,
        'computed_at': datetime.now()
    }

# ============================================================================
# SCAN TOUTES LES ACTIONS
# ============================================================================

def scan_all_opportunities(date=None, min_level='OBSERVATION'):
    """
    Scanner toutes les actions pour détecter opportunités
    
    Args:
        date: Date à analyser (défaut: hier)
        min_level: 'FORTE' | 'OBSERVATION' | 'NONE'
    
    Returns:
        list of dict: Opportunités détectées triées par score
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n🔍 SCAN OPPORTUNITÉS - {date}")
    print("="*80 + "\n")
    
    # Tous les symboles avec données daily
    symbols = db[COLLECTION_DAILY].distinct('symbol', {'date': date})
    
    print(f"Analyse de {len(symbols)} actions...\n")
    
    opportunities = []
    
    for symbol in symbols:
        result = calculate_opportunity_score(symbol, date)
        
        # Filtrer par niveau minimum
        if min_level == 'FORTE' and result['level'] != 'FORTE':
            continue
        elif min_level == 'OBSERVATION' and result['level'] == 'NONE':
            continue
        
        if result['level'] != 'NONE':
            opportunities.append(result)
            
            # Sauvegarder dans MongoDB
            db[COLLECTION_OPPORTUNITIES].update_one(
                {'symbol': symbol, 'date': date},
                {'$set': result},
                upsert=True
            )
    
    # Trier par score décroissant
    opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
    
    return opportunities

# ============================================================================
# AFFICHAGE
# ============================================================================

def display_opportunities(opportunities):
    """Afficher les opportunités détectées"""
    if not opportunities:
        print("❌ Aucune opportunité détectée\n")
        return
    
    print(f"✅ {len(opportunities)} OPPORTUNITÉS DÉTECTÉES\n")
    print("="*80)
    
    print(f"{'TICKER':<8} {'SCORE':<8} {'NIVEAU':<15} {'PRIX':<10} {'DÉTECTEURS':<40}")
    print("-"*80)
    
    for opp in opportunities:
        # Compter détecteurs actifs
        detectors_active = []
        if opp['detectors']['news_silent']['detected']:
            detectors_active.append('News')
        if opp['detectors']['volume_accumulation']['detected']:
            detectors_active.append('Vol')
        if opp['detectors']['volatility_awakening']['detected']:
            detectors_active.append('Volat')
        if opp['detectors']['sector_lag']['detected']:
            detectors_active.append('Sect')
        
        detectors_str = '+'.join(detectors_active) if detectors_active else '-'
        
        print(
            f"{opp['symbol']:<8} "
            f"{opp['opportunity_score']:<8.1f} "
            f"{opp['level']:<15} "
            f"{opp['current_price']:<10.0f} "
            f"{detectors_str:<40}"
        )
    
    print("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Opportunity Engine - Détection précoce BRVM')
    parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    parser.add_argument('--symbol', help='Analyser un symbole spécifique')
    parser.add_argument('--level', choices=['FORTE', 'OBSERVATION', 'NONE'], default='OBSERVATION',
                       help='Niveau minimum')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔴 OPPORTUNITY ENGINE - DÉTECTION PRÉCOCE")
    print("="*80)
    print("Horizon : J+1 à J+7 | Objectif : Détecter AVANT les autres")
    print("="*80 + "\n")
    
    if args.symbol:
        # Analyser symbole spécifique
        result = calculate_opportunity_score(args.symbol, args.date)
        
        print(f"\n📊 ANALYSE : {result['symbol']} - {result['date']}\n")
        print(f"OPPORTUNITY_SCORE : {result['opportunity_score']:.1f} ({result['level']})")
        print(f"Prix actuel       : {result['current_price']:.0f}")
        print()
        
        print("COMPOSANTES :")
        for key, val in result['components'].items():
            print(f"  • {key:<25} : {val:>6.1f}")
        
        print("\nDÉTECTEURS :")
        for key, detector in result['detectors'].items():
            status = "✅" if detector['detected'] else "  "
            print(f"  {status} {key:<25} : {detector['reason']}")
        
        print()
    
    else:
        # Scanner toutes les actions
        opportunities = scan_all_opportunities(args.date, args.level)
        display_opportunities(opportunities)
        
        # Stats
        forte_count = sum(1 for o in opportunities if o['level'] == 'FORTE')
        obs_count = sum(1 for o in opportunities if o['level'] == 'OBSERVATION')
        
        print(f"📊 Résumé :")
        print(f"   FORTE       : {forte_count}")
        print(f"   OBSERVATION : {obs_count}")
        print(f"   Total       : {len(opportunities)}")
        print()

if __name__ == "__main__":
    main()

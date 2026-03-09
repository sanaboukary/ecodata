#!/usr/bin/env python3
"""
🔵 PIPELINE WEEKLY - NIVEAU 3 (DÉCISIONNEL)

PRINCIPE :
- Agrégation DAILY → WEEKLY
- Calcul des indicateurs techniques calibrés BRVM :
  * RSI(14) avec oversold=40, overbought=65
  * ATR% normalisé (8-25%)
  * SMA 5/10 semaines
  * Volume ratio (moyenne 8 semaines)
  * Volatilité hebdomadaire (12 semaines)

📊 SEULE BASE DE DÉCISION pour le TOP5

EXÉCUTION :
- Chaque lundi matin (nouvelle semaine)
- OU manuellement pour rattrapage
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
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
SOURCE = "WEEKLY_AGGREGATION"

# ⚠️ MODE DÉMARRAGE : Config adaptée pour historique limité (<14 semaines)
# TODO: Basculer vers config PRODUCTION une fois 14+ semaines disponibles
MODE_STARTUP = False  # ← Passé en PRODUCTION - 72 jours disponibles (14+ semaines)

if MODE_STARTUP:
    # Configuration démarrage (5-8 semaines)
    RSI_PERIOD = 5
    ATR_PERIOD = 5
    SMA_FAST = 3
    SMA_SLOW = 5
    VOLUME_PERIOD = 5
    VOLATILITY_PERIOD = 5
    MIN_WEEKS_REQUIRED = 5
    print("ATTENTION MODE DEMARRAGE - Indicateurs adaptes historique limite")
else:
    # Configuration PRODUCTION (calibrée BRVM)
    RSI_PERIOD = 14
    ATR_PERIOD = 8
    SMA_FAST = 5
    SMA_SLOW = 10
    VOLUME_PERIOD = 8
    VOLATILITY_PERIOD = 12
    MIN_WEEKS_REQUIRED = 14
    print("OK MODE PRODUCTION - Calibration BRVM complete")

# Calibration BRVM (constantes)
RSI_OVERSOLD = 40    # Pas 30 !
RSI_OVERBOUGHT = 65  # Pas 70 !

# 🔥 CALIBRATION ATR BRVM PRO (réalités marché africain)
ATR_PERIOD_BRVM = 5  # Sweet spot (14=trop lent, 3=trop instable)
ATR_DEAD_MARKET = 4  # < 4% = marché mort
ATR_SLOW = 8         # 4-8% = lent
ATR_IDEAL_MIN = 8    # 8-18% = zone idéale
ATR_IDEAL_MAX = 18   
ATR_SPECULATIVE = 28 # 18-28% = spéculatif
ATR_DANGEROUS = 28   # > 28% = dangereux

# Filtres WEEKLY (avant BUY)
ATR_MIN_TRADE = 6    # Rejeter si < 6% (pas assez d'amplitude)
ATR_MAX_TRADE = 25   # Rejeter si > 25% (volatilité excessive)

# Stops/Targets (RR institutionnel)
STOP_MULTIPLIER = 1.0   # stop = 1.0 × ATR%
TARGET_MULTIPLIER = 2.6 # target = 2.6 × ATR% → RR=2.6
MIN_STOP_PCT = 4.0      # Stop minimum absolu

# ============================================================================
# UTILITAIRES
# ============================================================================

def get_week_number(date_str):
    """Convertir date YYYY-MM-DD en semaine ISO YYYY-Www"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%Y-W%V")

def get_week_days(week_str):
    """Retourner toutes les dates d'une semaine ISO"""
    year, week = week_str.split('-W')
    year = int(year)
    week = int(week)
    
    # Premier lundi de l'année
    jan1 = datetime(year, 1, 1)
    days_to_monday = (7 - jan1.weekday()) % 7
    if days_to_monday == 0 and jan1.weekday() != 0:
        days_to_monday = 7
    first_monday = jan1 + timedelta(days=days_to_monday)
    
    week_start = first_monday + timedelta(weeks=week-1)
    
    # Tous les jours de la semaine
    return [(week_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

# ============================================================================
# AGRÉGATION DAILY → WEEKLY
# ============================================================================

def aggregate_week(week_str, symbol=None):
    """
    Agréger les données DAILY d'une semaine en 1 ligne WEEKLY
    
    Args:
        week_str: Format "YYYY-Www" (ex: "2026-W06")
        symbol: Si None, traite tous les symboles
    
    Returns:
        int: Nombre de weekly créés
    """
    # Trouver toutes les dates de la semaine
    week_dates = get_week_days(week_str)
    
    query = {'date': {'$in': week_dates}}
    if symbol:
        query['symbol'] = symbol
    
    daily_data = list(db[COLLECTION_DAILY].find(query).sort('date', 1))
    
    if not daily_data:
        print(f"⚠️  Aucune donnée DAILY pour {week_str}" + (f" ({symbol})" if symbol else ""))
        return 0
    
    # Grouper par symbole
    from collections import defaultdict
    by_symbol = defaultdict(list)
    for doc in daily_data:
        by_symbol[doc['symbol']].append(doc)
    
    print(f"\n📅 Agrégation WEEKLY : {week_str}")
    print(f"   {len(by_symbol)} symboles à traiter")
    
    created = 0
    updated = 0
    
    for sym, days in by_symbol.items():
        # Trier par date
        days.sort(key=lambda x: x['date'])
        
        # Extraire prix
        opens = [d['open'] for d in days if d.get('open')]
        highs = [d['high'] for d in days if d.get('high')]
        lows = [d['low'] for d in days if d.get('low')]
        closes = [d['close'] for d in days if d.get('close')]
        volumes = [d['volume'] for d in days if d.get('volume')]
        
        if not (opens and highs and lows and closes):
            continue
        
        # Agrégation WEEKLY
        open_price = opens[0]              # Open du lundi
        high_price = max(highs)            # High de la semaine
        low_price = min(lows)              # Low de la semaine
        close_price = closes[-1]           # Close du vendredi
        volume = sum(volumes)              # Volume cumulé
        
        # Variation % hebdomadaire
        variation_pct = ((close_price - open_price) / open_price * 100) if open_price > 0 else 0
        
        # Document WEEKLY
        weekly_doc = {
            'symbol': sym,
            'week': week_str,
            'week_start': days[0]['date'],
            'week_end': days[-1]['date'],
            'source': SOURCE,
            'updated_at': datetime.now(),
            
            # OHLC hebdomadaire
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'variation_pct': variation_pct,
            
            # Métadonnées
            'nb_days': len(days),
            'dates': [d['date'] for d in days],
            
            # FLAGS
            'level': 'WEEKLY',
            'is_complete': len(days) >= 4,  # Au moins 4 jours de marché
            'indicators_computed': False    # Sera mis à True après calcul
        }
        
        # Upsert
        result = db[COLLECTION_WEEKLY].update_one(
            {'symbol': sym, 'week': week_str},
            {'$set': weekly_doc},
            upsert=True
        )
        
        if result.upserted_id:
            created += 1
        else:
            updated += 1
        
        # Marquer DAILY comme utilisé
        db[COLLECTION_DAILY].update_many(
            {'symbol': sym, 'date': {'$in': [d['date'] for d in days]}},
            {'$set': {'used_for_weekly': True}}
        )
    
    print(f"   ✅ Créés : {created}")
    print(f"   🔄 Mis à jour : {updated}")
    
    return created + updated

# ============================================================================
# INDICATEURS TECHNIQUES (CALIBRÉS BRVM)
# ============================================================================

def calculate_rsi(prices, period=14):
    """
    RSI calibré BRVM
    Oversold = 40 (pas 30)
    Overbought = 65 (pas 70)
    """
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def is_dead_week(week_data):
    """
    🔥 BRVM PRO v2: Détecter semaines VRAIMENT mortes
    RÉALITÉ BRVM: Volume=0 pendant plusieurs semaines = NORMAL (faible liquidité)
    Ne filtrer QUE si prix complètement bloqué
    """
    high = week_data.get('high', 0)
    low = week_data.get('low', 0)
    close = week_data.get('close', 0)
    
    # Données manquantes
    if high == 0 or low == 0 or close == 0:
        return True
    
    # Prix complètement bloqué (high == low == close)
    if high == low == close:
        return True
    
    # Variation EXTRÊMEMENT faible (< 0.05% - tolérance augmentée pour BRVM)
    open_price = week_data.get('open', close)
    if open_price > 0:
        variation_pct = abs((close - open_price) / open_price * 100)
        if variation_pct < 0.05:  # Réduit de 0.1% à 0.05%
            return True
    
    # ACCEPTER volume=0 si prix bouge (normal BRVM)
    return False

def calculate_atr_pct(weekly_data, period=5):
    """
    🔥 ATR BRVM PRO - Calibration définitive
    
    Différences vs académique:
    - Basé sur WEEKLY (marché lent)
    - Filtre semaines mortes (volume=0, prix bloqués)
    - 5 semaines (sweet spot BRVM)
    - Seuils réalistes: 6-25%
    
    Si ATR cassé → stop cassé → RR cassé → agent ment
    """
    if len(weekly_data) < period + 1:  # +1 pour prev_close
        return None
    
    # 🔥 ÉTAPE 1: Filtrer semaines mortes
    active_weeks = [w for w in weekly_data if not is_dead_week(w)]
    
    # 🔥 FALLBACK ADAPTATIF BRVM: Si pas assez de semaines actives, utiliser TOUTES
    min_weeks_needed = period + 1
    if len(active_weeks) < min_weeks_needed:
        # Marché très illiquide - utiliser toutes semaines disponibles
        if len(weekly_data) >= 4:  # Minimum absolu: 4 semaines
            active_weeks = weekly_data
        else:
            return None  # Vraiment pas assez de données
    
    # 🔥 ÉTAPE 2: Calculer True Range sur semaines actives
    true_ranges = []
    for i in range(1, len(active_weeks)):
        high = active_weeks[i].get('high', 0)
        low = active_weeks[i].get('low', 0)
        prev_close = active_weeks[i-1].get('close', 0)
        
        # True Range (formule correcte)
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    # 🔥 ÉTAPE 3: ATR = moyenne des 5 derniers TR
    atr_5w = sum(true_ranges[-period:]) / period
    
    # 🔥 ÉTAPE 4: Normaliser en % (ATR% = ATR / prix actuel)
    current_price = active_weeks[-1].get('close', 0)
    
    if current_price <= 0:
        return None
    
    atr_pct = (atr_5w / current_price) * 100
    
    # 🔥 ÉTAPE 5: Plafonner outliers (si > 40% = calcul cassé)
    if atr_pct > 40:
        return None  # Donnée aberrante, rejeter
    
    return round(atr_pct, 2)

def calculate_sma(prices, period):
    """SMA simple"""
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)

def calculate_volatility(weekly_data, period=12):
    """Volatilité hebdomadaire normalisée sur 12 semaines"""
    if len(weekly_data) < period:
        return None
    
    returns = []
    for i in range(1, len(weekly_data)):
        ret = (weekly_data[i]['close'] - weekly_data[i-1]['close']) / weekly_data[i-1]['close']
        returns.append(ret)
    
    # Écart-type
    mean_return = sum(returns[-period:]) / period
    variance = sum((r - mean_return) ** 2 for r in returns[-period:]) / period
    volatility = math.sqrt(variance)
    
    return round(volatility * 100, 2)  # En %

def compute_indicators(symbol, week_str):
    """
    Calculer tous les indicateurs techniques pour un symbole à une semaine donnée
    Calibration BRVM appliquée
    """
    # Récupérer historique WEEKLY
    weekly_history = list(db[COLLECTION_WEEKLY].find({
        'symbol': symbol,
        'week': {'$lte': week_str}
    }).sort('week', 1))
    
    if len(weekly_history) < MIN_WEEKS_REQUIRED:
        return None  # Pas assez d'historique
    
    # Extraire closes
    closes = [w['close'] for w in weekly_history if w.get('close')]
    
    if len(closes) < MIN_WEEKS_REQUIRED:
        return None
    
    # RSI (14 semaines, calibré BRVM)
    rsi = calculate_rsi(closes, RSI_PERIOD)
    
    # 🔥 ATR% BRVM PRO (5 semaines, filtré)
    atr_pct = calculate_atr_pct(weekly_history, ATR_PERIOD_BRVM)
    
    # SMA 5 et 10 semaines
    sma5 = calculate_sma(closes, SMA_FAST)
    sma10 = calculate_sma(closes, SMA_SLOW)
    
    # Volatilité (12 semaines)
    volatility = calculate_volatility(weekly_history, VOLATILITY_PERIOD)
    
    # Volume ratio (moyenne 8 semaines)
    volumes = [w['volume'] for w in weekly_history[-VOLUME_PERIOD:] if w.get('volume')]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    current_volume = weekly_history[-1].get('volume', 0)
    volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0
    
    # Signal RSI (calibré BRVM)
    rsi_signal = 'NEUTRAL'
    if rsi and rsi < RSI_OVERSOLD:
        rsi_signal = 'OVERSOLD'
    elif rsi and rsi > RSI_OVERBOUGHT:
        rsi_signal = 'OVERBOUGHT'
    
    # 🔥 Signal ATR BRVM PRO (seuils réalistes)
    atr_signal = 'NORMAL'
    tradable = True  # Flag pour filtres BUY
    
    if atr_pct:
        if atr_pct < ATR_DEAD_MARKET:
            atr_signal = 'DEAD_MARKET'
            tradable = False
        elif atr_pct < ATR_SLOW:
            atr_signal = 'SLOW'
            tradable = (atr_pct >= ATR_MIN_TRADE)  # Seuil 6%
        elif atr_pct <= ATR_IDEAL_MAX:
            atr_signal = 'IDEAL'
            tradable = True
        elif atr_pct <= ATR_SPECULATIVE:
            atr_signal = 'SPECULATIVE'
            tradable = (atr_pct <= ATR_MAX_TRADE)  # Seuil 25%
        else:
            atr_signal = 'DANGEROUS'
            tradable = False
    else:
        tradable = False  # ATR invalide
    
    # 🔥 Calcul STOP/TARGET institutionnel
    stop_pct = None
    target_pct = None
    risk_reward = None
    
    if atr_pct and tradable:
        stop_pct = max(STOP_MULTIPLIER * atr_pct, MIN_STOP_PCT)
        target_pct = TARGET_MULTIPLIER * atr_pct
        risk_reward = round(target_pct / stop_pct, 2) if stop_pct > 0 else None
    
    # Trend (SMA)
    trend = 'NEUTRAL'
    if sma5 and sma10:
        if sma5 > sma10 * 1.02:
            trend = 'BULLISH'
        elif sma5 < sma10 * 0.98:
            trend = 'BEARISH'
    
    indicators = {
        'rsi': rsi,
        'rsi_signal': rsi_signal,
        'atr_pct': atr_pct,
        'atr_signal': atr_signal,
        'tradable': tradable,  # 🔥 Filtre BRVM (6-25%)
        'stop_pct': stop_pct,
        'target_pct': target_pct,
        'risk_reward': risk_reward,
        'sma5': sma5,
        'sma10': sma10,
        'trend': trend,
        'volatility': volatility,
        'volume_ratio': round(volume_ratio, 2),
        'indicators_computed': True,
        'computed_at': datetime.now()
    }
    
    return indicators

def compute_all_indicators(week_str=None):
    """Calculer indicateurs pour toutes les actions d'une semaine"""
    if not week_str:
        # Dernière semaine
        last = db[COLLECTION_WEEKLY].find_one(sort=[('week', -1)])
        week_str = last['week'] if last else None
    
    if not week_str:
        print("❌ Aucune semaine trouvée")
        return
    
    print(f"\n📊 Calcul indicateurs : {week_str}")
    
    symbols = db[COLLECTION_WEEKLY].distinct('symbol', {'week': week_str})
    
    computed = 0
    skipped = 0
    
    for symbol in symbols:
        indicators = compute_indicators(symbol, week_str)
        
        if indicators:
            db[COLLECTION_WEEKLY].update_one(
                {'symbol': symbol, 'week': week_str},
                {'$set': indicators}
            )
            computed += 1
        else:
            skipped += 1
    
    print(f"   ✅ Calculés : {computed}")
    print(f"   ⏭️  Skippés : {skipped} (historique insuffisant)")

# ============================================================================
# RECONSTRUCTION
# ============================================================================

def rebuild_all_weekly():
    """Reconstruire toutes les semaines depuis DAILY"""
    print("\n" + "="*80)
    print("🔄 RECONSTRUCTION COMPLÈTE WEEKLY")
    print("="*80 + "\n")
    
    # Trouver toutes les dates daily
    all_dates = sorted(db[COLLECTION_DAILY].distinct('date'))
    
    if not all_dates:
        print("❌ Aucune date DAILY")
        return
    
    # Convertir en semaines uniques
    weeks = sorted(set(get_week_number(d) for d in all_dates))
    
    print(f"📅 Semaines à traiter : {len(weeks)}")
    print(f"   De : {weeks[0]}")
    print(f"   À  : {weeks[-1]}")
    print()
    
    # Agréger
    total = 0
    for i, week in enumerate(weeks, 1):
        print(f"[{i}/{len(weeks)}] {week}", end=" ")
        count = aggregate_week(week)
        total += count
    
    print("\n\n📊 Calcul des indicateurs techniques...")
    
    # Calculer indicateurs pour chaque semaine
    for week in weeks:
        compute_all_indicators(week)
    
    print("\n" + "="*80)
    print(f"✅ TOTAL WEEKLY : {total}")
    print("="*80 + "\n")

# ============================================================================
# STATS
# ============================================================================

def show_weekly_stats():
    """Stats WEEKLY"""
    total = db[COLLECTION_WEEKLY].count_documents({})
    
    weeks = sorted(db[COLLECTION_WEEKLY].distinct('week'))
    first_week = weeks[0] if weeks else 'N/A'
    last_week = weeks[-1] if weeks else 'N/A'
    
    symbols = len(db[COLLECTION_WEEKLY].distinct('symbol'))
    
    with_indicators = db[COLLECTION_WEEKLY].count_documents({'indicators_computed': True})
    ind_pct = (with_indicators / total * 100) if total > 0 else 0
    
    print("\n" + "="*80)
    print("📊 STATS COLLECTION WEEKLY (prices_weekly)")
    print("="*80)
    print(f"Total semaines × symboles : {total:,}")
    print(f"Période                   : {first_week} → {last_week} ({len(weeks)} semaines)")
    print(f"Symboles uniques          : {symbols}")
    print(f"Indicateurs calculés      : {with_indicators:,} / {total:,} ({ind_pct:.1f}%)")
    print("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline WEEKLY - Niveau 3')
    parser.add_argument('--week', help='Semaine spécifique (YYYY-Www)')
    parser.add_argument('--rebuild', action='store_true', help='Reconstruire tout')
    parser.add_argument('--indicators', action='store_true', help='Calculer indicateurs uniquement')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔵 PIPELINE WEEKLY - NIVEAU 3 (DÉCISIONNEL)")
    print("="*80)
    print("📊 Calibration BRVM : RSI(40-65), ATR%(8-25), SMA(5/10)")
    print("="*80 + "\n")
    
    if args.rebuild:
        rebuild_all_weekly()
    elif args.indicators:
        compute_all_indicators(args.week)
    elif args.week:
        aggregate_week(args.week)
        compute_all_indicators(args.week)
    else:
        # Par défaut : semaine dernière (complète)
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-W%V")
        print(f"📅 Semaine par défaut : {last_week}")
        aggregate_week(last_week)
        compute_all_indicators(last_week)
    
    show_weekly_stats()
    
    print("✅ Pipeline WEEKLY terminé\n")

if __name__ == "__main__":
    main()

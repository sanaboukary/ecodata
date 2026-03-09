#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE A - RECALIBRATION ATR BRVM DÉFINITIVE
============================================
Passer en MODE PRODUCTION avec calibration BRVM officielle
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ETAPE A - RECALIBRATION ATR BRVM PRODUCTION")
print("="*80 + "\n")

# CONFIGURATION MODE PRODUCTION
CONFIG_PRODUCTION = {
    'MODE': 'PRODUCTION',
    'RSI_PERIOD': 14,      # BRVM standard (au lieu de 5)
    'ATR_PERIOD': 8,       # BRVM optimisé (au lieu de 14 classique)
    'SMA_FAST': 5,         # Au lieu de 3
    'SMA_SLOW': 10,        # Au lieu de 5
    'MIN_WEEKS_REQUIRED': 14,
    'VOLATILITY_WINDOW': 8  # Pour cohérence avec ATR
}

print("Configuration MODE PRODUCTION:")
for key, value in CONFIG_PRODUCTION.items():
    print(f"  {key}: {value}")

print("\n" + "-"*80)
print("PHASE 1: REBUILD WEEKLY COMPLET")
print("-"*80 + "\n")

# 1. Supprimer ancien WEEKLY (mode démarrage)
old_count = db.prices_weekly.count_documents({})
print(f"Suppression ancien WEEKLY: {old_count} observations...")

result = db.prices_weekly.delete_many({})
print(f"Supprime: {result.deleted_count}\n")

# 2. Reconstruire WEEKLY depuis DAILY (72 jours)
print("Reconstruction WEEKLY depuis DAILY...")

# Récupérer toutes les données DAILY triées
daily_data = list(db.prices_daily.find({}).sort([('symbol', 1), ('date', 1)]))

print(f"DAILY disponible: {len(daily_data)} observations")

# Grouper par symbole
symbol_data = defaultdict(list)
for doc in daily_data:
    symbol = doc.get('symbol')
    if symbol:
        symbol_data[symbol].append(doc)

print(f"Symboles distincts: {len(symbol_data)}\n")

# Fonction pour calculer la semaine ISO
def get_iso_week(date_str):
    """Retourne la semaine ISO (YYYY-Www)"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        iso = dt.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    except:
        return None

# Agrégation WEEKLY
weekly_docs = []
stats = {'symbols': 0, 'weeks': 0, 'observations': 0}

for symbol, docs in symbol_data.items():
    stats['symbols'] += 1
    
    # Grouper par semaine
    weeks_data = defaultdict(list)
    for doc in docs:
        week = get_iso_week(doc.get('date', ''))
        if week:
            weeks_data[week].append(doc)
    
    # Créer document WEEKLY pour chaque semaine
    for week, week_docs in weeks_data.items():
        if not week_docs:
            continue
        
        stats['weeks'] += 1
        
        # Trier par date
        week_docs.sort(key=lambda x: x.get('date', ''))
        
        # OHLC hebdomadaire
        opens = [d.get('open') for d in week_docs if d.get('open')]
        highs = [d.get('high') for d in week_docs if d.get('high')]
        lows = [d.get('low') for d in week_docs if d.get('low')]
        closes = [d.get('close') for d in week_docs if d.get('close')]
        volumes = [d.get('volume', 0) for d in week_docs]
        
        if not closes:
            continue
        
        # Document WEEKLY de base
        weekly_doc = {
            'symbol': symbol,
            'week': week,
            'open': opens[0] if opens else closes[0],
            'high': max(highs) if highs else max(closes),
            'low': min(lows) if lows else min(closes),
            'close': closes[-1],
            'volume': sum(volumes),
            'days_count': len(week_docs),
            'date_start': week_docs[0].get('date'),
            'date_end': week_docs[-1].get('date'),
            'indicators_computed': False,
            'created_at': datetime.utcnow()
        }
        
        weekly_docs.append(weekly_doc)

# Insérer tous les documents WEEKLY
if weekly_docs:
    stats['observations'] = len(weekly_docs)
    print(f"Insertion de {len(weekly_docs)} observations WEEKLY...")
    db.prices_weekly.insert_many(weekly_docs)
    print(f"Insere: {len(weekly_docs)}\n")

print("Statistiques WEEKLY:")
print(f"  Symboles: {stats['symbols']}")
print(f"  Semaines distinctes: {len(set(d['week'] for d in weekly_docs))}")
print(f"  Total observations: {stats['observations']}")

# Vérifier semaines disponibles
weeks_list = sorted(set(d['week'] for d in weekly_docs))
print(f"\nSemaines: {weeks_list[0]} -> {weeks_list[-1]}")
print(f"Total: {len(weeks_list)} semaines\n")

# 3. CALCUL INDICATEURS MODE PRODUCTION
print("-"*80)
print("PHASE 2: CALCUL INDICATEURS (MODE PRODUCTION)")
print("-"*80 + "\n")

def calculate_rsi(prices, period=14):
    """Calcul RSI avec période donnée"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_atr(highs, lows, closes, period=8):
    """Calcul ATR calibré BRVM (période 8)"""
    if len(highs) < period + 1:
        return None
    
    true_ranges = []
    for i in range(1, len(highs)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        tr = max(hl, hc, lc)
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    atr = sum(true_ranges[-period:]) / period
    
    # ATR en pourcentage du prix moyen
    avg_price = sum(closes[-period:]) / period
    atr_pct = (atr / avg_price) * 100 if avg_price > 0 else 0
    
    return round(atr_pct, 2)

def calculate_volatility(closes, period=8):
    """Volatilité = écart-type / moyenne sur période"""
    if len(closes) < period:
        return None
    
    recent = closes[-period:]
    avg = sum(recent) / len(recent)
    
    variance = sum((x - avg) ** 2 for x in recent) / len(recent)
    std_dev = variance ** 0.5
    
    volatility = (std_dev / avg) * 100 if avg > 0 else 0
    return round(volatility, 2)

# Pour chaque symbole, calculer indicateurs
updated_count = 0
symbols_processed = set()

for symbol in symbol_data.keys():
    symbols_processed.add(symbol)
    
    # Récupérer toutes les semaines pour ce symbole (triées)
    symbol_weeks = list(db.prices_weekly.find(
        {'symbol': symbol}
    ).sort('week', 1))
    
    if len(symbol_weeks) < CONFIG_PRODUCTION['MIN_WEEKS_REQUIRED']:
        continue  # Pas assez de données
    
    # Récupérer prix DAILY pour calculs
    daily_prices = list(db.prices_daily.find(
        {'symbol': symbol}
    ).sort('date', 1))
    
    if len(daily_prices) < 20:
        continue
    
    # Extraire arrays
    closes = [d.get('close') for d in daily_prices if d.get('close')]
    highs = [d.get('high') for d in daily_prices if d.get('high')]
    lows = [d.get('low') for d in daily_prices if d.get('low')]
    volumes = [d.get('volume', 0) for d in daily_prices]
    
    if not closes or len(closes) < CONFIG_PRODUCTION['RSI_PERIOD'] + 1:
        continue
    
    # Calculer indicateurs pour chaque semaine
    for week_doc in symbol_weeks:
        week = week_doc['week']
        
        # RSI
        rsi = calculate_rsi(closes, CONFIG_PRODUCTION['RSI_PERIOD'])
        
        # ATR calibré BRVM
        atr_pct = calculate_atr(highs, lows, closes, CONFIG_PRODUCTION['ATR_PERIOD'])
        
        # Volatilité
        volatility = calculate_volatility(closes, CONFIG_PRODUCTION['VOLATILITY_WINDOW'])
        
        # SMA
        sma_fast = sum(closes[-CONFIG_PRODUCTION['SMA_FAST']:]) / CONFIG_PRODUCTION['SMA_FAST'] if len(closes) >= CONFIG_PRODUCTION['SMA_FAST'] else None
        sma_slow = sum(closes[-CONFIG_PRODUCTION['SMA_SLOW']:]) / CONFIG_PRODUCTION['SMA_SLOW'] if len(closes) >= CONFIG_PRODUCTION['SMA_SLOW'] else None
        
        # Trend
        trend = 'BULLISH' if sma_fast and sma_slow and sma_fast > sma_slow else 'BEARISH' if sma_fast and sma_slow else 'NEUTRAL'
        
        # Volume ratio
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        current_volume = week_doc.get('volume', 0)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Signal RSI
        rsi_signal = 'OVERBOUGHT' if rsi and rsi > 70 else 'OVERSOLD' if rsi and rsi < 30 else 'NEUTRAL'
        
        # Mise à jour du document
        db.prices_weekly.update_one(
            {'symbol': symbol, 'week': week},
            {'$set': {
                'rsi': rsi,
                'rsi_signal': rsi_signal,
                'atr_pct': atr_pct,
                'volatility': volatility,
                'sma5': sma_fast,
                'sma10': sma_slow,
                'trend': trend,
                'volume_ratio': round(volume_ratio, 2),
                'indicators_computed': True,
                'indicators_config': CONFIG_PRODUCTION,
                'computed_at': datetime.utcnow()
            }}
        )
        
        updated_count += 1

print(f"Indicateurs calcules:")
print(f"  Symboles traites: {len(symbols_processed)}")
print(f"  Observations mises a jour: {updated_count}\n")

# 4. VÉRIFICATION QUALITÉ
print("-"*80)
print("PHASE 3: VERIFICATION QUALITE")
print("-"*80 + "\n")

# Statistiques ATR
atr_docs = list(db.prices_weekly.find(
    {'indicators_computed': True, 'atr_pct': {'$exists': True, '$ne': None}},
    {'atr_pct': 1, 'volatility': 1, 'symbol': 1, 'week': 1}
))

if atr_docs:
    atr_values = [doc['atr_pct'] for doc in atr_docs if doc.get('atr_pct')]
    vol_values = [doc['volatility'] for doc in atr_docs if doc.get('volatility')]
    
    avg_atr = sum(atr_values) / len(atr_values)
    min_atr = min(atr_values)
    max_atr = max(atr_values)
    
    avg_vol = sum(vol_values) / len(vol_values) if vol_values else 0
    max_vol = max(vol_values) if vol_values else 0
    
    print(f"ATR (periode {CONFIG_PRODUCTION['ATR_PERIOD']}):")
    print(f"  Moyenne: {avg_atr:.2f}%")
    print(f"  Min: {min_atr:.2f}%")
    print(f"  Max: {max_atr:.2f}%")
    print(f"  Cible BRVM: 5-18%")
    print(f"  Status: {'OK ✓' if 5 <= avg_atr <= 18 else 'A VERIFIER'}")
    
    print(f"\nVolatilite (periode {CONFIG_PRODUCTION['VOLATILITY_WINDOW']}):")
    print(f"  Moyenne: {avg_vol:.2f}%")
    print(f"  Max: {max_vol:.2f}%")
    print(f"  Cible: < 35%")
    print(f"  Status: {'OK ✓' if max_vol <= 35 else 'A VERIFIER'}")

# Résumé final
print("\n" + "="*80)
print("RECAPITULATIF RECALIBRATION")
print("="*80 + "\n")

final_weekly = db.prices_weekly.count_documents({})
final_weeks = len(db.prices_weekly.distinct('week'))
final_with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})

print(f"WEEKLY reconstruit:")
print(f"  Observations: {final_weekly}")
print(f"  Semaines: {final_weeks}")
print(f"  Avec indicateurs: {final_with_indicators} ({final_with_indicators/final_weekly*100:.1f}%)")

print(f"\nConfiguration appliquee:")
print(f"  Mode: {CONFIG_PRODUCTION['MODE']}")
print(f"  RSI: {CONFIG_PRODUCTION['RSI_PERIOD']} periodes")
print(f"  ATR: {CONFIG_PRODUCTION['ATR_PERIOD']} periodes (BRVM)")
print(f"  SMA: {CONFIG_PRODUCTION['SMA_FAST']}/{CONFIG_PRODUCTION['SMA_SLOW']}")

print(f"\n{'='*80}")
if final_weeks >= 14 and 5 <= avg_atr <= 18 and max_vol <= 35:
    print("STATUT: CALIBRATION PRODUCTION REUSSIE ✓")
    print("\nProchaines etapes:")
    print("  B - Rebuild moteur opportuniste daily")
    print("  C - Recalculer Top5 avec 14 semaines")
    print("  D - Activer auto-learning")
else:
    print("STATUT: VERIFICATION NECESSAIRE")
    if final_weeks < 14:
        print(f"  - Semaines insuffisantes: {final_weeks}/14")
    if not (5 <= avg_atr <= 18):
        print(f"  - ATR hors cible: {avg_atr:.2f}% (cible 5-18%)")
    if max_vol > 35:
        print(f"  - Volatilite excessive: {max_vol:.2f}% (cible <35%)")

print(f"\n{'='*80}\n")

# Sauvegarder config
with open('CONFIG_PRODUCTION_BRVM.txt', 'w', encoding='utf-8') as f:
    f.write("CONFIGURATION PRODUCTION BRVM\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date application: {datetime.now()}\n\n")
    for key, value in CONFIG_PRODUCTION.items():
        f.write(f"{key}: {value}\n")
    f.write(f"\nWEEKLY: {final_weekly} obs, {final_weeks} semaines\n")
    f.write(f"Indicateurs: {final_with_indicators}/{final_weekly}\n")
    if atr_docs:
        f.write(f"\nATR moyen: {avg_atr:.2f}%\n")
        f.write(f"Volatilite max: {max_vol:.2f}%\n")

print("Configuration sauvegardee: CONFIG_PRODUCTION_BRVM.txt")

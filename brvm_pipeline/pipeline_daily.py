#!/usr/bin/env python3
"""
🟢 PIPELINE DAILY - NIVEAU 2 (SOURCE DE VÉRITÉ)

PRINCIPE :
- 1 ligne par action / par jour
- Construite à partir des données RAW (niveau 1)
- Agrégation : Open=premier, High=max, Low=min, Close=dernier, Volume=somme
- Alimente les indicateurs techniques (RSI, ATR, SMA)

EXÉCUTION :
- À la clôture du marché (17h BRVM)
- OU manuellement pour rattrapage historique
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

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

COLLECTION_RAW = "prices_intraday_raw"
COLLECTION_DAILY = "prices_daily"
SOURCE = "DAILY_AGGREGATION"

# ============================================================================
# AGRÉGATION RAW → DAILY
# ============================================================================

def aggregate_day(date_str, symbol=None):
    """
    Agréger toutes les collectes intraday d'une date en 1 ligne daily
    
    Args:
        date_str: Format "YYYY-MM-DD"
        symbol: Si None, traite tous les symboles
    
    Returns:
        int: Nombre de daily créés
    """
    query = {'date': date_str}
    if symbol:
        query['symbol'] = symbol
    
    # Grouper par symbole
    raw_data = list(db[COLLECTION_RAW].find(query).sort('datetime', 1))
    
    if not raw_data:
        print(f"⚠️  Aucune donnée RAW pour {date_str}" + (f" ({symbol})" if symbol else ""))
        return 0
    
    # Grouper par symbol
    by_symbol = defaultdict(list)
    for doc in raw_data:
        by_symbol[doc['symbol']].append(doc)
    
    print(f"\n📅 Agrégation DAILY : {date_str}")
    print(f"   {len(by_symbol)} symboles à traiter")
    
    created = 0
    updated = 0
    
    for sym, observations in by_symbol.items():
        # Trier par datetime
        observations.sort(key=lambda x: x['datetime'])
        
        # Extraire tous les prix non-null
        all_opens = [o['open'] for o in observations if o.get('open')]
        all_highs = [o['high'] for o in observations if o.get('high')]
        all_lows = [o['low'] for o in observations if o.get('low')]
        all_closes = [o['close'] for o in observations if o.get('close')]
        all_volumes = [o['volume'] for o in observations if o.get('volume')]
        
        # Agrégation mathématique
        open_price = all_opens[0] if all_opens else None         # Premier
        high_price = max(all_highs) if all_highs else None       # Maximum
        low_price = min(all_lows) if all_lows else None          # Minimum
        close_price = all_closes[-1] if all_closes else None     # Dernier
        volume = sum(all_volumes) if all_volumes else 0          # Somme
        
        # Variation %
        variation_pct = None
        if open_price and close_price and open_price > 0:
            variation_pct = ((close_price - open_price) / open_price) * 100
        
        # Document DAILY (source de vérité)
        daily_doc = {
            'symbol': sym,
            'date': date_str,
            'source': SOURCE,
            'updated_at': datetime.now(),
            
            # OHLC officiel (source de vérité)
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'variation_pct': variation_pct,
            
            # Métadonnées
            'nb_observations_raw': len(observations),  # Combien de collectes intraday
            'first_datetime': observations[0]['datetime'],
            'last_datetime': observations[-1]['datetime'],
            
            # FLAGS
            'level': 'DAILY',
            'is_complete': bool(open_price and high_price and low_price and close_price),
            'used_for_weekly': False,
            'indicators_computed': False  # RSI, ATR, etc. seront calculés après
        }
        
        # Upsert (1 seul daily par symbol + date)
        result = db[COLLECTION_DAILY].update_one(
            {'symbol': sym, 'date': date_str},
            {'$set': daily_doc},
            upsert=True
        )
        
        if result.upserted_id:
            created += 1
        else:
            updated += 1
        
        # Marquer les RAW comme utilisés
        db[COLLECTION_RAW].update_many(
            {'symbol': sym, 'date': date_str},
            {'$set': {'used_for_daily': True}}
        )
    
    print(f"   ✅ Créés : {created}")
    print(f"   🔄 Mis à jour : {updated}")
    
    return created + updated

# ============================================================================
# RATTRAPAGE HISTORIQUE
# ============================================================================

def rebuild_all_daily(from_date=None, to_date=None):
    """
    Reconstruire toutes les données DAILY à partir de RAW
    
    Args:
        from_date: Date début (YYYY-MM-DD) ou None pour tout
        to_date: Date fin (YYYY-MM-DD) ou None pour aujourd'hui
    """
    print("\n" + "="*80)
    print("🔄 RECONSTRUCTION COMPLÈTE DAILY (depuis RAW)")
    print("="*80 + "\n")
    
    # Trouver toutes les dates dans RAW
    query = {}
    if from_date:
        query['date'] = {'$gte': from_date}
    if to_date:
        if 'date' in query:
            query['date']['$lte'] = to_date
        else:
            query['date'] = {'$lte': to_date}
    
    all_dates = sorted(db[COLLECTION_RAW].distinct('date', query))
    
    if not all_dates:
        print("❌ Aucune date trouvée dans RAW")
        return
    
    print(f"📅 Dates à traiter : {len(all_dates)}")
    print(f"   De : {all_dates[0]}")
    print(f"   À  : {all_dates[-1]}")
    print()
    
    total = 0
    for i, date in enumerate(all_dates, 1):
        print(f"[{i}/{len(all_dates)}] {date}", end=" ")
        count = aggregate_day(date)
        total += count
    
    print("\n" + "="*80)
    print(f"✅ TOTAL DAILY créés/mis à jour : {total}")
    print("="*80 + "\n")

# ============================================================================
# STATS
# ============================================================================

def show_daily_stats():
    """Afficher stats DAILY"""
    total = db[COLLECTION_DAILY].count_documents({})
    
    # Dates
    dates = sorted(db[COLLECTION_DAILY].distinct('date'))
    first_date = dates[0] if dates else 'N/A'
    last_date = dates[-1] if dates else 'N/A'
    
    # Symboles
    symbols = len(db[COLLECTION_DAILY].distinct('symbol'))
    
    # Complétude
    complete = db[COLLECTION_DAILY].count_documents({'is_complete': True})
    complete_pct = (complete / total * 100) if total > 0 else 0
    
    print("\n" + "="*80)
    print("📊 STATS COLLECTION DAILY (prices_daily)")
    print("="*80)
    print(f"Total jours × symboles : {total:,}")
    print(f"Période                : {first_date} → {last_date} ({len(dates)} jours)")
    print(f"Symboles uniques       : {symbols}")
    print(f"OHLC complet           : {complete:,} / {total:,} ({complete_pct:.1f}%)")
    print("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline DAILY - Niveau 2')
    parser.add_argument('--date', help='Date spécifique (YYYY-MM-DD)')
    parser.add_argument('--rebuild', action='store_true', help='Reconstruire tout')
    parser.add_argument('--from-date', help='Date début pour rebuild')
    parser.add_argument('--to-date', help='Date fin pour rebuild')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🟢 PIPELINE DAILY - NIVEAU 2 (SOURCE DE VÉRITÉ)")
    print("="*80 + "\n")
    
    if args.rebuild:
        # Reconstruction complète
        rebuild_all_daily(args.from_date, args.to_date)
    elif args.date:
        # Date spécifique
        aggregate_day(args.date)
    else:
        # Par défaut : hier (car données complètes)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 Agrégation par défaut : {yesterday}")
        aggregate_day(yesterday)
    
    # Stats
    show_daily_stats()
    
    print("✅ Pipeline DAILY terminé\n")

if __name__ == "__main__":
    main()

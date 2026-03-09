"""
AGRÉGATION HEBDOMADAIRE DES DONNÉES BRVM
Objectif: Trading hebdomadaire - besoin de données OHLC par semaine
"""

import pymongo
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# Connexion MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("AGRÉGATION HEBDOMADAIRE BRVM - TRADING HEBDOMADAIRE")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print()

# ÉTAPE 1: Récupérer toutes les observations STOCK_PRICE
print("[1/5] Chargement observations STOCK_PRICE...")
observations = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}).sort('timestamp', 1))
print(f"  Total observations: {len(observations)}")
print()

# ÉTAPE 2: Grouper par ticker et semaine
print("[2/5] Groupement par ticker et semaine...")

def get_week_key(date_obj):
    """Retourne année-semaine (ex: 2025-W38)"""
    if isinstance(date_obj, str):
        # Parser différents formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
            try:
                date_obj = datetime.strptime(date_obj.split('+')[0].split('.')[0], fmt)
                break
            except:
                continue
    
    if isinstance(date_obj, datetime):
        year, week, _ = date_obj.isocalendar()
        return f"{year}-W{week:02d}"
    return None

# Grouper par ticker + semaine
by_ticker_week = defaultdict(lambda: defaultdict(list))

for obs in observations:
    ticker = obs.get('ticker') or obs.get('symbole')
    timestamp = obs.get('timestamp') or obs.get('ts') or obs.get('date')
    
    if not ticker or ticker == 'N/A' or not timestamp:
        continue
    
    week_key = get_week_key(timestamp)
    if week_key:
        by_ticker_week[ticker][week_key].append(obs)

print(f"  Tickers uniques: {len(by_ticker_week)}")
total_weeks = sum(len(weeks) for weeks in by_ticker_week.values())
print(f"  Total semaines: {total_weeks}")
print()

# ÉTAPE 3: Calculer OHLC hebdomadaire + volume
print("[3/5] Calcul OHLC hebdomadaire par action...")

weekly_data = []
stats = {
    'semaines_creees': 0,
    'tickers_traites': 0,
    'observations_sources': 0
}

for ticker in sorted(by_ticker_week.keys()):
    weeks = by_ticker_week[ticker]
    
    for week_key in sorted(weeks.keys()):
        week_obs = weeks[week_key]
        
        if len(week_obs) == 0:
            continue
        
        # Normaliser timestamps pour tri
        def get_sortable_ts(obs):
            ts = obs.get('timestamp') or obs.get('ts') or obs.get('date')
            if isinstance(ts, str):
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
                    try:
                        return datetime.strptime(ts.split('+')[0].split('.')[0], fmt)
                    except:
                        continue
                return datetime.now()
            return ts if isinstance(ts, datetime) else datetime.now()
        
        # Trier par timestamp
        week_obs_sorted = sorted(week_obs, key=get_sortable_ts)
        
        # Extraire OHLC depuis attrs ou racine
        opens = []
        highs = []
        lows = []
        closes = []
        
        for obs in week_obs_sorted:
            # Essayer attrs d'abord, sinon racine
            attrs = obs.get('attrs', {})
            
            open_p = attrs.get('open') or obs.get('open') or obs.get('prix')
            high_p = attrs.get('high') or obs.get('high')
            low_p = attrs.get('low') or obs.get('low')
            close_p = attrs.get('close') or obs.get('close') or obs.get('value') or obs.get('prix_cloture')
            
            if close_p and close_p > 0:
                closes.append(close_p)
                if open_p and open_p > 0:
                    opens.append(open_p)
                if high_p and high_p > 0:
                    highs.append(high_p)
                if low_p and low_p > 0:
                    lows.append(low_p)
        
        if len(closes) == 0:
            continue
        
        # OHLC hebdomadaire
        open_price = opens[0] if opens else closes[0]  # Premier open ou premier close
        high_price = max(highs) if highs else max(closes)  # Prix max
        low_price = min(lows) if lows else min(closes)  # Prix min
        close_price = closes[-1]  # Dernier close de la semaine
        
        # Volume total de la semaine
        volumes = []
        for obs in week_obs:
            attrs = obs.get('attrs', {})
            vol = attrs.get('volume') or obs.get('volume')
            if vol:
                volumes.append(vol)
        total_volume = sum(volumes) if volumes else 0
        
        # Variation hebdomadaire
        variation_pct = ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0
        
        # Timestamp début semaine (lundi)
        first_ts = week_obs_sorted[0].get('timestamp') or week_obs_sorted[0].get('ts') or week_obs_sorted[0].get('date')
        if isinstance(first_ts, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
                try:
                    first_ts = datetime.strptime(first_ts.split('+')[0].split('.')[0], fmt)
                    break
                except:
                    continue
        
        # Trouver le lundi de la semaine
        if isinstance(first_ts, datetime):
            monday = first_ts - timedelta(days=first_ts.weekday())
            week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            week_start = datetime.now()
        
        # Créer document hebdomadaire
        weekly_doc = {
            'dataset': 'STOCK_PRICE',
            'granularite': 'WEEKLY',
            'ticker': ticker,
            'symbole': ticker,
            'week': week_key,
            'week_start': week_start,
            'timestamp': week_start,
            'ts': week_start.isoformat() if isinstance(week_start, datetime) else str(week_start),
            'key': f"{ticker}_{week_key}",  # Clé unique pour index
            
            # OHLC hebdomadaire
            'open': float(open_price),
            'high': float(high_price),
            'low': float(low_price),
            'close': float(close_price),
            'prix_cloture': float(close_price),
            'prix': float(close_price),
            
            # Volume
            'volume': int(total_volume),
            
            # Variation
            'variation_pct': float(variation_pct),
            'variation': float(variation_pct),
            
            # Métadonnées
            'nb_observations': len(week_obs),
            'created_at': datetime.now(),
            'source': 'AGREGATION_HEBDOMADAIRE'
        }
        
        weekly_data.append(weekly_doc)
        stats['semaines_creees'] += 1
        stats['observations_sources'] += len(week_obs)
    
    stats['tickers_traites'] += 1
    if stats['tickers_traites'] % 10 == 0:
        print(f"  Traité {stats['tickers_traites']}/{len(by_ticker_week)} tickers...")

print(f"  Semaines créées: {stats['semaines_creees']}")
print()

# ÉTAPE 4: Nettoyer anciennes données hebdomadaires
print("[4/5] Nettoyage anciennes données hebdomadaires...")
deleted = db.curated_observations.delete_many({'granularite': 'WEEKLY'})
print(f"  Supprimé: {deleted.deleted_count} anciennes semaines")
print()

# ÉTAPE 5: Insérer nouvelles données hebdomadaires
print("[5/5] Insertion données hebdomadaires...")
if weekly_data:
    result = db.curated_observations.insert_many(weekly_data)
    print(f"  Inséré: {len(result.inserted_ids)} semaines")
else:
    print("  Aucune donnée à insérer")
print()

# RÉSUMÉ
print("="*80)
print("RÉSUMÉ AGRÉGATION HEBDOMADAIRE")
print("="*80)
print(f"  Observations sources     : {stats['observations_sources']}")
print(f"  Tickers traités          : {stats['tickers_traites']}")
print(f"  Semaines créées          : {stats['semaines_creees']}")
print()

# Statistiques par ticker
print("COUVERTURE PAR TICKER (Top 10):")
ticker_weeks = defaultdict(int)
for doc in weekly_data:
    ticker_weeks[doc['ticker']] += 1

for ticker in sorted(ticker_weeks.keys(), key=lambda t: ticker_weeks[t], reverse=True)[:10]:
    weeks = ticker_weeks[ticker]
    print(f"  {ticker:6s} : {weeks:3d} semaines")
print()

# Vérification finale
total_weekly = db.curated_observations.count_documents({'granularite': 'WEEKLY'})
total_hourly = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE', 'granularite': {'$exists': False}})

print("="*80)
print("ÉTAT FINAL BASE DE DONNÉES")
print("="*80)
print(f"  Données HEBDOMADAIRES (WEEKLY) : {total_weekly}")
print(f"  Données HORAIRES (brutes)      : {total_hourly}")
print()
print("✓ Prêt pour ANALYSE TECHNIQUE HEBDOMADAIRE")
print("✓ Prêt pour TRADING HEBDOMADAIRE (horizon 1 semaine)")
print()

client.close()

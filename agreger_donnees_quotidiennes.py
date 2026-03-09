"""
AGRÉGATION DES DONNÉES STOCK_PRICE PAR JOUR
Convertir les données minute-par-minute en données OHLC quotidiennes
pour l'analyse technique
"""

from pymongo import MongoClient
from datetime import datetime
from collections import defaultdict
import re

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("AGRÉGATION DONNÉES STOCK_PRICE PAR JOUR")
print("="*80)
print()

# 1. État initial
total_avant = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"[AVANT] Observations STOCK_PRICE: {total_avant}")
print()

# 2. Récupérer toutes les observations
print("[ÉTAPE 1/3] Récupération des observations...")
observations = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}))
print(f"  {len(observations)} observations récupérées")
print()

# 3. Grouper par ticker et date (sans heure)
print("[ÉTAPE 2/3] Agrégation par ticker et jour...")
grouped = defaultdict(lambda: defaultdict(list))

for obs in observations:
    ticker = obs.get('ticker')
    if not ticker:
        continue
    
    # Extraire la date (sans heure)
    ts = obs.get('ts')
    if not ts:
        continue
    
    # Extraire juste la date (YYYY-MM-DD)
    if 'T' in ts:
        date_only = ts.split('T')[0]
    else:
        date_only = ts[:10]
    
    grouped[ticker][date_only].append(obs)

print(f"  {len(grouped)} tickers traités")
print()

# 4. Créer les observations quotidiennes OHLC
print("[ÉTAPE 3/3] Création observations OHLC quotidiennes...")
observations_journalieres = []
stats = {
    'tickers_traites': 0,
    'jours_crees': 0,
    'obs_agregees': 0
}

for ticker in sorted(grouped.keys()):
    dates_ticker = grouped[ticker]
    stats['tickers_traites'] += 1
    
    for date_str, obs_jour in dates_ticker.items():
        stats['jours_crees'] += 1
        stats['obs_agregees'] += len(obs_jour)
        
        # Extraire les valeurs
        values = []
        volumes = []
        timestamps = []
        
        for obs in obs_jour:
            # Prix de clôture
            prix = obs.get('value') or obs.get('prix_cloture') or obs.get('close')
            if prix:
                values.append(float(prix))
            
            # Volume
            vol = obs.get('volume') or 0
            if vol:
                volumes.append(int(vol))
            
            # Timestamp pour tri
            ts = obs.get('ts', '')
            timestamps.append(ts)
            
            # Attributs additionnels
            attrs = obs.get('attrs', {})
            if attrs:
                if attrs.get('open'):
                    values.append(float(attrs['open']))
                if attrs.get('high'):
                    values.append(float(attrs['high']))
                if attrs.get('low'):
                    values.append(float(attrs['low']))
                if attrs.get('close'):
                    values.append(float(attrs['close']))
        
        if not values:
            continue
        
        # Trier les observations par timestamp pour avoir bon ordre
        obs_sorted = sorted(zip(timestamps, obs_jour), key=lambda x: x[0])
        
        # Calculer OHLC
        open_price = None
        high_price = max(values) if values else None
        low_price = min(values) if values else None
        close_price = None
        total_volume = sum(volumes) if volumes else 0
        
        # Open = prix de la première observation
        if obs_sorted:
            first_obs = obs_sorted[0][1]
            open_price = (first_obs.get('value') or 
                         first_obs.get('prix_cloture') or 
                         first_obs.get('close') or
                         first_obs.get('attrs', {}).get('open'))
        
        # Close = prix de la dernière observation
        if obs_sorted:
            last_obs = obs_sorted[-1][1]
            close_price = (last_obs.get('value') or 
                          last_obs.get('prix_cloture') or 
                          last_obs.get('close') or
                          last_obs.get('attrs', {}).get('close'))
        
        # Variation
        variation_pct = 0
        if open_price and close_price and open_price > 0:
            variation_pct = ((close_price - open_price) / open_price) * 100
        
        # Créer l'observation quotidienne
        obs_quotidienne = {
            'dataset': 'STOCK_PRICE_DAILY',
            'ticker': ticker,
            'symbole': ticker,
            'date': date_str,
            'timestamp': f"{date_str}T00:00:00+00:00",
            'source': 'BRVM_AGGREGATED',
            'key': f"{ticker}_{date_str}",
            
            # OHLC
            'open': float(open_price) if open_price else None,
            'high': float(high_price) if high_price else None,
            'low': float(low_price) if low_price else None,
            'close': float(close_price) if close_price else None,
            'prix_ouverture': float(open_price) if open_price else None,
            'prix_haut': float(high_price) if high_price else None,
            'prix_bas': float(low_price) if low_price else None,
            'prix_cloture': float(close_price) if close_price else None,
            
            # Volume
            'volume': int(total_volume),
            
            # Variation
            'variation_pct': round(variation_pct, 2),
            'variation': round(variation_pct, 2),
            
            # Métadonnées
            'nombre_ticks': len(obs_jour),
            'aggregation_source': 'intraday_to_daily',
            'created_at': datetime.utcnow()
        }
        
        observations_journalieres.append(obs_quotidienne)

print(f"  {stats['jours_crees']} jours créés")
print(f"  {stats['obs_agregees']} observations agrégées")
print()

# 5. Insertion dans MongoDB
if observations_journalieres:
    print("[INSERTION] Sauvegarde des données quotidiennes...")
    
    # Supprimer anciennes données quotidiennes
    deleted = db.curated_observations.delete_many({'dataset': 'STOCK_PRICE_DAILY'})
    print(f"  Anciennes données supprimées: {deleted.deleted_count}")
    
    # Insérer nouvelles données
    result = db.curated_observations.insert_many(observations_journalieres)
    print(f"  Nouvelles observations insérées: {len(result.inserted_ids)}")
    print()

# 6. Statistiques finales
print("="*80)
print("RÉSUMÉ AGRÉGATION")
print("="*80)
print(f"  Tickers traités: {stats['tickers_traites']}")
print(f"  Jours créés: {stats['jours_crees']}")
print(f"  Observations minute agrégées: {stats['obs_agregees']}")
print(f"  Observations quotidiennes créées: {len(observations_journalieres)}")
print()

# 7. Vérification par ticker
print("VÉRIFICATION PAR TICKER (top 10):")
pipeline = [
    {'$match': {'dataset': 'STOCK_PRICE_DAILY'}},
    {'$group': {
        '_id': '$ticker',
        'count': {'$sum': 1}
    }},
    {'$sort': {'count': -1}},
    {'$limit': 10}
]

daily_stats = list(db.curated_observations.aggregate(pipeline))
for stat in daily_stats:
    ticker = stat['_id']
    count = stat['count']
    print(f"  {ticker:10s} : {count:3d} jours de données")
print()

print("="*80)
print("DONNÉES PRÊTES POUR ANALYSE TECHNIQUE")
print("="*80)
print("  ✓ Dataset créé: STOCK_PRICE_DAILY")
print("  ✓ Format: OHLC quotidien")
print(f"  ✓ {len(observations_journalieres)} observations disponibles")
print("  ✓ Analyse technique peut maintenant utiliser ces données")
print()

client.close()

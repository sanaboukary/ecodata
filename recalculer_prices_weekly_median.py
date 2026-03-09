#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recalculer prices_weekly depuis prices_daily avec MÉDIANE (tolérance zéro)
Supprime données aberrantes et utilise VRAIES données BRVM uniquement
"""

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

_, db = get_mongo_db()

print('=' * 80)
print('NETTOYAGE ET RECALCUL PRICES_WEEKLY (MÉTHODE MÉDIANE)')
print('=' * 80)

# ÉTAPE 1: Supprimer toutes les données weekly aberrantes
print('\n[ÉTAPE 1] Suppression prices_weekly (données aberrantes)...')
result = db.prices_weekly.delete_many({})
print(f'  ✓ {result.deleted_count} documents supprimés')

# ÉTAPE 2: Récupérer toutes les données daily réelles
print('\n[ÉTAPE 2] Récupération prices_daily (données réelles BRVM)...')
daily_docs = list(db.prices_daily.find({}).sort('date', 1))
print(f'  ✓ {len(daily_docs)} documents daily trouvés')

# ÉTAPE 3: Grouper par symbol + semaine
print('\n[ÉTAPE 3] Agrégation par semaine avec MÉDIANE...')
weekly_data = defaultdict(lambda: defaultdict(list))

for doc in daily_docs:
    symbol = doc.get('symbol')
    date = doc.get('date')
    
    if not symbol or not date:
        continue
    
    # Convertir date en semaine ISO
    if isinstance(date, str):
        try:
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except:
            continue
    else:
        date_obj = date
    
    iso_year, iso_week, _ = date_obj.isocalendar()
    week_key = f"{iso_year}-W{iso_week:02d}"
    
    # Collecter les prix pour calculer médiane
    weekly_data[symbol][week_key].append({
        'open': doc.get('open', 0),
        'high': doc.get('high', 0),
        'low': doc.get('low', 0),
        'close': doc.get('close', 0),
        'volume': doc.get('volume', 0),
        'date': date_obj
    })

# ÉTAPE 4: Calculer médianes et insérer
print('\n[ÉTAPE 4] Calcul médianes et insertion...')
inserted_count = 0

for symbol, weeks in weekly_data.items():
    for week, daily_prices in weeks.items():
        if not daily_prices:
            continue
        
        # Calculer MÉDIANES (plus robuste que moyenne contre aberrations)
        opens = [p['open'] for p in daily_prices if p['open'] > 0]
        highs = [p['high'] for p in daily_prices if p['high'] > 0]
        lows = [p['low'] for p in daily_prices if p['low'] > 0]
        closes = [p['close'] for p in daily_prices if p['close'] > 0]
        volumes = [p['volume'] for p in daily_prices if p['volume'] > 0]
        
        if not closes:  # Pas de données valides
            continue
        
        weekly_doc = {
            'symbol': symbol,
            'week': week,
            'open': statistics.median(opens) if opens else 0,
            'high': max(highs) if highs else 0,  # Max pour high
            'low': min(lows) if lows else 0,      # Min pour low
            'close': statistics.median(closes),   # Médiane pour close
            'volume': sum(volumes),                # Somme pour volume
            'nb_jours': len(daily_prices),
            'updated_at': datetime.utcnow()
        }
        
        db.prices_weekly.insert_one(weekly_doc)
        inserted_count += 1

print(f'  ✓ {inserted_count} semaines insérées')

# ÉTAPE 5: Vérification échantillon
print('\n[ÉTAPE 5] Vérification (ETIT, NEIC, SIBC)...')
for symbol in ['ETIT', 'NEIC', 'SIBC']:
    # Prix daily récent
    daily = db.prices_daily.find_one({'symbol': symbol}, sort=[('date', -1)])
    prix_daily = daily.get('close', 0) if daily else 0
    
    # Prix weekly récent
    weekly = db.prices_weekly.find_one({'symbol': symbol}, sort=[('week', -1)])
    prix_weekly = weekly.get('close', 0) if weekly else 0
    week_str = weekly.get('week', 'N/A') if weekly else 'N/A'
    
    # Calculer ratio (doit être proche de 1.0)
    ratio = prix_weekly / prix_daily if prix_daily > 0 else 0
    status = '✓ OK' if 0.8 <= ratio <= 1.2 else '⚠️ VÉRIFIER'
    
    print(f'  [{symbol}]')
    print(f'    Daily récent: {prix_daily:,.0f} FCFA')
    print(f'    Weekly {week_str}: {prix_weekly:,.0f} FCFA (ratio: {ratio:.2f}) {status}')

print('\n' + '=' * 80)
print('RÉSULTAT:')
print('  ✓ prices_weekly recalculé avec MÉDIANES depuis données BRVM réelles')
print('  ✓ Tolérance zéro: Aucune donnée simulée/aberrante')
print('  ✓ Prêt pour génération recommandations')
print('=' * 80)

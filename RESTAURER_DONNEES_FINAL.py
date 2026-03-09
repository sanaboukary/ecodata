#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTAURATION DES DONNÉES BRVM PERDUES
======================================
Restaurer 43 jours de données depuis curated_observations vers prices_daily
"""
from pymongo import MongoClient
from datetime import datetime
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("RESTAURATION DES DONNEES BRVM PERDUES")
print("="*80 + "\n")

# Liste des jours manquants à restaurer
MISSING_DATES = [
    '2025-10-16', '2025-10-17', '2025-10-20', '2025-10-21', '2025-10-22',
    '2025-10-23', '2025-10-24', '2025-10-27', '2025-10-28', '2025-10-29',
    '2025-10-30', '2025-10-31', '2025-11-03', '2025-11-04', '2025-11-05',
    '2025-11-06', '2025-11-07', '2025-11-10', '2025-11-11', '2025-11-12',
    '2025-11-13', '2025-11-14', '2025-11-17', '2025-11-18', '2025-11-19',
    '2025-11-20', '2025-11-21', '2025-11-24', '2025-11-25', '2025-11-26',
    '2025-11-27', '2025-11-28', '2025-12-01', '2025-12-02', '2025-12-03',
    '2025-12-04', '2025-12-05', '2025-12-09', '2025-12-11', '2025-12-12',
    '2026-01-05', '2026-01-09', '2026-02-02'
]

print(f"Jours a restaurer: {len(MISSING_DATES)}\n")

# Statistiques
stats = {
    'processed_dates': 0,
    'created': 0,
    'skipped': 0,
    'errors': 0
}

# Fonction de restauration pour une date
def restore_date(date_str):
    """Restaurer tous les symboles pour une date donnee"""
    print(f"\nTraitement: {date_str}")
    print("-" * 40)
    
    created_count = 0
    skipped_count = 0
    
    # 1. Chercher dans BRVM_AGGREGATED (prioritaire - format OHLC complet)
    aggregated_docs = list(db.curated_observations.find({
        'source': 'BRVM_AGGREGATED',
        'date': date_str
    }))
    
    print(f"  BRVM_AGGREGATED: {len(aggregated_docs)} observations")
    
    for doc in aggregated_docs:
        symbol = doc.get('symbole') or doc.get('ticker')
        if not symbol:
            continue
        
        # Verifier si existe deja
        existing = db.prices_daily.find_one({
            'symbol': symbol,
            'date': date_str
        })
        
        if existing:
            skipped_count += 1
            continue
        
        # Creer document prices_daily
        daily_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': doc.get('open', doc.get('prix_ouverture')),
            'high': doc.get('high', doc.get('prix_haut')),
            'low': doc.get('low', doc.get('prix_bas')),
            'close': doc.get('close', doc.get('prix_cloture')),
            'volume': doc.get('volume', 0),
            'variation_pct': doc.get('variation_pct', doc.get('variation', 0.0)),
            'is_complete': True,
            'source': 'RESTORED_FROM_CURATED',
            'original_source': 'BRVM_AGGREGATED',
            'restored_at': datetime.now()
        }
        
        # Inserer
        try:
            db.prices_daily.insert_one(daily_doc)
            created_count += 1
        except Exception as e:
            print(f"    Erreur {symbol}: {e}")
            stats['errors'] += 1
    
    # 2. Completer avec BRVM_CSV_HISTORIQUE pour symboles manquants
    csv_docs = list(db.curated_observations.find({
        'source': 'BRVM_CSV_HISTORIQUE',
        'ts': date_str
    }))
    
    if csv_docs:
        print(f"  BRVM_CSV_HISTORIQUE: {len(csv_docs)} observations")
    
    for doc in csv_docs:
        symbol = doc.get('ticker')
        if not symbol:
            continue
        
        # Verifier si existe deja
        existing = db.prices_daily.find_one({
            'symbol': symbol,
            'date': date_str
        })
        
        if existing:
            continue
        
        # Creer document (format simplifie)
        close_price = doc.get('value') or doc.get('attrs', {}).get('close')
        volume = doc.get('attrs', {}).get('volume', 0)
        variation = doc.get('attrs', {}).get('variation', 0.0)
        
        daily_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': close_price,   # Approximation
            'high': close_price,   # Approximation
            'low': close_price,    # Approximation
            'close': close_price,
            'volume': volume,
            'variation_pct': variation,
            'is_complete': False,  # Pas OHLC complet
            'source': 'RESTORED_FROM_CURATED',
            'original_source': 'BRVM_CSV_HISTORIQUE',
            'restored_at': datetime.now()
        }
        
        try:
            db.prices_daily.insert_one(daily_doc)
            created_count += 1
        except Exception as e:
            print(f"    Erreur {symbol}: {e}")
            stats['errors'] += 1
    
    # 3. Completer avec BRVM_CSV_RESTAURATION si necessaire
    resto_docs = list(db.curated_observations.find({
        'source': 'BRVM_CSV_RESTAURATION',
        'ts': date_str
    }))
    
    if resto_docs:
        print(f"  BRVM_CSV_RESTAURATION: {len(resto_docs)} observations")
    
    for doc in resto_docs:
        symbol = doc.get('key')
        if not symbol:
            continue
        
        # Verifier si existe deja
        existing = db.prices_daily.find_one({
            'symbol': symbol,
            'date': date_str
        })
        
        if existing:
            continue
        
        attrs = doc.get('attrs', {})
        close_price = doc.get('value') or attrs.get('cours')
        
        daily_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': attrs.get('ouverture', close_price),
            'high': close_price,   # Approximation
            'low': close_price,    # Approximation
            'close': close_price,
            'volume': attrs.get('volume', 0),
            'variation_pct': attrs.get('variation_pct', 0.0),
            'is_complete': False,
            'source': 'RESTORED_FROM_CURATED',
            'original_source': 'BRVM_CSV_RESTAURATION',
            'restored_at': datetime.now()
        }
        
        try:
            db.prices_daily.insert_one(daily_doc)
            created_count += 1
        except Exception as e:
            print(f"    Erreur {symbol}: {e}")
            stats['errors'] += 1
    
    print(f"  Crees: {created_count} | Ignores: {skipped_count}")
    
    return created_count, skipped_count

# MODE SIMULATION ou EXECUTION
SIMULATION_MODE = True  # Mettre False pour vraie restauration

if SIMULATION_MODE:
    print("MODE: SIMULATION (aucune modification)")
    print("Pour restaurer reellement, editer le script et mettre SIMULATION_MODE = False\n")
    # Tester sur 3 dates seulement
    test_dates = MISSING_DATES[:3]
else:
    print("MODE: EXECUTION REELLE\n")
    # Demander confirmation
    print("ATTENTION: Cette operation va modifier prices_daily")
    response = input("Continuer? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Annule")
        sys.exit(0)
    test_dates = MISSING_DATES

# Restauration
print("\nDemarrage restauration...")
print("="*80)

for date in (test_dates if SIMULATION_MODE else MISSING_DATES):
    created, skipped = restore_date(date)
    stats['processed_dates'] += 1
    stats['created'] += created
    stats['skipped'] += skipped

# Resultats finaux
print("\n" + "="*80)
print("RESULTATS DE LA RESTAURATION")
print("="*80)
print(f"\nDates traitees: {stats['processed_dates']}/{len(MISSING_DATES)}")
print(f"Observations creees: {stats['created']}")
print(f"Observations ignorees (deja existantes): {stats['skipped']}")
print(f"Erreurs: {stats['errors']}")

if SIMULATION_MODE:
    print("\nSIMULATION - Aucune modification effectuee")
    print("Pour restaurer reellement:")
    print("  1. Editer ce script")
    print("  2. Mettre SIMULATION_MODE = False")
    print("  3. Relancer le script")
else:
    # Verification post-restauration
    print("\nVerification post-restauration...")
    new_count = db.prices_daily.count_documents({})
    new_dates = sorted(db.prices_daily.distinct('date'))
    
    print(f"\nprices_daily apres restauration:")
    print(f"  Total observations: {new_count:,}")
    print(f"  Dates uniques: {len(new_dates)}")
    if new_dates:
        print(f"  Periode: {new_dates[0]} -> {new_dates[-1]}")
    
    # Jours encore manquants
    curated_dates_set = set(['2025-09-15', '2025-09-16', '2025-09-17', '2025-09-18',
                              '2025-09-19', '2025-09-22', '2025-09-23', '2025-09-24',
                              '2025-09-25', '2025-09-26', '2025-09-29', '2025-09-30',
                              '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-06',
                              '2025-10-07', '2025-10-08', '2025-10-09', '2025-10-10',
                              '2025-10-13', '2025-10-14', '2025-10-15'] + MISSING_DATES + 
                             ['2026-01-07', '2026-01-08', '2026-01-13'])
    still_missing = curated_dates_set - set(new_dates)
    
    if still_missing:
        print(f"\n{len(still_missing)} jours encore manquants:")
        for date in sorted(still_missing)[:10]:
            print(f"    - {date}")
    else:
        print("\nTous les jours ont ete restaures!")

print("\n" + "="*80)
print("Restauration terminee")
print("="*80 + "\n")

# Sauvegarder resultats
with open('RESTAURATION_BRVM_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("RESULTATS DE LA RESTAURATION\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date execution: {datetime.now()}\n")
    f.write(f"Mode: {'SIMULATION' if SIMULATION_MODE else 'EXECUTION REELLE'}\n\n")
    f.write(f"Dates traitees: {stats['processed_dates']}/{len(MISSING_DATES)}\n")
    f.write(f"Observations creees: {stats['created']}\n")
    f.write(f"Observations ignorees: {stats['skipped']}\n")
    f.write(f"Erreurs: {stats['errors']}\n")

print("Rapport sauvegarde: RESTAURATION_BRVM_RESULTS.txt")

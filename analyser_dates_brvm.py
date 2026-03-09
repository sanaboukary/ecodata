#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANALYSER DATES DISPONIBLES DANS curated_observations BRVM
"""
from pymongo import MongoClient
from collections import Counter
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ANALYSE DES DATES DISPONIBLES - DONNEES BRVM")
print("="*80 + "\n")

# Sources à analyser
sources_config = {
    'BRVM_AGGREGATED': 'date',  # Champ date
    'BRVM_CSV_HISTORIQUE': 'ts',  # Champ ts
    'BRVM_CSV_RESTAURATION': 'ts'  # Champ ts
}

all_dates = set()
all_symbols = set()
total_obs = 0

for source, date_field in sources_config.items():
    print(f"\n{'='*80}")
    print(f"SOURCE: {source}")
    print(f"{'='*80}")
    
    # Compter total
    count = db.curated_observations.count_documents({'source': source})
    total_obs += count
    print(f"Total observations: {count:,}")
    
    if count == 0:
        continue
    
    # Extraire dates et symboles
    docs = list(db.curated_observations.find(
        {'source': source},
        {date_field: 1, 'ticker': 1, 'symbole': 1, 'key': 1}
    ))
    
    dates_this_source = set()
    symbols_this_source = set()
    
    for doc in docs:
        # Date
        date_val = doc.get(date_field)
        if date_val:
            # Convertir en string YYYY-MM-DD
            date_str = str(date_val)[:10]
            dates_this_source.add(date_str)
            all_dates.add(date_str)
        
        # Symbole
        symbol = doc.get('ticker') or doc.get('symbole') or doc.get('key', '').split('_')[0]
        if symbol and symbol not in ['BRVM', 'None', '']:
            symbols_this_source.add(symbol)
            all_symbols.add(symbol)
    
    print(f"Dates uniques: {len(dates_this_source)}")
    print(f"Symboles uniques: {len(symbols_this_source)}")
    
    if dates_this_source:
        dates_sorted = sorted(list(dates_this_source))
        print(f"Première date: {dates_sorted[0]}")
        print(f"Dernière date: {dates_sorted[-1]}")
        
        # Compter par mois
        month_counts = Counter()
        for d in dates_sorted:
            month = d[:7]
            month_counts[month] += 1
        
        print(f"\nRépartition par mois:")
        for month in sorted(month_counts.keys()):
            print(f"  {month}: {month_counts[month]:>3} jours")

# SYNTHÈSE GLOBALE
print("\n\n" + "="*80)
print("SYNTHESE GLOBALE - curated_observations")
print("="*80)
print(f"\nTotal observations BRVM: {total_obs:,}")
print(f"Dates uniques: {len(all_dates)}")
print(f"Symboles uniques: {len(all_symbols)}")

if all_dates:
    all_dates_sorted = sorted(list(all_dates))
    print(f"\nPériode complète:")
    print(f"  Première date: {all_dates_sorted[0]}")
    print(f"  Dernière date: {all_dates_sorted[-1]}")
    
    from datetime import datetime
    first = datetime.strptime(all_dates_sorted[0], '%Y-%m-%d')
    last = datetime.strptime(all_dates_sorted[-1], '%Y-%m-%d')
    duration = (last - first).days
    print(f"  Durée: {duration} jours")
    
    # Compter par mois
    month_counts = Counter()
    for d in all_dates_sorted:
        month = d[:7]
        month_counts[month] += 1
    
    print(f"\nRépartition mensuelle globale:")
    for month in sorted(month_counts.keys()):
        print(f"  {month}: {month_counts[month]:>3} jours")

# COMPARAISON AVEC prices_daily
print("\n\n" + "="*80)
print("COMPARAISON avec prices_daily")
print("="*80)

daily_count = db.prices_daily.count_documents({})
daily_dates = sorted(db.prices_daily.distinct('date'))
daily_symbols = db.prices_daily.distinct('symbol')

print(f"\nprices_daily actuel:")
print(f"  Observations: {daily_count:,}")
print(f"  Dates: {len(daily_dates)} jours")
print(f"  Symboles: {len(daily_symbols)}")
if daily_dates:
    print(f"  Période: {daily_dates[0]} -> {daily_dates[-1]}")

# Jours manquants
if all_dates and daily_dates:
    daily_dates_set = set(daily_dates)
    missing_dates = all_dates - daily_dates_set
    extra_dates = daily_dates_set - all_dates
    
    print(f"\nDIFFERENCES:")
    print(f"  Jours dans curated MAIS PAS dans prices_daily: {len(missing_dates)}")
    print(f"  Jours dans prices_daily MAIS PAS dans curated: {len(extra_dates)}")
    
    if missing_dates:
        missing_sorted = sorted(list(missing_dates))
        print(f"\n  JOURS MANQUANTS dans prices_daily (premiers 30):")
        for i, date in enumerate(missing_sorted[:30]):
            print(f"    {i+1:2}. {date}")
        
        if len(missing_sorted) > 30:
            print(f"    ... et {len(missing_sorted) - 30} autres jours")
        
        # Grouper par mois
        missing_months = Counter()
        for d in missing_sorted:
            month = d[:7]
            missing_months[month] += 1
        
        print(f"\n  Jours manquants par mois:")
        for month in sorted(missing_months.keys()):
            print(f"    {month}: {missing_months[month]:>3} jours manquants")

# CONCLUSION
print("\n\n" + "="*80)
print("CONCLUSION")
print("="*80)

if missing_dates and len(missing_dates) > 0:
    print(f"\nOUI - DONNEES RECUPERABLES!")
    print(f"\n  {len(missing_dates)} jours de données sont dans curated_observations")
    print(f"  mais absents de prices_daily")
    print(f"\n  Ces données peuvent être restaurées en:")
    print(f"  1. Extrayant de curated_observations (BRVM_AGGREGATED prioritaire)")
    print(f"  2. Re-créant prices_daily à partir de ces données")
    print(f"  3. Recalculant prices_weekly ensuite")
    
    print(f"\n  PLAN DE RESTAURATION:")
    print(f"  - Créer script de migration curated -> prices_daily")
    print(f"  - Utiliser BRVM_AGGREGATED (format OHLC complet)")
    print(f"  - Compléter avec BRVM_CSV_HISTORIQUE si besoin")
    print(f"  - Restaurer {len(missing_dates)} jours manquants")
else:
    print("\nAucune donnée supplémentaire trouvée dans curated_observations")

print("\n" + "="*80)

# Sauvegarder résultat
with open('ANALYSE_DATES_BRVM.txt', 'w', encoding='utf-8') as f:
    f.write("DATES DISPONIBLES DANS curated_observations\n")
    f.write("="*80 + "\n\n")
    f.write(f"Total observations: {total_obs:,}\n")
    f.write(f"Dates uniques: {len(all_dates)}\n")
    f.write(f"Symboles uniques: {len(all_symbols)}\n\n")
    
    if all_dates:
        f.write(f"Période: {all_dates_sorted[0]} -> {all_dates_sorted[-1]}\n\n")
        f.write("Tous les jours disponibles:\n")
        for date in sorted(all_dates):
            f.write(f"  {date}\n")
    
    if missing_dates:
        f.write(f"\n\nJOURS MANQUANTS dans prices_daily ({len(missing_dates)}):\n")
        for date in sorted(missing_dates):
            f.write(f"  {date}\n")

print("\nRapport sauvegarde: ANALYSE_DATES_BRVM.txt")

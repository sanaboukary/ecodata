#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RECHERCHE RAPIDE DES DONNÉES BRVM PERDUES
"""
from pymongo import MongoClient
from datetime import datetime
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

output = []

def log(msg):
    print(msg)
    output.append(msg)

log("="*80)
log("🔍 RECHERCHE DONNÉES BRVM PERDUES")
log("="*80 + "\n")

# 1. Compter données BRVM dans curated_observations
brvm_sources = ['BRVM', 'BRVM_AGGREGATED', 'BRVM_CSV_HISTORIQUE', 'BRVM_CSV_RESTAURATION']

total_brvm = 0
for source in brvm_sources:
    count = db.curated_observations.count_documents({'source': source})
    total_brvm += count
    if count > 0:
        log(f"Source '{source}': {count:,} observations")

log(f"\nTOTAL curated_observations BRVM: {total_brvm:,}\n")

# 2. État actuel prices_daily
daily_count = db.prices_daily.count_documents({})
daily_dates = sorted(db.prices_daily.distinct('date'))

log(f"prices_daily actuel: {daily_count:,} observations")
if daily_count > 0:
    log(f"Période: {daily_dates[0]} → {daily_dates[-1]}")
    log(f"Jours: {len(daily_dates)}\n")

# 3. Analyser les dates dans curated_observations BRVM
log("Extraction dates depuis curated_observations...")

# Chercher données BRVM avec structure connue
brvm_data = list(db.curated_observations.find(
    {
        'source': {'$in': brvm_sources},
        'attrs.date': {'$exists': True}
    },
    {'attrs.date': 1, 'key': 1, 'source': 1}
).limit(5000))  # Limite pour test

log(f"Trouvé {len(brvm_data):,} observations BRVM avec date\n")

if len(brvm_data) > 0:
    # Parser les dates
    dates_set = set()
    symbols_set = set()
    
    for doc in brvm_data:
        date_str = doc.get('attrs', {}).get('date', '')
        symbol = doc.get('key', '')
        
        if date_str:
            try:
                # Extraire juste YYYY-MM-DD
                date_part = str(date_str)[:10]
                dates_set.add(date_part)
                symbols_set.add(symbol)
            except:
                pass
    
    if dates_set:
        dates_sorted = sorted(list(dates_set))
        log(f"Dates trouvées dans curated_observations:")
        log(f"  Première: {dates_sorted[0]}")
        log(f"  Dernière: {dates_sorted[-1]}")
        log(f"  Total jours: {len(dates_sorted)}")
        log(f"  Symboles: {len(symbols_set)}\n")
        
        # Compter par mois
        month_counts = Counter()
        for date_str in dates_sorted:
            month = date_str[:7]  # YYYY-MM
            month_counts[month] += 1
        
        log("Répartition par mois:")
        for month in sorted(month_counts.keys()):
            log(f"  {month}: {month_counts[month]:>3} jours")
        
        # Jours manquants
        daily_days_set = set(daily_dates)
        missing_days = dates_set - daily_days_set
        
        log(f"\n⚠️  JOURS MANQUANTS dans prices_daily: {len(missing_days)}")
        
        if len(missing_days) > 0:
            missing_sorted = sorted(list(missing_days))
            log("\nPremiers 20 jours manquants:")
            for day in missing_sorted[:20]:
                log(f"  - {day}")
            
            if len(missing_sorted) > 20:
                log(f"  ... et {len(missing_sorted) - 20} autres jours")
            
            log("\n" + "="*80)
            log("✅ DONNEES RECUPERABLES!")
            log("="*80)
            log(f"\n{len(missing_days)} jours de données sont dans curated_observations")
            log("mais absents de prices_daily.")
            log("\nPLAN DE RESTAURATION:")
            log("1. Créer script de migration curated → prices_daily")
            log("2. Restaurer les données jour par jour")
            log("3. Recalculer prices_weekly après restauration")
        else:
            log("\n✅ Aucun jour manquant - données cohérentes")
else:
    log("❌ Aucune donnée BRVM avec date trouvée dans curated_observations")

# Sauvegarder
log("\n" + "="*80)
with open('ANALYSE_DONNEES_PERDUES.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

log("\n✅ Rapport sauvegardé: ANALYSE_DONNEES_PERDUES.txt")

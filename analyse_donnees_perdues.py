#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANALYSE DES DONNÉES BRVM PERDUES - RECHERCHE & RESTAURATION
============================================================
Vérifier si les données octobre-février sont dans curated_observations
"""
from pymongo import MongoClient
from datetime import datetime
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("\n" + "="*80)
print("🔍 RECHERCHE DES DONNÉES BRVM PERDUES (OCTOBRE 2025 → FÉVRIER 2026)")
print("="*80 + "\n")

# ============================================================================
# 1. ANALYSER curated_observations POUR DONNÉES BRVM
# ============================================================================

print("1️⃣ ANALYSE DE curated_observations")
print("-"*80)

# Données BRVM dans curated_observations
brvm_sources = ['BRVM', 'BRVM_AGGREGATED', 'BRVM_CSV_HISTORIQUE', 
                'BRVM_CSV_RESTAURATION', 'AGREGATION_HEBDOMADAIRE']

total_brvm = 0
for source in brvm_sources:
    count = db.curated_observations.count_documents({'source': source})
    total_brvm += count
    if count > 0:
        print(f"\n📊 Source '{source}': {count:,} observations")
        
        # Dates disponibles
        sample_docs = list(db.curated_observations.find(
            {'source': source},
            {'ts': 1, 'attrs': 1, 'key': 1}
        ).limit(5))
        
        if sample_docs:
            print("   Échantillon:")
            for doc in sample_docs[:3]:
                key = doc.get('key', 'N/A')
                ts = doc.get('ts', 'N/A')
                attrs = doc.get('attrs', {})
                date = attrs.get('date', attrs.get('Date', ts))
                print(f"     {key:<10} | Date: {date}")

print(f"\n📈 TOTAL DONNÉES BRVM dans curated_observations: {total_brvm:,}")

# ============================================================================
# 2. VÉRIFIER PÉRIODE OCTOBRE 2025 - FÉVRIER 2026
# ============================================================================

print("\n\n2️⃣ RECHERCHE PÉRIODE OCTOBRE 2025 → FÉVRIER 2026")
print("-"*80)

# Chercher toutes les données BRVM avec dates
pipeline = [
    {'$match': {'source': {'$in': brvm_sources}}},
    {'$project': {
        'key': 1,
        'source': 1,
        'ts': 1,
        'date_field': {
            '$ifNull': [
                '$attrs.date',
                {'$ifNull': ['$attrs.Date', '$ts']}
            ]
        }
    }},
    {'$match': {'date_field': {'$exists': True}}}
]

print("Extraction des dates depuis curated_observations...")
all_brvm_dates = list(db.curated_observations.aggregate(pipeline))
print(f"✓ {len(all_brvm_dates):,} observations BRVM avec dates trouvées")

if len(all_brvm_dates) > 0:
    # Analyser les dates
    dates_list = []
    symbols_set = set()
    
    for doc in all_brvm_dates:
        date_str = str(doc.get('date_field', ''))
        symbol = doc.get('key', 'UNKNOWN')
        
        # Essayer de parser la date
        try:
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
            
            dates_list.append(date_obj)
            symbols_set.add(symbol)
        except:
            pass
    
    if dates_list:
        dates_list.sort()
        print(f"\n📅 PÉRIODE COMPLÈTE TROUVÉE:")
        print(f"   Première date: {dates_list[0].strftime('%Y-%m-%d')}")
        print(f"   Dernière date: {dates_list[-1].strftime('%Y-%m-%d')}")
        print(f"   Durée: {(dates_list[-1] - dates_list[0]).days} jours")
        print(f"   Symboles uniques: {len(symbols_set)}")
        
        # Compter par mois
        month_counts = Counter()
        for d in dates_list:
            month_key = f"{d.year}-{d.month:02d}"
            month_counts[month_key] += 1
        
        print(f"\n📊 RÉPARTITION PAR MOIS:")
        for month in sorted(month_counts.keys()):
            count = month_counts[month]
            print(f"   {month}: {count:>5,} observations")
        
        # Vérifier octobre 2025 - février 2026
        target_months = ['2025-10', '2025-11', '2025-12', '2026-01', '2026-02']
        missing_data = False
        
        print(f"\n🎯 PÉRIODE CIBLÉE (Octobre 2025 → Février 2026):")
        for month in target_months:
            count = month_counts.get(month, 0)
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {month}: {count:>5,} observations")
            if count == 0:
                missing_data = True

# ============================================================================
# 3. COMPARER AVEC prices_daily ACTUEL
# ============================================================================

print("\n\n3️⃣ COMPARAISON curated_observations vs prices_daily")
print("-"*80)

daily_count = db.prices_daily.count_documents({})
daily_dates = sorted(db.prices_daily.distinct('date'))
daily_symbols = db.prices_daily.distinct('symbol')

print(f"\n📊 prices_daily (état actuel):")
print(f"   Total: {daily_count:,} observations")
print(f"   Période: {daily_dates[0]} → {daily_dates[-1]}")
print(f"   Jours: {len(daily_dates)}")
print(f"   Symboles: {len(daily_symbols)}")

print(f"\n📊 curated_observations (données historiques):")
print(f"   Total BRVM: {total_brvm:,} observations")
if len(all_brvm_dates) > 0 and dates_list:
    unique_dates = len(set([d.strftime('%Y-%m-%d') for d in dates_list]))
    print(f"   Jours uniques: {unique_dates}")
    print(f"   Symboles: {len(symbols_set)}")

if len(all_brvm_dates) > 0 and dates_list:
    # Calculer les données manquantes
    curated_days = set([d.strftime('%Y-%m-%d') for d in dates_list])
    daily_days = set(daily_dates)
    
    missing_days = curated_days - daily_days
    
    print(f"\n⚠️  DONNÉES MANQUANTES dans prices_daily:")
    print(f"   {len(missing_days)} jours présents dans curated mais absents de prices_daily")
    
    if len(missing_days) > 0:
        # Trier et afficher les premiers/derniers
        missing_sorted = sorted(list(missing_days))
        print(f"\n   Premiers jours manquants:")
        for day in missing_sorted[:10]:
            print(f"     - {day}")
        
        if len(missing_sorted) > 10:
            print(f"     ... et {len(missing_sorted) - 10} autres jours")

# ============================================================================
# 4. CHERCHER FICHIERS DE BACKUP
# ============================================================================

print("\n\n4️⃣ RECHERCHE DE FICHIERS DE BACKUP/SAUVEGARDE")
print("-"*80)

import os
import glob

# Patterns de fichiers à chercher
patterns = [
    '**/backup*.csv',
    '**/brvm*backup*.csv',
    '**/prices_daily_backup*.csv',
    '**/sauvegarde*.csv',
    '**/restore*.csv',
    '**/*_before_*.csv',
    '**/brvm_cours*.csv'
]

backup_files = []
workspace = os.getcwd()

print(f"\nRecherche dans: {workspace}")
for pattern in patterns:
    try:
        files = glob.glob(pattern, recursive=True)
        if files:
            backup_files.extend(files)
    except:
        pass

if backup_files:
    print(f"\n✅ {len(backup_files)} fichier(s) de backup trouvé(s):")
    for f in backup_files[:20]:  # Limite à 20
        size = os.path.getsize(f) / 1024  # KB
        print(f"   📄 {f} ({size:.1f} KB)")
else:
    print("\n❌ Aucun fichier de backup trouvé")

# ============================================================================
# 5. RECOMMANDATIONS DE RESTAURATION
# ============================================================================

print("\n\n" + "="*80)
print("💡 RECOMMANDATIONS DE RESTAURATION")
print("="*80)

if len(all_brvm_dates) > 0 and dates_list and len(missing_days) > 0:
    print(f"\n✅ BONNE NOUVELLE: {len(missing_days)} jours de données sont RÉCUPÉRABLES!")
    print(f"\n📋 PLAN DE RESTAURATION:")
    print(f"\n   1. SOURCE: curated_observations contient {total_brvm:,} observations BRVM")
    print(f"      - Période complète: {dates_list[0].strftime('%Y-%m-%d')} → {dates_list[-1].strftime('%Y-%m-%d')}")
    print(f"      - {len(symbols_set)} symboles distincts")
    
    print(f"\n   2. ACTION: Reconstruire prices_daily depuis curated_observations")
    print(f"      - Script: brvm_pipeline/pipeline_daily.py --rebuild-from-curated")
    print(f"      - Données à restaurer: {len(missing_days)} jours")
    
    print(f"\n   3. VALIDATION:")
    print(f"      - Vérifier prices_daily après restauration")
    print(f"      - Comparer avec jours attendus: Octobre 2025 → Février 2026")
    
    print(f"\n   4. PRÉVENTION:")
    print(f"      - NE JAMAIS supprimer de prices_daily directement")
    print(f"      - Utiliser flags 'is_outlier' au lieu de supprimer")
    print(f"      - Faire backup avant traitement outliers")

elif total_brvm > 0:
    print(f"\n⚠️  Données BRVM trouvées mais problème de parsing des dates")
    print(f"   - {total_brvm:,} observations BRVM dans curated_observations")
    print(f"   - Vérifier manuellement la structure des données")

else:
    print(f"\n❌ AUCUNE donnée BRVM trouvée dans curated_observations")
    print(f"   - Vérifier d'autres bases MongoDB")
    print(f"   - Chercher fichiers CSV de backup")

print("\n" + "="*80)

# Sauvegarder dans fichier
with open('ANALYSE_DONNEES_PERDUES.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("ANALYSE DES DONNÉES BRVM PERDUES\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date analyse: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write(f"curated_observations: {total_brvm:,} observations BRVM\n")
    f.write(f"prices_daily actuel: {daily_count:,} observations\n\n")
    
    if len(all_brvm_dates) > 0 and dates_list:
        f.write(f"Période dans curated: {dates_list[0].strftime('%Y-%m-%d')} → {dates_list[-1].strftime('%Y-%m-%d')}\n")
        f.write(f"Période dans daily: {daily_dates[0]} → {daily_dates[-1]}\n\n")
        
        if len(missing_days) > 0:
            f.write(f"JOURS MANQUANTS: {len(missing_days)}\n")
            f.write("RÉCUPÉRATION POSSIBLE depuis curated_observations\n\n")
            
            f.write("Jours à restaurer:\n")
            for day in sorted(list(missing_days)):
                f.write(f"  - {day}\n")

print(f"\n✅ Rapport détaillé sauvegardé: ANALYSE_DONNEES_PERDUES.txt\n")

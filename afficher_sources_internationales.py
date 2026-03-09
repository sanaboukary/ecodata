#!/usr/bin/env python3
"""
📊 ÉTAT DES SOURCES INTERNATIONALES (HORS BRVM)
Affiche le détail des données WorldBank, IMF, AfDB, UN SDG
"""

import os
import sys
from datetime import datetime, timedelta
from collections import Counter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "=" * 120)
print("📊 ÉTAT DÉTAILLÉ DES SOURCES INTERNATIONALES")
print("=" * 120)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 120)
print()

# ========== 1. WORLD BANK ==========
print("🌍 1. WORLD BANK - Indicateurs Macroéconomiques")
print("-" * 120)

wb_obs = list(db.curated_observations.find({'source': 'WorldBank'}))
total_wb = len(wb_obs)

if total_wb > 0:
    # Statistiques générales
    dates = [obs.get('ts', '')[:10] for obs in wb_obs if obs.get('ts')]
    dates_sorted = sorted([d for d in dates if d])
    
    premiere_date = dates_sorted[0] if dates_sorted else "N/A"
    derniere_date = dates_sorted[-1] if dates_sorted else "N/A"
    
    # Calculer ancienneté
    if derniere_date != "N/A":
        last_date_obj = datetime.strptime(derniere_date, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        
        if days_old < 30:
            status = f"✅ RÉCENTES ({days_old} jours)"
        elif days_old < 60:
            status = f"⚠️  MOYENNEMENT ANCIENNES ({days_old} jours)"
        else:
            status = f"❌ ANCIENNES ({days_old} jours)"
    else:
        status = "❌ AUCUNE DATE"
        days_old = 0
    
    print(f"Total observations    : {total_wb:,}")
    print(f"Période              : {premiere_date} → {derniere_date}")
    print(f"Ancienneté           : {status}")
    print()
    
    # Répartition par pays
    print("📍 Répartition par pays:")
    pays_count = Counter([obs.get('attrs', {}).get('country', 'N/A') for obs in wb_obs])
    for pays, count in sorted(pays_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_wb * 100)
        print(f"   {pays:4s} : {count:6,} obs ({pct:5.1f}%)")
    print()
    
    # Top 10 indicateurs
    print("📊 Top 10 indicateurs:")
    indicators = Counter([obs.get('dataset', 'N/A') for obs in wb_obs])
    for idx, (indicator, count) in enumerate(indicators.most_common(10), 1):
        pct = (count / total_wb * 100)
        print(f"   {idx:2d}. {indicator:30s} : {count:5,} obs ({pct:5.1f}%)")
    print()
    
    # Données récentes (derniers 30 jours)
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    recent_obs = [obs for obs in wb_obs if obs.get('ts', '')[:10] >= cutoff_date]
    print(f"📅 Observations récentes (< 30 jours) : {len(recent_obs):,}")
    
else:
    print("❌ AUCUNE DONNÉE WORLD BANK")

print()

# ========== 2. IMF ==========
print("💰 2. IMF - Données Monétaires et Financières")
print("-" * 120)

imf_obs = list(db.curated_observations.find({'source': 'IMF'}))
total_imf = len(imf_obs)

if total_imf > 0:
    # Statistiques générales
    dates = [obs.get('ts', '')[:10] for obs in imf_obs if obs.get('ts')]
    dates_sorted = sorted([d for d in dates if d])
    
    premiere_date = dates_sorted[0] if dates_sorted else "N/A"
    derniere_date = dates_sorted[-1] if dates_sorted else "N/A"
    
    # Calculer ancienneté
    if derniere_date != "N/A":
        last_date_obj = datetime.strptime(derniere_date, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        
        if days_old < 30:
            status = f"✅ RÉCENTES ({days_old} jours)"
        elif days_old < 60:
            status = f"⚠️  MOYENNEMENT ANCIENNES ({days_old} jours)"
        else:
            status = f"❌ ANCIENNES ({days_old} jours)"
    else:
        status = "❌ AUCUNE DATE"
        days_old = 0
    
    print(f"Total observations    : {total_imf:,}")
    print(f"Période              : {premiere_date} → {derniere_date}")
    print(f"Ancienneté           : {status}")
    print()
    
    # Répartition par pays
    print("📍 Répartition par zone géographique:")
    areas = Counter([obs.get('key', 'N/A')[:2] if obs.get('key') else 'N/A' for obs in imf_obs])
    for area, count in sorted(areas.items(), key=lambda x: x[1], reverse=True)[:15]:
        pct = (count / total_imf * 100)
        print(f"   {area:4s} : {count:6,} obs ({pct:5.1f}%)")
    print()
    
    # Top séries
    print("📊 Top 10 séries économiques:")
    series = Counter([obs.get('dataset', 'N/A') for obs in imf_obs])
    for idx, (serie, count) in enumerate(series.most_common(10), 1):
        pct = (count / total_imf * 100)
        print(f"   {idx:2d}. {serie:30s} : {count:5,} obs ({pct:5.1f}%)")
    print()
    
    # Données récentes
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    recent_obs = [obs for obs in imf_obs if obs.get('ts', '')[:10] >= cutoff_date]
    print(f"📅 Observations récentes (< 30 jours) : {len(recent_obs):,}")
    
else:
    print("❌ AUCUNE DONNÉE IMF")

print()

# ========== 3. AfDB ==========
print("🏛️  3. AfDB - Banque Africaine de Développement")
print("-" * 120)

afdb_obs = list(db.curated_observations.find({'source': 'AfDB'}))
total_afdb = len(afdb_obs)

if total_afdb > 0:
    # Statistiques générales
    dates = [obs.get('ts', '')[:10] for obs in afdb_obs if obs.get('ts')]
    dates_sorted = sorted([d for d in dates if d])
    
    premiere_date = dates_sorted[0] if dates_sorted else "N/A"
    derniere_date = dates_sorted[-1] if dates_sorted else "N/A"
    
    # Calculer ancienneté
    if derniere_date != "N/A":
        last_date_obj = datetime.strptime(derniere_date, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        
        if days_old < 90:
            status = f"✅ RÉCENTES ({days_old} jours)"
        elif days_old < 180:
            status = f"⚠️  MOYENNEMENT ANCIENNES ({days_old} jours)"
        else:
            status = f"❌ ANCIENNES ({days_old} jours)"
    else:
        status = "❌ AUCUNE DATE"
        days_old = 0
    
    print(f"Total observations    : {total_afdb:,}")
    print(f"Période              : {premiere_date} → {derniere_date}")
    print(f"Ancienneté           : {status}")
    print()
    
    # Répartition par pays
    print("📍 Répartition par pays:")
    countries = Counter([obs.get('key', 'N/A')[:2] if obs.get('key') else 'N/A' for obs in afdb_obs])
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_afdb * 100)
        print(f"   {country:4s} : {count:6,} obs ({pct:5.1f}%)")
    print()
    
    # Top indicateurs
    print("📊 Top 10 indicateurs:")
    indicators = Counter([obs.get('dataset', 'N/A') for obs in afdb_obs])
    for idx, (indicator, count) in enumerate(indicators.most_common(10), 1):
        pct = (count / total_afdb * 100)
        print(f"   {idx:2d}. {indicator:30s} : {count:5,} obs ({pct:5.1f}%)")
    print()
    
    # Données récentes
    cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    recent_obs = [obs for obs in afdb_obs if obs.get('ts', '')[:10] >= cutoff_date]
    print(f"📅 Observations récentes (< 90 jours) : {len(recent_obs):,}")
    
else:
    print("❌ AUCUNE DONNÉE AfDB")

print()

# ========== 4. UN SDG ==========
print("🎯 4. UN SDG - Objectifs de Développement Durable")
print("-" * 120)

un_obs = list(db.curated_observations.find({'source': 'UN_SDG'}))
total_un = len(un_obs)

if total_un > 0:
    # Statistiques générales
    dates = [obs.get('ts', '')[:10] for obs in un_obs if obs.get('ts')]
    dates_sorted = sorted([d for d in dates if d])
    
    premiere_date = dates_sorted[0] if dates_sorted else "N/A"
    derniere_date = dates_sorted[-1] if dates_sorted else "N/A"
    
    # Calculer ancienneté
    if derniere_date != "N/A":
        last_date_obj = datetime.strptime(derniere_date, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        
        if days_old < 90:
            status = f"✅ RÉCENTES ({days_old} jours)"
        elif days_old < 180:
            status = f"⚠️  MOYENNEMENT ANCIENNES ({days_old} jours)"
        else:
            status = f"❌ ANCIENNES ({days_old} jours)"
    else:
        status = "❌ AUCUNE DATE"
        days_old = 0
    
    print(f"Total observations    : {total_un:,}")
    print(f"Période              : {premiere_date} → {derniere_date}")
    print(f"Ancienneté           : {status}")
    print()
    
    # Répartition par pays
    print("📍 Répartition par pays:")
    countries = Counter([obs.get('attrs', {}).get('country', 'N/A') for obs in un_obs])
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_un * 100)
        print(f"   {country:4s} : {count:6,} obs ({pct:5.1f}%)")
    print()
    
    # Top indicateurs ODD
    print("📊 Top 10 indicateurs ODD:")
    indicators = Counter([obs.get('dataset', 'N/A') for obs in un_obs])
    for idx, (indicator, count) in enumerate(indicators.most_common(10), 1):
        pct = (count / total_un * 100)
        print(f"   {idx:2d}. {indicator:30s} : {count:5,} obs ({pct:5.1f}%)")
    print()
    
    # Données récentes
    cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    recent_obs = [obs for obs in un_obs if obs.get('ts', '')[:10] >= cutoff_date]
    print(f"📅 Observations récentes (< 90 jours) : {len(recent_obs):,}")
    
else:
    print("❌ AUCUNE DONNÉE UN SDG")

print()

# ========== RÉSUMÉ GLOBAL ==========
print("=" * 120)
print("📊 RÉSUMÉ GLOBAL - SOURCES INTERNATIONALES")
print("=" * 120)
print()

total_global = total_wb + total_imf + total_afdb + total_un

print(f"Source               Total Obs      % du Total")
print("-" * 60)
print(f"🌍 World Bank      : {total_wb:10,}    ({total_wb/total_global*100:5.1f}%)" if total_global > 0 else "🌍 World Bank      :          0    (  0.0%)")
print(f"💰 IMF             : {total_imf:10,}    ({total_imf/total_global*100:5.1f}%)" if total_global > 0 else "💰 IMF             :          0    (  0.0%)")
print(f"🏛️  AfDB            : {total_afdb:10,}    ({total_afdb/total_global*100:5.1f}%)" if total_global > 0 else "🏛️  AfDB            :          0    (  0.0%)")
print(f"🎯 UN SDG          : {total_un:10,}    ({total_un/total_global*100:5.1f}%)" if total_global > 0 else "🎯 UN SDG          :          0    (  0.0%)")
print("-" * 60)
print(f"{'TOTAL':17s}: {total_global:10,}    (100.0%)")

print()
print("=" * 120)
print("📋 RECOMMANDATIONS")
print("=" * 120)
print()

recommandations = []

# World Bank
if total_wb == 0:
    recommandations.append(("🔴 URGENT", "World Bank", "Aucune donnée - Lancer collecte initiale"))
elif derniere_date != "N/A":
    last_date_obj = datetime.strptime(derniere_date, '%Y-%m-%d')
    days_old = (datetime.now() - last_date_obj).days
    if days_old > 60:
        recommandations.append(("🟠 HAUTE", "World Bank", f"Données anciennes ({days_old}j) - Mettre à jour"))
    elif days_old > 30:
        recommandations.append(("🟡 MOYENNE", "World Bank", f"Mise à jour recommandée ({days_old}j)"))

# IMF
if total_imf == 0:
    recommandations.append(("🔴 URGENT", "IMF", "Aucune donnée - Lancer collecte initiale"))
elif 'derniere_date' in dir() and derniere_date != "N/A":
    imf_dates = [obs.get('ts', '')[:10] for obs in imf_obs if obs.get('ts')]
    if imf_dates:
        last_imf = sorted(imf_dates)[-1]
        last_date_obj = datetime.strptime(last_imf, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        if days_old > 60:
            recommandations.append(("🟠 HAUTE", "IMF", f"Données anciennes ({days_old}j) - Mettre à jour"))
        elif days_old > 30:
            recommandations.append(("🟡 MOYENNE", "IMF", f"Mise à jour recommandée ({days_old}j)"))

# AfDB
if total_afdb == 0:
    recommandations.append(("🔴 URGENT", "AfDB", "Aucune donnée - Lancer collecte initiale"))
elif afdb_obs:
    afdb_dates = [obs.get('ts', '')[:10] for obs in afdb_obs if obs.get('ts')]
    if afdb_dates:
        last_afdb = sorted(afdb_dates)[-1]
        last_date_obj = datetime.strptime(last_afdb, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        if days_old > 180:
            recommandations.append(("🟠 HAUTE", "AfDB", f"Données très anciennes ({days_old}j) - Mettre à jour"))
        elif days_old > 90:
            recommandations.append(("🟡 MOYENNE", "AfDB", f"Mise à jour recommandée ({days_old}j)"))

# UN SDG
if total_un == 0:
    recommandations.append(("🔴 URGENT", "UN SDG", "Aucune donnée - Lancer collecte initiale"))
elif un_obs:
    un_dates = [obs.get('ts', '')[:10] for obs in un_obs if obs.get('ts')]
    if un_dates:
        last_un = sorted(un_dates)[-1]
        last_date_obj = datetime.strptime(last_un, '%Y-%m-%d')
        days_old = (datetime.now() - last_date_obj).days
        if days_old > 180:
            recommandations.append(("🟠 HAUTE", "UN SDG", f"Données très anciennes ({days_old}j) - Mettre à jour"))
        elif days_old > 90:
            recommandations.append(("🟡 MOYENNE", "UN SDG", f"Mise à jour recommandée ({days_old}j)"))

if recommandations:
    priorites = {"🔴 URGENT": 1, "🟠 HAUTE": 2, "🟡 MOYENNE": 3, "🟢 BASSE": 4}
    recommandations_sorted = sorted(recommandations, key=lambda x: priorites.get(x[0], 99))
    
    for prio, source, action in recommandations_sorted:
        print(f"{prio:12s} {source:15s} → {action}")
else:
    print("🟢 Toutes les sources sont à jour !")

print()
print("=" * 120)
print()
print("📋 COMMANDES UTILES:")
print()
print("   Mise à jour manuelle:")
print("   ├─ python mettre_a_jour_toutes_sources.py")
print("   └─ METTRE_A_JOUR_SOURCES.cmd")
print()
print("   Dashboard:")
print("   └─ http://127.0.0.1:8000/")
print()
print("=" * 120)
print()

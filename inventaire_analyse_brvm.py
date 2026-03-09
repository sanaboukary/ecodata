#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INVENTAIRE COMPLET BRVM + ANALYSE DOUBLE OBJECTIF
================================================

Objectif 1: TOP5 Hebdomadaire (≥60% présence dans TOP5 officiel BRVM)
Objectif 2: Opportunités J+1 à J+7 (≥40% conversion)
"""
from pymongo import MongoClient
from collections import Counter
from datetime import datetime, timedelta
import sys
import io

# Capture output to file
output_file = 'INVENTAIRE_BRVM_RESULTAT.txt'
original_stdout = sys.stdout
sys.stdout = io.TextIOWrapper(open(output_file, 'w', encoding='utf-8'), encoding='utf-8', line_buffering=True)

# Also print to console
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

sys.stdout = Tee(sys.stdout, original_stdout)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("\n" + "="*80)
print("📊 INVENTAIRE COMPLET DES DONNÉES BRVM")
print("="*80 + "\n")

# ============================================================================
# 1. ARCHITECTURE 3 NIVEAUX (RAW → DAILY → WEEKLY)
# ============================================================================

print("1️⃣ ARCHITECTURE DES DONNÉES")
print("-"*80)

# RAW
raw_count = db.prices_intraday_raw.count_documents({})
print(f"\n🔴 RAW (prices_intraday_raw) : {raw_count:,} observations")
if raw_count > 0:
    raw_dates = sorted(db.prices_intraday_raw.distinct('date'))
    raw_symbols = db.prices_intraday_raw.distinct('symbol')
    print(f"   Période: {raw_dates[0]} → {raw_dates[-1]} ({len(raw_dates)} dates)")
    print(f"   Symboles: {len(raw_symbols)} actions")
    print(f"   Sessions collectées: {db.prices_intraday_raw.distinct('session_id').__len__()}")

# DAILY
daily_count = db.prices_daily.count_documents({})
print(f"\n🟢 DAILY (prices_daily) : {daily_count:,} observations")
if daily_count > 0:
    daily_dates = sorted(db.prices_daily.distinct('date'))
    daily_symbols = db.prices_daily.distinct('symbol')
    complete_ohlc = db.prices_daily.count_documents({'is_complete': True})
    
    print(f"   Période: {daily_dates[0]} → {daily_dates[-1]}")
    print(f"   Jours uniques: {len(daily_dates)} jours")
    print(f"   Symboles: {len(daily_symbols)} actions")
    print(f"   OHLC complet: {complete_ohlc}/{daily_count} ({complete_ohlc/daily_count*100:.1f}%)")
    
    # Top 5 actions avec plus de données
    print(f"\n   TOP 5 actions (plus de jours de cotation):")
    pipeline = [
        {"$group": {"_id": "$symbol", "jours": {"$sum": 1}}},
        {"$sort": {"jours": -1}},
        {"$limit": 5}
    ]
    for item in db.prices_daily.aggregate(pipeline):
        print(f"     {item['_id']:<10} : {item['jours']:>2} jours")

# WEEKLY
weekly_count = db.prices_weekly.count_documents({})
print(f"\n🔵 WEEKLY (prices_weekly) : {weekly_count:,} observations")
if weekly_count > 0:
    weekly_weeks = sorted(db.prices_weekly.distinct('week'))
    weekly_symbols = db.prices_weekly.distinct('symbol')
    with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    
    print(f"   Semaines: {weekly_weeks[0]} → {weekly_weeks[-1]}")
    print(f"   Semaines uniques: {len(weekly_weeks)}")
    print(f"   Liste: {', '.join(weekly_weeks)}")
    print(f"   Symboles: {len(weekly_symbols)} actions")
    print(f"   Avec indicateurs: {with_indicators}/{weekly_count} ({with_indicators/weekly_count*100:.1f}%)")

# ============================================================================
# 2. OBJECTIF 1 : TOP5 HEBDOMADAIRE
# ============================================================================

print("\n\n" + "="*80)
print("🎯 OBJECTIF 1 : TOP5 HEBDOMADAIRE")
print("="*80)
print("Cible: Être dans le TOP5 officiel BRVM ≥60% du temps")
print("Formule: 30% Expected_Return + 25% Volume + 20% Semantic + 15% WOS + 10% RR")
print("-"*80)

# État actuel TOP5
top5_count = db.top5_weekly_brvm.count_documents({})
print(f"\n📈 TOP5 générés : {top5_count} semaines")

if top5_count > 0:
    top5_weeks = sorted(db.top5_weekly_brvm.distinct('week'))
    print(f"   Semaines avec TOP5: {', '.join(top5_weeks)}")
    
    # Dernière génération
    last_top5 = list(db.top5_weekly_brvm.find({}).sort('week', -1).limit(1))
    if last_top5:
        print(f"\n   Dernière génération: {last_top5[0].get('week')}")
        
    # Actions récurrentes dans TOP5
    all_top5 = list(db.top5_weekly_brvm.find({}))
    symbol_counts = Counter([doc.get('symbol') for doc in all_top5])
    print(f"\n   Actions les plus fréquentes dans TOP5:")
    for symbol, count in symbol_counts.most_common(5):
        print(f"     {symbol:<10} : {count} fois")

# Évaluation capacité actuelle
print(f"\n⚠️  ÉVALUATION CAPACITÉ:")

required_weeks = 14  # Pour RSI(14) en production
available_weeks = len(weekly_weeks) if weekly_count > 0 else 0
startup_mode = available_weeks < required_weeks

if startup_mode:
    print(f"   MODE DÉMARRAGE activé ({available_weeks}/{required_weeks} semaines)")
    print(f"   - Indicateurs calculés: {with_indicators}/{weekly_count}")
    print(f"   - Formule adaptée: RSI(5), ATR(5), SMA(3/5)")
    print(f"   - ⚠️ Manque {required_weeks - available_weeks} semaines pour mode PRODUCTION")
else:
    print(f"   MODE PRODUCTION possible ({available_weeks}/{required_weeks} semaines)")
    print(f"   - Indicateurs complets disponibles")
    print(f"   - Calibration BRVM complète: RSI(14), ATR(8), SMA(5/10)")

# Données manquantes pour TOP5
print(f"\n📊 DONNÉES POUR TOP5:")
print(f"   ✓ Prix hebdomadaires: {weekly_count} observations")
print(f"   ✓ Indicateurs techniques: {with_indicators} calculés")

# Vérifier données sémantiques
semantic_count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'})
print(f"   {'✓' if semantic_count > 0 else '✗'} Données sémantiques: {semantic_count} publications")

# Vérifier WOS setups
# TODO: Vérifier collection wos_setups ou indicateurs WOS

# ============================================================================
# 3. OBJECTIF 2 : OPPORTUNITÉS J+1 à J+7
# ============================================================================

print("\n\n" + "="*80)
print("🔍 OBJECTIF 2 : OPPORTUNITÉS (J+1 à J+7)")
print("="*80)
print("Cible: Détecter opportunités ≥40% de conversion")
print("Formule: 35% Volume + 30% Semantic + 20% Volatility + 15% Sector")
print("Détecteurs: News Silencieuse, Volume Anormal, Rupture Sommeil, Retard Secteur")
print("-"*80)

# État actuel Opportunités
opp_count = db.opportunities_brvm.count_documents({})
print(f"\n🎲 Opportunités détectées : {opp_count}")

if opp_count > 0:
    opp_dates = sorted(db.opportunities_brvm.distinct('detection_date'))
    print(f"   Période: {opp_dates[0]} → {opp_dates[-1]}")
    
    # Par détecteur
    detectors = db.opportunities_brvm.distinct('detector')
    print(f"\n   Détecteurs actifs:")
    for detector in detectors:
        count = db.opportunities_brvm.count_documents({'detector': detector})
        print(f"     {detector:<25} : {count} détections")
    
    # Symboles avec opportunités
    opp_symbols = db.opportunities_brvm.distinct('symbol')
    print(f"\n   Symboles avec opportunités: {len(opp_symbols)}")
else:
    print("   ⚠️ Aucune opportunité détectée pour le moment")

# Évaluation capacité
print(f"\n⚠️  ÉVALUATION CAPACITÉ:")
print(f"   Données DAILY: {daily_count:,} observations sur {len(daily_dates) if daily_count > 0 else 0} jours")

if daily_count > 0 and len(daily_dates) >= 7:
    print(f"   ✓ Historique suffisant pour détection J-7")
    print(f"   ✓ Peut détecter ruptures de patterns")
else:
    print(f"   ✗ Historique insuffisant (besoin 7+ jours)")

# Données nécessaires pour opportunités
print(f"\n📊 DONNÉES POUR OPPORTUNITÉS:")
print(f"   {'✓' if daily_count > 0 else '✗'} Prix quotidiens: {daily_count:,}")
print(f"   {'✓' if semantic_count > 0 else '✗'} Publications: {semantic_count}")

# Volume anormal
volume_data = db.prices_daily.count_documents({'volume': {'$exists': True, '$gt': 0}})
print(f"   {'✓' if volume_data > 0 else '✗'} Données volume: {volume_data}/{daily_count}")

# ============================================================================
# 4. SYNTHÈSE & RECOMMANDATIONS
# ============================================================================

print("\n\n" + "="*80)
print("📋 SYNTHÈSE GÉNÉRALE")
print("="*80)

total_data = raw_count + daily_count + weekly_count
print(f"\nDONNÉES TOTALES: {total_data:,} observations BRVM")
print(f"  - RAW:    {raw_count:>6,} ({raw_count/total_data*100:.1f}%)" if total_data > 0 else "")
print(f"  - DAILY:  {daily_count:>6,} ({daily_count/total_data*100:.1f}%)" if total_data > 0 else "")
print(f"  - WEEKLY: {weekly_count:>6,} ({weekly_count/total_data*100:.1f}%)" if total_data > 0 else "")

print(f"\n🎯 OBJECTIF TOP5:")
if with_indicators > 0 and weekly_count > 0:
    readiness = min(100, (available_weeks / required_weeks) * 100)
    print(f"   Prêt à: {readiness:.0f}%")
    if readiness >= 100:
        print(f"   ✅ Peut générer TOP5 avec calibration complète")
    else:
        print(f"   ⚠️  Mode démarrage ({available_weeks}/{required_weeks} semaines)")
        print(f"   ⏳ Besoin {required_weeks - available_weeks} semaines supplémentaires")
else:
    print(f"   ❌ Pas de données WEEKLY avec indicateurs")
    print(f"   Action: Lancer pipeline_weekly.py --rebuild")

print(f"\n🔍 OBJECTIF OPPORTUNITÉS:")
if daily_count >= 100 and len(daily_dates) >= 7:
    print(f"   ✅ Données suffisantes pour détecter opportunités")
    print(f"   Action: Lancer opportunity_engine.py")
else:
    need_more = max(0, 7 - len(daily_dates)) if daily_count > 0 else 7
    print(f"   ⏳ Besoin {need_more} jours supplémentaires minimum")
    print(f"   Action: Continuer collecte quotidienne")

print("\n" + "="*80)
print("🚀 PROCHAINES ÉTAPES")
print("="*80)

steps = []

# Étape 1: Collecte
if len(daily_dates) < 30 if daily_count > 0 else True:
    steps.append("1. COLLECTE: Activer collecte quotidienne automatique (cron 17h)")

# Étape 2: Pipeline WEEKLY
if with_indicators < weekly_count:
    steps.append("2. INDICATEURS: Calculer indicateurs manquants (pipeline_weekly.py --indicators)")

# Étape 3: TOP5
if available_weeks >= 5:
    steps.append("3. TOP5: Générer recommandations hebdo (top5_engine.py --week 2026-W02)")
else:
    steps.append("3. TOP5: Attendre 14 semaines pour calibration complète")

# Étape 4: Opportunités
if daily_count >= 100:
    steps.append("4. OPPORTUNITÉS: Activer détection (opportunity_engine.py)")
else:
    steps.append("4. OPPORTUNITÉS: Accumuler historique (besoin 100+ obs)")

# Étape 5: Production
steps.append("5. PRODUCTION: Scheduler workflows (daily 17h, weekly lundi 8h)")

for step in steps:
    print(f"\n   {step}")

print("\n" + "="*80 + "\n")

# ============================================================================
# 5. DÉTAILS TECHNIQUES
# ============================================================================

print("\n📊 DÉTAILS TECHNIQUES")
print("-"*80)

print(f"\nINDICATEURS CALCULÉS (échantillon):")
sample = db.prices_weekly.find_one({'indicators_computed': True})
if sample:
    print(f"  Symbole: {sample.get('symbol')} - Semaine: {sample.get('week')}")
    print(f"  - RSI: {sample.get('rsi', 'N/A')}")
    print(f"  - ATR%: {sample.get('atr_pct', 'N/A')}")
    print(f"  - SMA5: {sample.get('sma5', 'N/A')}")
    print(f"  - SMA10: {sample.get('sma10', 'N/A')}")
    print(f"  - Trend: {sample.get('trend', 'N/A')}")
    print(f"  - Volume ratio: {sample.get('volume_ratio', 'N/A')}")
else:
    print("  Aucun indicateur calculé pour le moment")

print(f"\nQUALITÉ DES DONNÉES:")
if daily_count > 0:
    # Complétude
    with_close = db.prices_daily.count_documents({'close': {'$exists': True}})
    with_volume = db.prices_daily.count_documents({'volume': {'$exists': True, '$gt': 0}})
    
    print(f"  - Prix close: {with_close}/{daily_count} ({with_close/daily_count*100:.1f}%)")
    print(f"  - Volume: {with_volume}/{daily_count} ({with_volume/daily_count*100:.1f}%)")
    print(f"  - OHLC complet: {complete_ohlc}/{daily_count} ({complete_ohlc/daily_count*100:.1f}%)")

print("\n" + "="*80 + "\n")

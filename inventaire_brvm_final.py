#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INVENTAIRE COMPLET BRVM + ANALYSE DOUBLE OBJECTIF
================================================
"""
from pymongo import MongoClient
from collections import Counter
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Open output file
with open('INVENTAIRE_BRVM_RESULTAT.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("📊 INVENTAIRE COMPLET DES DONNÉES BRVM\n")
    f.write("="*80 + "\n\n")
    
    # ========================================================================
    # 1. ARCHITECTURE 3 NIVEAUX (RAW → DAILY → WEEKLY)
    # ========================================================================
    
    f.write("1️⃣ ARCHITECTURE DES DONNÉES\n")
    f.write("-"*80 + "\n")
    
    # RAW
    raw_count = db.prices_intraday_raw.count_documents({})
    f.write(f"\n🔴 RAW (prices_intraday_raw) : {raw_count:,} observations\n")
    if raw_count > 0:
        raw_dates = sorted(db.prices_intraday_raw.distinct('date'))
        raw_symbols = db.prices_intraday_raw.distinct('symbol')
        raw_sessions = len(db.prices_intraday_raw.distinct('session_id'))
        f.write(f"   Période: {raw_dates[0]} → {raw_dates[-1]} ({len(raw_dates)} dates)\n")
        f.write(f"   Symboles: {len(raw_symbols)} actions\n")
        f.write(f"   Sessions collectées: {raw_sessions}\n")
    
    # DAILY
    daily_count = db.prices_daily.count_documents({})
    f.write(f"\n🟢 DAILY (prices_daily) : {daily_count:,} observations\n")
    daily_dates = []
    daily_symbols = []
    if daily_count > 0:
        daily_dates = sorted(db.prices_daily.distinct('date'))
        daily_symbols = db.prices_daily.distinct('symbol')
        complete_ohlc = db.prices_daily.count_documents({'is_complete': True})
        
        f.write(f"   Période: {daily_dates[0]} → {daily_dates[-1]}\n")
        f.write(f"   Jours uniques: {len(daily_dates)} jours\n")
        f.write(f"   Symboles: {len(daily_symbols)} actions\n")
        f.write(f"   OHLC complet: {complete_ohlc}/{daily_count} ({complete_ohlc/daily_count*100:.1f}%)\n")
        
        # Top 5 actions
        f.write(f"\n   TOP 5 actions (plus de jours de cotation):\n")
        pipeline = [
            {"$group": {"_id": "$symbol", "jours": {"$sum": 1}}},
            {"$sort": {"jours": -1}},
            {"$limit": 5}
        ]
        for item in db.prices_daily.aggregate(pipeline):
            f.write(f"     {item['_id']:<10} : {item['jours']:>2} jours\n")
    
    # WEEKLY
    weekly_count = db.prices_weekly.count_documents({})
    f.write(f"\n🔵 WEEKLY (prices_weekly) : {weekly_count:,} observations\n")
    weekly_weeks = []
    weekly_symbols = []
    with_indicators = 0
    available_weeks = 0
    
    if weekly_count > 0:
        weekly_weeks = sorted(db.prices_weekly.distinct('week'))
        weekly_symbols = db.prices_weekly.distinct('symbol')
        with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
        available_weeks = len(weekly_weeks)
        
        f.write(f"   Semaines: {weekly_weeks[0]} → {weekly_weeks[-1]}\n")
        f.write(f"   Semaines uniques: {len(weekly_weeks)}\n")
        f.write(f"   Liste: {', '.join(weekly_weeks)}\n")
        f.write(f"   Symboles: {len(weekly_symbols)} actions\n")
        f.write(f"   Avec indicateurs: {with_indicators}/{weekly_count} ({with_indicators/weekly_count*100:.1f}%)\n")
    
    # ========================================================================
    # 2. OBJECTIF 1 : TOP5 HEBDOMADAIRE
    # ========================================================================
    
    f.write("\n\n" + "="*80 + "\n")
    f.write("🎯 OBJECTIF 1 : TOP5 HEBDOMADAIRE\n")
    f.write("="*80 + "\n")
    f.write("Cible: Être dans le TOP5 officiel BRVM ≥60% du temps\n")
    f.write("Formule: 30% Expected_Return + 25% Volume + 20% Semantic + 15% WOS + 10% RR\n")
    f.write("-"*80 + "\n")
    
    # État actuel TOP5
    top5_count = db.top5_weekly_brvm.count_documents({})
    f.write(f"\n📈 TOP5 générés : {top5_count} semaines\n")
    
    if top5_count > 0:
        top5_weeks = sorted([w for w in db.top5_weekly_brvm.distinct('week') if w])  # Filter None
        if top5_weeks:
            f.write(f"   Semaines avec TOP5: {', '.join(top5_weeks)}\n")
        
        # Dernière génération
        last_top5 = list(db.top5_weekly_brvm.find({'week': {'$ne': None}}).sort('week', -1).limit(1))
        if last_top5:
            f.write(f"\n   Dernière génération: {last_top5[0].get('week')}\n")
            
        # Actions récurrentes
        all_top5 = list(db.top5_weekly_brvm.find({'symbol': {'$ne': None}}))
        symbol_counts = Counter([doc.get('symbol') for doc in all_top5 if doc.get('symbol')])
        if symbol_counts:
            f.write(f"\n   Actions les plus fréquentes dans TOP5:\n")
            for symbol, count in symbol_counts.most_common(5):
                f.write(f"     {symbol:<10} : {count} fois\n")
    
    # Évaluation capacité
    f.write(f"\n⚠️  ÉVALUATION CAPACITÉ:\n")
    
    required_weeks = 14
    startup_mode = available_weeks < required_weeks
    
    if startup_mode:
        f.write(f"   MODE DÉMARRAGE activé ({available_weeks}/{required_weeks} semaines)\n")
        f.write(f"   - Indicateurs calculés: {with_indicators}/{weekly_count}\n")
        f.write(f"   - Formule adaptée: RSI(5), ATR(5), SMA(3/5)\n")
        f.write(f"   - ⚠️ Manque {required_weeks - available_weeks} semaines pour mode PRODUCTION\n")
    else:
        f.write(f"   MODE PRODUCTION possible ({available_weeks}/{required_weeks} semaines)\n")
        f.write(f"   - Indicateurs complets disponibles\n")
        f.write(f"   - Calibration BRVM complète: RSI(14), ATR(8), SMA(5/10)\n")
    
    # Données pour TOP5
    f.write(f"\n📊 DONNÉES POUR TOP5:\n")
    f.write(f"   ✓ Prix hebdomadaires: {weekly_count} observations\n")
    f.write(f"   ✓ Indicateurs techniques: {with_indicators} calculés\n")
    
    semantic_count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'})
    f.write(f"   {'✓' if semantic_count > 0 else '✗'} Données sémantiques: {semantic_count} publications\n")
    
    # ========================================================================
    # 3. OBJECTIF 2 : OPPORTUNITÉS J+1 à J+7
    # ========================================================================
    
    f.write("\n\n" + "="*80 + "\n")
    f.write("🔍 OBJECTIF 2 : OPPORTUNITÉS (J+1 à J+7)\n")
    f.write("="*80 + "\n")
    f.write("Cible: Détecter opportunités ≥40% de conversion\n")
    f.write("Formule: 35% Volume + 30% Semantic + 20% Volatility + 15% Sector\n")
    f.write("Détecteurs: News Silencieuse, Volume Anormal, Rupture Sommeil, Retard Secteur\n")
    f.write("-"*80 + "\n")
    
    # Opportunités
    opp_count = db.opportunities_brvm.count_documents({})
    f.write(f"\n🎲 Opportunités détectées : {opp_count}\n")
    
    if opp_count > 0:
        opp_dates = sorted([d for d in db.opportunities_brvm.distinct('detection_date') if d])
        if opp_dates:
            f.write(f"   Période: {opp_dates[0]} → {opp_dates[-1]}\n")
        
        detectors = [d for d in db.opportunities_brvm.distinct('detector') if d]
        if detectors:
            f.write(f"\n   Détecteurs actifs:\n")
            for detector in detectors:
                count = db.opportunities_brvm.count_documents({'detector': detector})
                f.write(f"     {detector:<25} : {count} détections\n")
        
        opp_symbols = [s for s in db.opportunities_brvm.distinct('symbol') if s]
        f.write(f"\n   Symboles avec opportunités: {len(opp_symbols)}\n")
    else:
        f.write("   ⚠️ Aucune opportunité détectée pour le moment\n")
    
    # Évaluation
    f.write(f"\n⚠️  ÉVALUATION CAPACITÉ:\n")
    f.write(f"   Données DAILY: {daily_count:,} observations sur {len(daily_dates)} jours\n")
    
    if daily_count > 0 and len(daily_dates) >= 7:
        f.write(f"   ✓ Historique suffisant pour détection J-7\n")
        f.write(f"   ✓ Peut détecter ruptures de patterns\n")
    else:
        f.write(f"   ✗ Historique insuffisant (besoin 7+ jours)\n")
    
    # Données nécessaires
    f.write(f"\n📊 DONNÉES POUR OPPORTUNITÉS:\n")
    f.write(f"   {'✓' if daily_count > 0 else '✗'} Prix quotidiens: {daily_count:,}\n")
    f.write(f"   {'✓' if semantic_count > 0 else '✗'} Publications: {semantic_count}\n")
    
    volume_data = db.prices_daily.count_documents({'volume': {'$exists': True, '$gt': 0}})
    f.write(f"   {'✓' if volume_data > 0 else '✗'} Données volume: {volume_data}/{daily_count}\n")
    
    # ========================================================================
    # 4. SYNTHÈSE & RECOMMANDATIONS
    # ========================================================================
    
    f.write("\n\n" + "="*80 + "\n")
    f.write("📋 SYNTHÈSE GÉNÉRALE\n")
    f.write("="*80 + "\n")
    
    total_data = raw_count + daily_count + weekly_count
    f.write(f"\nDONNÉES TOTALES: {total_data:,} observations BRVM\n")
    if total_data > 0:
        f.write(f"  - RAW:    {raw_count:>6,} ({raw_count/total_data*100:.1f}%)\n")
        f.write(f"  - DAILY:  {daily_count:>6,} ({daily_count/total_data*100:.1f}%)\n")
        f.write(f"  - WEEKLY: {weekly_count:>6,} ({weekly_count/total_data*100:.1f}%)\n")
    
    f.write(f"\n🎯 OBJECTIF TOP5:\n")
    if with_indicators > 0 and weekly_count > 0:
        readiness = min(100, (available_weeks / required_weeks) * 100)
        f.write(f"   Prêt à: {readiness:.0f}%\n")
        if readiness >= 100:
            f.write(f"   ✅ Peut générer TOP5 avec calibration complète\n")
        else:
            f.write(f"   ⚠️  Mode démarrage ({available_weeks}/{required_weeks} semaines)\n")
            f.write(f"   ⏳ Besoin {required_weeks - available_weeks} semaines supplémentaires\n")
    else:
        f.write(f"   ❌ Pas de données WEEKLY avec indicateurs\n")
        f.write(f"   Action: Lancer pipeline_weekly.py --rebuild\n")
    
    f.write(f"\n🔍 OBJECTIF OPPORTUNITÉS:\n")
    if daily_count >= 100 and len(daily_dates) >= 7:
        f.write(f"   ✅ Données suffisantes pour détecter opportunités\n")
        f.write(f"   Action: Lancer opportunity_engine.py\n")
    else:
        need_more = max(0, 7 - len(daily_dates)) if daily_count > 0 else 7
        f.write(f"   ⏳ Besoin {need_more} jours supplémentaires minimum\n")
        f.write(f"   Action: Continuer collecte quotidienne\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("🚀 PROCHAINES ÉTAPES\n")
    f.write("="*80 + "\n")
    
    steps = []
    
    if len(daily_dates) < 30 if daily_count > 0 else True:
        steps.append("1. COLLECTE: Activer collecte quotidienne automatique (cron 17h)")
    
    if with_indicators < weekly_count:
        steps.append("2. INDICATEURS: Calculer indicateurs manquants (pipeline_weekly.py --indicators)")
    
    if available_weeks >= 5:
        steps.append("3. TOP5: Générer recommandations hebdo (top5_engine.py --week 2026-W07)")
    else:
        steps.append("3. TOP5: Attendre 14 semaines pour calibration complète")
    
    if daily_count >= 100:
        steps.append("4. OPPORTUNITÉS: Activer détection (opportunity_engine.py)")
    else:
        steps.append("4. OPPORTUNITÉS: Accumuler historique (besoin 100+ obs)")
    
    steps.append("5. PRODUCTION: Scheduler workflows (daily 17h, weekly lundi 8h)")
    
    for step in steps:
        f.write(f"\n   {step}")
    
    f.write("\n\n" + "="*80 + "\n")
    
    # ========================================================================
    # 5. DÉTAILS TECHNIQUES
    # ========================================================================
    
    f.write("\n📊 DÉTAILS TECHNIQUES\n")
    f.write("-"*80 + "\n")
    
    f.write(f"\nINDICATEURS CALCULÉS (échantillon):\n")
    sample = db.prices_weekly.find_one({'indicators_computed': True})
    if sample:
        f.write(f"  Symbole: {sample.get('symbol')} - Semaine: {sample.get('week')}\n")
        f.write(f"  - RSI: {sample.get('rsi', 'N/A')}\n")
        f.write(f"  - ATR%: {sample.get('atr_pct', 'N/A')}\n")
        f.write(f"  - SMA5: {sample.get('sma5', 'N/A')}\n")
        f.write(f"  - SMA10: {sample.get('sma10', 'N/A')}\n")
        f.write(f"  - Trend: {sample.get('trend', 'N/A')}\n")
        f.write(f"  - Volume ratio: {sample.get('volume_ratio', 'N/A')}\n")
    else:
        f.write("  Aucun indicateur calculé pour le moment\n")
    
    f.write(f"\nQUALITÉ DES DONNÉES:\n")
    if daily_count > 0:
        with_close = db.prices_daily.count_documents({'close': {'$exists': True}})
        with_volume = db.prices_daily.count_documents({'volume': {'$exists': True, '$gt': 0}})
        
        f.write(f"  - Prix close: {with_close}/{daily_count} ({with_close/daily_count*100:.1f}%)\n")
        f.write(f"  - Volume: {with_volume}/{daily_count} ({with_volume/daily_count*100:.1f}%)\n")
        if complete_ohlc:
            f.write(f"  - OHLC complet: {complete_ohlc}/{daily_count} ({complete_ohlc/daily_count*100:.1f}%)\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write(f"\n✅ Rapport généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"📄 Fichier: INVENTAIRE_BRVM_RESULTAT.txt\n\n")

print("✅ Inventaire généré dans INVENTAIRE_BRVM_RESULTAT.txt")

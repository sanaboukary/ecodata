#!/usr/bin/env python3
"""
📊 DASHBOARD OPPORTUNITÉS BRVM

Suivi des opportunités détectées et leur conversion

MÉTRIQUES CLÉS :
1. Opportunités du jour (FORTE + OBSERVATION)
2. Opportunités → TOP5 (conversion)
3. Taux de conversion sur 12 semaines
4. Délai moyen détection → TOP5

RÈGLE :
Les meilleurs trades commencent par une opportunité détectée 3-7 jours avant.
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import math

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# COLLECTIONS
# ============================================================================

COLLECTION_OPPORTUNITIES = "opportunities_brvm"
COLLECTION_TOP5 = "top5_weekly_brvm"
COLLECTION_DAILY = "prices_daily"

# ============================================================================
# OPPORTUNITÉS DU JOUR
# ============================================================================

def show_today_opportunities(date=None):
    """Afficher opportunités détectées aujourd'hui"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("\n" + "="*100)
    print(f"📊 OPPORTUNITÉS DÉTECTÉES - {date}")
    print("="*100 + "\n")
    
    opps = list(db[COLLECTION_OPPORTUNITIES].find(
        {'date': date, 'level': {'$in': ['FORTE', 'OBSERVATION']}}
    ).sort('opportunity_score', -1))
    
    if not opps:
        print("❌ Aucune opportunité détectée\n")
        return
    
    forte = [o for o in opps if o['level'] == 'FORTE']
    observation = [o for o in opps if o['level'] == 'OBSERVATION']
    
    # Opportunités FORTES
    if forte:
        print(f"🔥 OPPORTUNITÉS FORTES ({len(forte)}) - Score ≥ 70")
        print("-"*100)
        print(f"{'TICKER':<8} {'SCORE':<8} {'PRIX':<10} {'VOL_ACC':<10} {'NEWS':<10} {'VOLAT':<10} {'SECT':<10} {'DÉTECTEURS'}")
        print("-"*100)
        
        for opp in forte:
            comp = opp['components']
            det = opp['detectors']
            
            # Détecteurs actifs
            det_active = []
            if det['news_silent']['detected']:
                det_active.append('📰News')
            if det['volume_accumulation']['detected']:
                det_active.append('📊Vol')
            if det['volatility_awakening']['detected']:
                det_active.append('⚡Volat')
            if det['sector_lag']['detected']:
                det_active.append('🏢Sect')
            
            print(
                f"{opp['symbol']:<8} "
                f"{opp['opportunity_score']:<8.1f} "
                f"{opp['current_price']:<10.0f} "
                f"{comp['volume_acceleration']:<10.1f} "
                f"{comp['semantic_impact']:<10.1f} "
                f"{comp['volatility_expansion']:<10.1f} "
                f"{comp['sector_momentum']:<10.1f} "
                f"{' + '.join(det_active)}"
            )
        print()
    
    # Opportunités OBSERVATION
    if observation:
        print(f"🔍 OPPORTUNITÉS EN OBSERVATION ({len(observation)}) - Score 55-70")
        print("-"*100)
        print(f"{'TICKER':<8} {'SCORE':<8} {'PRIX':<10} {'DÉTECTEUR PRINCIPAL':<30} {'RAISON'}")
        print("-"*100)
        
        for opp in observation:
            comp = opp['components']
            
            # Trouver composante dominante
            dominant = max(comp.items(), key=lambda x: x[1])
            dominant_name = {
                'volume_acceleration': 'Volume anormal',
                'semantic_impact': 'News silencieuse',
                'volatility_expansion': 'Rupture de sommeil',
                'sector_momentum': 'Retard secteur'
            }[dominant[0]]
            
            # Raison détaillée
            det = opp['detectors']
            reason = ""
            if det['news_silent']['detected']:
                reason = det['news_silent']['reason']
            elif det['volume_accumulation']['detected']:
                reason = det['volume_accumulation']['reason']
            elif det['volatility_awakening']['detected']:
                reason = det['volatility_awakening']['reason']
            elif det['sector_lag']['detected']:
                reason = det['sector_lag']['reason']
            else:
                reason = "Multiple signaux faibles"
            
            print(
                f"{opp['symbol']:<8} "
                f"{opp['opportunity_score']:<8.1f} "
                f"{opp['current_price']:<10.0f} "
                f"{dominant_name:<30} "
                f"{reason}"
            )
        print()
    
    print(f"📈 TOTAL : {len(opps)} opportunités ({len(forte)} fortes, {len(observation)} observation)")
    print("="*100 + "\n")

# ============================================================================
# CONVERSION OPPORTUNITÉS → TOP5
# ============================================================================

def analyze_opportunity_conversion(weeks=12):
    """
    Analyser conversion opportunités → TOP5
    
    Pour chaque opportunité détectée :
    - Est-elle entrée dans un TOP5 dans les 7 jours suivants ?
    - Combien de jours entre détection et TOP5 ?
    - Performance réalisée ?
    
    Args:
        weeks: Nombre de semaines à analyser
    
    Returns:
        dict: Statistiques conversion
    """
    print("\n" + "="*100)
    print(f"🔄 ANALYSE CONVERSION OPPORTUNITÉS → TOP5 ({weeks} dernières semaines)")
    print("="*100 + "\n")
    
    # Date début analyse
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    start_str = start_date.strftime("%Y-%m-%d")
    
    # Toutes les opportunités détectées
    opps = list(db[COLLECTION_OPPORTUNITIES].find({
        'date': {'$gte': start_str},
        'level': {'$in': ['FORTE', 'OBSERVATION']}
    }))
    
    print(f"📊 {len(opps)} opportunités détectées depuis {start_str}\n")
    
    if not opps:
        print("❌ Aucune opportunité sur la période\n")
        return {}
    
    # Pour chaque opportunité, vérifier si elle est entrée dans TOP5
    conversions = []
    no_conversion = []
    
    for opp in opps:
        symbol = opp['symbol']
        opp_date = datetime.strptime(opp['date'], "%Y-%m-%d")
        
        # Chercher TOP5 dans les 7 jours suivants
        window_end = opp_date + timedelta(days=7)
        
        # Trouver semaines concernées
        weeks_to_check = []
        current = opp_date
        while current <= window_end:
            week_str = current.strftime("%Y-W%V")
            if week_str not in weeks_to_check:
                weeks_to_check.append(week_str)
            current += timedelta(days=7)
        
        # Chercher dans TOP5
        found_in_top5 = None
        for week in weeks_to_check:
            top5_entry = db[COLLECTION_TOP5].find_one({
                'symbol': symbol,
                'week': week
            })
            
            if top5_entry:
                found_in_top5 = {
                    'week': week,
                    'rank': top5_entry.get('rank', 0),
                    'score': top5_entry.get('top5_score', 0)
                }
                break
        
        if found_in_top5:
            # Calculer performance réalisée
            # Trouver prix entrée (date opportunité) et prix sortie (fin de semaine TOP5)
            entry_price = opp.get('current_price', 0)
            
            # Dernier jour de la semaine TOP5
            week_num = int(found_in_top5['week'].split('-W')[1])
            year = int(found_in_top5['week'].split('-W')[0])
            
            # Approx fin de semaine
            week_end_approx = (opp_date + timedelta(days=14)).strftime("%Y-%m-%d")
            
            exit_daily = db[COLLECTION_DAILY].find_one({
                'symbol': symbol,
                'date': {'$lte': week_end_approx}
            }, sort=[('date', -1)])
            
            exit_price = exit_daily.get('close', 0) if exit_daily else 0
            
            performance = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            conversions.append({
                'symbol': symbol,
                'opp_date': opp['date'],
                'opp_level': opp['level'],
                'opp_score': opp['opportunity_score'],
                'top5_week': found_in_top5['week'],
                'top5_rank': found_in_top5['rank'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'performance': performance
            })
        else:
            no_conversion.append({
                'symbol': symbol,
                'opp_date': opp['date'],
                'opp_level': opp['level'],
                'opp_score': opp['opportunity_score']
            })
    
    # Statistiques
    total_opps = len(opps)
    converted = len(conversions)
    conversion_rate = (converted / total_opps * 100) if total_opps > 0 else 0
    
    # Affichage conversions
    if conversions:
        print(f"✅ OPPORTUNITÉS CONVERTIES EN TOP5 ({converted}/{total_opps} = {conversion_rate:.1f}%)\n")
        print("-"*100)
        print(f"{'TICKER':<8} {'DATE_OPP':<12} {'NIVEAU':<15} {'SCORE_OPP':<10} {'SEMAINE_TOP5':<15} {'RANK':<6} {'PERF':<8}")
        print("-"*100)
        
        conversions.sort(key=lambda x: x['performance'], reverse=True)
        
        for conv in conversions[:20]:  # Top 20
            print(
                f"{conv['symbol']:<8} "
                f"{conv['opp_date']:<12} "
                f"{conv['opp_level']:<15} "
                f"{conv['opp_score']:<10.1f} "
                f"{conv['top5_week']:<15} "
                f"#{conv['top5_rank']:<5} "
                f"{conv['performance']:>7.1f}%"
            )
        
        # Moyennes
        avg_perf = sum(c['performance'] for c in conversions) / len(conversions)
        print("-"*100)
        print(f"Performance moyenne : {avg_perf:+.1f}%")
        print()
    
    # Non converties
    if no_conversion:
        print(f"\n❌ OPPORTUNITÉS NON CONVERTIES ({len(no_conversion)})\n")
        print("-"*100)
        print(f"{'TICKER':<8} {'DATE':<12} {'NIVEAU':<15} {'SCORE':<10} {'RAISON PROBABLE'}")
        print("-"*100)
        
        for nc in no_conversion[:10]:  # Top 10
            # Vérifier si le marché a baissé
            symbol = nc['symbol']
            opp_date = nc['opp_date']
            
            # Performance 7j après
            week_later = (datetime.strptime(opp_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
            
            entry = db[COLLECTION_DAILY].find_one({'symbol': symbol, 'date': opp_date})
            exit_d = db[COLLECTION_DAILY].find_one({'symbol': symbol, 'date': {'$lte': week_later}}, sort=[('date', -1)])
            
            if entry and exit_d:
                perf = ((exit_d['close'] - entry['close']) / entry['close'] * 100)
                
                if perf < -5:
                    reason = f"Chute {perf:.1f}%"
                elif perf > 5:
                    reason = f"Hausse {perf:.1f}% (pas assez pour TOP5)"
                else:
                    reason = "Stagnation"
            else:
                reason = "Données insuffisantes"
            
            print(
                f"{nc['symbol']:<8} "
                f"{nc['opp_date']:<12} "
                f"{nc['opp_level']:<15} "
                f"{nc['opp_score']:<10.1f} "
                f"{reason}"
            )
        print()
    
    print("="*100)
    print(f"\n📊 RÉSUMÉ :")
    print(f"   Taux de conversion : {conversion_rate:.1f}%")
    print(f"   Converties         : {converted}")
    print(f"   Non converties     : {len(no_conversion)}")
    print(f"   Total opportunités : {total_opps}")
    
    if conversions:
        forte_conv = sum(1 for c in conversions if c['opp_level'] == 'FORTE')
        forte_total = sum(1 for o in opps if o['level'] == 'FORTE')
        forte_rate = (forte_conv / forte_total * 100) if forte_total > 0 else 0
        
        print(f"\n   FORTE → TOP5       : {forte_rate:.1f}% ({forte_conv}/{forte_total})")
    
    print("\n" + "="*100 + "\n")
    
    return {
        'total_opportunities': total_opps,
        'converted': converted,
        'conversion_rate': conversion_rate,
        'conversions': conversions,
        'no_conversion': no_conversion
    }

# ============================================================================
# HISTORIQUE OPPORTUNITÉS
# ============================================================================

def show_opportunity_history(symbol, days=30):
    """Afficher historique opportunités pour un symbole"""
    print("\n" + "="*100)
    print(f"📜 HISTORIQUE OPPORTUNITÉS - {symbol} ({days} derniers jours)")
    print("="*100 + "\n")
    
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    opps = list(db[COLLECTION_OPPORTUNITIES].find({
        'symbol': symbol,
        'date': {'$gte': cutoff}
    }).sort('date', -1))
    
    if not opps:
        print(f"❌ Aucune opportunité détectée pour {symbol} sur {days}j\n")
        return
    
    print(f"📊 {len(opps)} détections\n")
    print("-"*100)
    print(f"{'DATE':<12} {'SCORE':<8} {'NIVEAU':<15} {'DÉTECTEURS ACTIFS':<50}")
    print("-"*100)
    
    for opp in opps:
        det = opp['detectors']
        
        det_active = []
        if det['news_silent']['detected']:
            det_active.append('News')
        if det['volume_accumulation']['detected']:
            det_active.append('Volume')
        if det['volatility_awakening']['detected']:
            det_active.append('Volatilité')
        if det['sector_lag']['detected']:
            det_active.append('Secteur')
        
        print(
            f"{opp['date']:<12} "
            f"{opp['opportunity_score']:<8.1f} "
            f"{opp['level']:<15} "
            f"{' + '.join(det_active) if det_active else 'Aucun':<50}"
        )
    
    print("="*100 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Dashboard principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dashboard Opportunités BRVM')
    parser.add_argument('--today', action='store_true', help='Opportunités du jour')
    parser.add_argument('--conversion', action='store_true', help='Analyse conversion → TOP5')
    parser.add_argument('--weeks', type=int, default=12, help='Semaines pour analyse conversion')
    parser.add_argument('--history', help='Historique symbole')
    parser.add_argument('--days', type=int, default=30, help='Jours pour historique')
    parser.add_argument('--date', help='Date spécifique (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print("\n" + "="*100)
    print("📊 DASHBOARD OPPORTUNITÉS BRVM")
    print("="*100)
    print("Objectif : Détecter AVANT | Entrer TÔT | Capturer le mouvement")
    print("="*100)
    
    if args.today:
        show_today_opportunities(args.date)
    
    if args.conversion:
        analyze_opportunity_conversion(args.weeks)
    
    if args.history:
        show_opportunity_history(args.history, args.days)
    
    if not any([args.today, args.conversion, args.history]):
        # Affichage par défaut : tout
        show_today_opportunities(args.date)
        analyze_opportunity_conversion(args.weeks)

if __name__ == "__main__":
    main()

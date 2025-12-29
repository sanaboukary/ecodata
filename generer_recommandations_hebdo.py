#!/usr/bin/env python3
"""
🎯 ANALYSE QUOTIDIENNE STRATEGIQUE - TRADING HEBDOMADAIRE BRVM
Recommandations quotidiennes pour 50-80% rendement/semaine
"""

import os
import sys
import io
import django

# Forcer UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta
import json
import statistics

def collecter_publications_brvm():
    """Collecte publications BRVM récentes"""
    
    client, db = get_mongo_db()
    
    # Publications des 30 derniers jours
    date_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    publications = list(db.brvm_publications.find({
        'date_publication': {'$gte': date_limite}
    }).sort('date_publication', -1))
    
    return publications

def collecter_evenements_futurs():
    """Collecte événements corporate à venir"""
    
    client, db = get_mongo_db()
    
    # Événements des 14 prochains jours
    date_limite = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    
    evenements = list(db.brvm_events.find({
        'date': {'$lte': date_limite}
    }).sort('date', 1))
    
    return evenements

def analyser_action_strategique(symbol: str) -> dict:
    """Analyse stratégique complète d'une action"""
    
    client, db = get_mongo_db()
    
    # 1. Récupérer historique prix 60 jours
    historique = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': symbol,
        'data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    }).sort('ts', 1).limit(60))
    
    if len(historique) < 10:
        return None
    
    prix = [obs['value'] for obs in historique]
    
    # Filtrer prix valides (>0)
    prix_valides = [p for p in prix if p > 0]
    
    if len(prix_valides) < 10:
        return None
    
    # 2. Momentum 5 jours
    momentum_5j = 0
    if len(prix_valides) >= 6 and prix_valides[-6] > 0:
        momentum_5j = ((prix_valides[-1] / prix_valides[-6]) - 1) * 100
    
    # 3. Volatilité
    variations = []
    for i in range(1, len(prix_valides)):
        if prix_valides[i-1] > 0:
            variations.append((prix_valides[i]/prix_valides[i-1] - 1))
    
    volatility = statistics.stdev(variations) if len(variations) > 1 else 0.05
    
    # 4. Publications récentes (catalyseurs)
    nb_publications = db.curated_observations.count_documents({
        'source': 'BRVM_PUBLICATIONS',
        'attrs.emetteur': {'$regex': symbol.replace('.BC', ''), '$options': 'i'}
    })
    
    # 5. Scoring simplifié
    score_momentum = min(30, max(0, int(momentum_5j * 3))) if momentum_5j > 0 else 0
    score_catalyseurs = min(25, nb_publications * 5)
    score_volatility = 10 if 0.01 < volatility < 0.05 else 0
    
    score_total = score_momentum + score_catalyseurs + score_volatility
    
    # 6. Potentiel et confiance
    potentiel_gain = momentum_5j / 100 * 5 if momentum_5j > 0 else 0.05
    confiance = min(0.95, 0.60 + (score_total / 200))
    
    return {
        'symbol': symbol,
        'prix_actuel': prix_valides[-1],
        'momentum_5j': momentum_5j,
        'volatility': volatility,
        'nb_publications': nb_publications,
        'score': score_total,
        'potentiel_gain': potentiel_gain,
        'confiance': confiance,
        'prix_cible': prix_valides[-1] * (1 + potentiel_gain),
        'stop_loss': prix_valides[-1] * 0.93,
        'jours_holding': 5,
        'recommendation': 'BUY' if score_total >= 50 else 'HOLD',
        'catalyseurs': [f'Momentum +{momentum_5j:.1f}%', f'{nb_publications} publications'],
        'risques': ['Volatilité élevée'] if volatility > 0.05 else [],
        'scores_detail': {
            'momentum': score_momentum,
            'catalyseurs': score_catalyseurs,
            'volatility': score_volatility
        }
    }

def generer_recommandations_quotidiennes():
    """Génère recommandations quotidiennes pour toutes les actions"""
    
    print("\n" + "="*80)
    print("ANALYSE QUOTIDIENNE STRATEGIQUE - TRADING HEBDOMADAIRE")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🎯 Objectif: 50-80% rendement hebdomadaire")
    print(f"🎲 Confiance cible: 85-95%")
    print("\n" + "="*80)
    
    # Actions à analyser
    ACTIONS_BRVM = [
        'ABJC.BC', 'BICC.BC', 'BOAB.BC', 'BOABF.BC', 'BOAC.BC',
        'BOAM.BC', 'CABC.BC', 'CFAC.BC', 'CIAC.BC', 'CIE.BC',
        'ECOC.BC', 'ETIT.BC', 'NEIC.BC', 'NSBC.BC', 'NTLC.BC',
        'ORGT.BC', 'SABC.BC', 'SCRC.BC', 'SDCC.BC', 'SDSC.BC',
        'SEMC.BC', 'SGBC.BC', 'SHEC.BC', 'SIBC.BC', 'SICC.BC',
        'SICB.BC', 'SIVC.BC', 'SLBC.BC', 'SMBC.BC', 'SNTS.BC',
        'SOGC.BC', 'STAC.BC', 'STBC.BC', 'SVOC.BC', 'ONTBF.BC',
        'PALC.BC', 'PRSC.BC', 'TTLC.BC', 'TTLS.BC', 'UNXC.BC',
        'FTSC.BC', 'UNLC.BC', 'BNBC.BC'
    ]
    
    print(f"\n🔍 Analyse de {len(ACTIONS_BRVM)} actions...\n")
    
    analyses = []
    
    for symbol in ACTIONS_BRVM:
        try:
            analyse = analyser_action_strategique(symbol)
            
            if analyse and analyse['score'] >= 50:
                analyses.append(analyse)
                print(f"  ✓ {symbol:<12} Score: {analyse['score']}/100  "
                      f"Potentiel: +{analyse['potentiel_gain']*100:.0f}%  "
                      f"Confiance: {analyse['confiance']*100:.0f}%")
        except Exception as e:
            print(f"  ✗ {symbol:<12} Erreur: {str(e)[:50]}")
    
    print(f"\n{'='*80}")
    print(f"📊 FILTRAGE DES OPPORTUNITÉS PREMIUM")
    print(f"{'='*80}\n")
    
    # Filtrer top 5 - trié par score
    top_opportunites = sorted(
        [a for a in analyses if a['score'] >= 50],
        key=lambda x: x['score'],
        reverse=True
    )[:5]
    
    print(f"🏆 TOP 5 OPPORTUNITÉS HEBDOMADAIRES:\n")
    
    for i, opp in enumerate(top_opportunites, 1):
        print(f"{i}. {opp['symbol']:<12} - {opp['recommendation']}")
        print(f"   Prix actuel:  {opp['prix_actuel']:>10,.0f} FCFA")
        print(f"   Prix cible:   {opp['prix_cible']:>10,.0f} FCFA (+{opp['potentiel_gain']*100:.0f}%)")
        print(f"   Stop loss:    {opp['stop_loss']:>10,.0f} FCFA")
        print(f"   Confiance:    {opp['confiance']*100:>10.0f}%")
        print(f"   Score global: {opp['score']:>10.0f}/100")
        print(f"   Horizon:      {opp['jours_holding']:>10} jours")
        
        print(f"\n   🎯 CATALYSEURS:")
        for cat in opp['catalyseurs'][:3]:
            print(f"      • {cat}")
        
        if opp['risques']:
            print(f"\n   ⚠️  RISQUES:")
            for risque in opp['risques'][:2]:
                print(f"      • {risque}")
        
        print()
    
    # Sauvegarder
    filename = f'recommandations_hebdo_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'date_generation': datetime.now().isoformat(),
            'strategie': 'TRADING_HEBDOMADAIRE',
            'objectif_rendement': '50-80%',
            'top_opportunites': top_opportunites,
            'toutes_analyses': analyses
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"{'='*80}")
    print(f"💾 SAUVEGARDE")
    print(f"{'='*80}\n")
    print(f"✓ Fichier: {filename}")
    print(f"✓ Opportunités premium: {len(top_opportunites)}")
    print(f"✓ Analyses totales: {len(analyses)}")
    print()
    
    return top_opportunites

if __name__ == '__main__':
    recommandations = generer_recommandations_quotidiennes()
    
    print("="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)
    print()
    print("📋 PROCHAINES ÉTAPES:")
    print("  1. Consulter le dashboard: http://localhost:8000/dashboard/brvm/")
    print("  2. Configurer alertes quotidiennes (email/SMS)")
    print("  3. Activer DAG Airflow pour automatisation")
    print()

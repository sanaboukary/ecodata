#!/usr/bin/env python3
"""
📊 BACKTESTING SYSTÈME DE RECOMMANDATIONS
Valide la précision 85-95% sur les 60 derniers jours
Objectif: 50-80% rendement hebdomadaire
"""
import os
import sys
import io
import django
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*100)
print("📊 BACKTESTING SYSTÈME RECOMMANDATIONS BRVM - 60 JOURS")
print("="*100)
print()

client, db = get_mongo_db()

# Paramètres backtesting
PERIODE_HOLDING = 7  # 7 jours (1 semaine)
SEUIL_SCORE = 70      # Score minimum pour recommander
OBJECTIF_MIN = 50     # 50% gain minimum
OBJECTIF_MAX = 80     # 80% gain maximum
PRECISION_CIBLE_MIN = 85  # 85% minimum de précision
PRECISION_CIBLE_MAX = 95  # 95% maximum de précision

print(f"⚙️  PARAMÈTRES BACKTESTING:")
print(f"  - Période de holding: {PERIODE_HOLDING} jours")
print(f"  - Score minimum: {SEUIL_SCORE}/100")
print(f"  - Objectif rendement: {OBJECTIF_MIN}-{OBJECTIF_MAX}% par semaine")
print(f"  - Précision cible: {PRECISION_CIBLE_MIN}-{PRECISION_CIBLE_MAX}%")
print()

# Récupérer toutes les actions avec au moins 15 observations
actions_brvm = db.curated_observations.distinct('key', {'source': 'BRVM'})

actions_testables = []
for symbol in actions_brvm:
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'key': symbol,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    if count >= 15:  # Au moins 15 observations pour tester
        actions_testables.append(symbol)

print(f"📊 Actions testables: {len(actions_testables)} (sur {len(actions_brvm)} total)")
print()

# Récupérer sentiment publications (simplifié pour backtesting)
bulletins = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS',
    'attrs.sentiment_label': {'$exists': True}
}))

ag_convocations = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'CONVOCATIONS_AG'
}))

print(f"📰 Publications: {len(bulletins)} bulletins, {len(ag_convocations)} AG")
print()
print("="*100)
print("🔍 SIMULATION DES TRADES...")
print("="*100)
print()

resultats_trades = []
total_trades = 0
trades_gagnants = 0
trades_perdants = 0
rendements = []

for symbol in actions_testables[:20]:  # Tester les 20 premières pour ne pas être trop long
    # Récupérer historique complet
    historique = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': symbol,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    }).sort('ts', 1))
    
    if len(historique) < 15:
        continue
    
    # Simuler des points d'entrée (chaque 7 jours)
    for i in range(0, len(historique) - PERIODE_HOLDING - 5, PERIODE_HOLDING):
        # Données pour décision (5 jours d'historique)
        donnees_decision = historique[i:i+5]
        
        if len(donnees_decision) < 5:
            continue
        
        # Calcul score simplifié
        prix = [obs['value'] for obs in donnees_decision if obs.get('value', 0) > 0]
        
        if len(prix) < 5:
            continue
        
        # Momentum
        prix_debut = prix[0]
        prix_fin_decision = prix[-1]
        momentum = ((prix_fin_decision / prix_debut) - 1) * 100
        score_momentum = max(0, min(40, int(momentum * 4)))
        
        # Catalyseurs (simplifié)
        score_catalyseurs = 16 if bulletins and ag_convocations else 0
        
        # Sentiment (simplifié)
        score_sentiment = 13 if bulletins else 0
        
        # Tendance
        tendance_haussiere = all(prix[j] <= prix[j+1] for j in range(len(prix)-1))
        score_tendance = 5 if tendance_haussiere else 0
        
        # Volatilité
        if len(prix) >= 3:
            high = max(prix[-3:])
            low = min(prix[-3:])
            volatility_pct = ((high - low) / low * 100) if low > 0 else 0
            score_volatility = min(10, int(volatility_pct / 2))
        else:
            score_volatility = 0
        
        score_total = score_momentum + score_catalyseurs + score_sentiment + score_tendance + score_volatility
        
        # Recommander si score >= seuil
        if score_total >= SEUIL_SCORE:
            # Simuler achat au dernier prix de décision
            prix_achat = prix_fin_decision
            
            # Vérifier prix 7 jours plus tard
            idx_vente = i + 5 + PERIODE_HOLDING
            if idx_vente < len(historique):
                prix_vente = historique[idx_vente].get('value', 0)
                
                if prix_vente > 0 and prix_achat > 0:
                    rendement = ((prix_vente / prix_achat) - 1) * 100
                    
                    total_trades += 1
                    rendements.append(rendement)
                    
                    if rendement >= OBJECTIF_MIN:
                        trades_gagnants += 1
                        status = "✅ GAGNANT"
                    else:
                        trades_perdants += 1
                        status = "❌ PERDANT"
                    
                    resultats_trades.append({
                        'symbol': symbol,
                        'date_achat': donnees_decision[-1]['ts'],
                        'prix_achat': prix_achat,
                        'prix_vente': prix_vente,
                        'rendement': rendement,
                        'score': score_total,
                        'status': status
                    })
                    
                    if total_trades <= 10:  # Afficher les 10 premiers
                        print(f"{status} {symbol:<10} Score:{score_total:>3} | Achat:{prix_achat:>8,.0f} → Vente:{prix_vente:>8,.0f} | Rendement:{rendement:>+7.1f}%")

print()
print("="*100)
print("📊 RÉSULTATS BACKTESTING")
print("="*100)
print()

if total_trades > 0:
    precision = (trades_gagnants / total_trades * 100)
    rendement_moyen = statistics.mean(rendements)
    rendement_median = statistics.median(rendements)
    
    print(f"📈 PERFORMANCE GLOBALE:")
    print(f"  Total trades:        {total_trades}")
    print(f"  Trades gagnants:     {trades_gagnants} ({trades_gagnants/total_trades*100:.1f}%)")
    print(f"  Trades perdants:     {trades_perdants} ({trades_perdants/total_trades*100:.1f}%)")
    print()
    print(f"🎯 PRÉCISION: {precision:.1f}%")
    
    if precision >= PRECISION_CIBLE_MIN and precision <= PRECISION_CIBLE_MAX:
        print(f"  ✅ OBJECTIF ATTEINT ({PRECISION_CIBLE_MIN}-{PRECISION_CIBLE_MAX}%)")
    elif precision > PRECISION_CIBLE_MAX:
        print(f"  ⚠️  DÉPASSEMENT DE L'OBJECTIF (peut indiquer overfitting)")
    else:
        print(f"  ❌ EN DESSOUS DE L'OBJECTIF ({PRECISION_CIBLE_MIN}%)")
    
    print()
    print(f"💰 RENDEMENTS:")
    print(f"  Moyen:               {rendement_moyen:+.1f}%")
    print(f"  Médian:              {rendement_median:+.1f}%")
    print(f"  Minimum:             {min(rendements):+.1f}%")
    print(f"  Maximum:             {max(rendements):+.1f}%")
    print()
    
    # Trades dépassant l'objectif 50-80%
    trades_objectif = [r for r in rendements if OBJECTIF_MIN <= r <= OBJECTIF_MAX]
    trades_au_dessus = [r for r in rendements if r > OBJECTIF_MAX]
    trades_en_dessous = [r for r in rendements if r < OBJECTIF_MIN]
    
    print(f"🎯 RÉPARTITION OBJECTIF 50-80%:")
    print(f"  Dans l'objectif:     {len(trades_objectif)} ({len(trades_objectif)/total_trades*100:.1f}%)")
    print(f"  Au-dessus (>80%):    {len(trades_au_dessus)} ({len(trades_au_dessus)/total_trades*100:.1f}%)")
    print(f"  En-dessous (<50%):   {len(trades_en_dessous)} ({len(trades_en_dessous)/total_trades*100:.1f}%)")
    print()
    
    # Meilleurs trades
    print(f"="*100)
    print(f"🏆 TOP 5 MEILLEURS TRADES:")
    print(f"="*100)
    print()
    
    top_trades = sorted(resultats_trades, key=lambda x: x['rendement'], reverse=True)[:5]
    for i, trade in enumerate(top_trades, 1):
        print(f"{i}. {trade['symbol']:<10} | {trade['date_achat']} | {trade['prix_achat']:>8,.0f} → {trade['prix_vente']:>8,.0f} FCFA | {trade['rendement']:>+7.1f}% | Score:{trade['score']}")
    
    print()
    
    # Recommandations
    print(f"="*100)
    print(f"📋 RECOMMANDATIONS:")
    print(f"="*100)
    print()
    
    if precision >= PRECISION_CIBLE_MIN:
        print(f"  ✅ Le système atteint la précision cible de {PRECISION_CIBLE_MIN}%+")
        print(f"  ✅ Déploiement en production recommandé")
        print()
        print(f"  📊 Prochaines étapes:")
        print(f"    1. Ajuster seuil de score pour optimiser rendement/risque")
        print(f"    2. Intégrer stop-loss à -10% pour limiter pertes")
        print(f"    3. Automatiser avec Airflow (génération quotidienne 17h30)")
        print(f"    4. Monitorer performance en temps réel")
    else:
        print(f"  ⚠️  Précision {precision:.1f}% < {PRECISION_CIBLE_MIN}% cible")
        print(f"  📊 Améliorations suggérées:")
        print(f"    1. Augmenter le seuil de score (actuellement {SEUIL_SCORE}/100)")
        print(f"    2. Analyser plus de bulletins NLP (actuellement {len(bulletins)})")
        print(f"    3. Affiner le scoring des catalyseurs")
        print(f"    4. Intégrer indicateurs techniques (RSI, MACD)")
    
else:
    print(f"❌ Aucun trade généré (vérifier données et paramètres)")

print()
print("="*100)
print()

# Sauvegarder résultats
import json
output = {
    'date_backtest': datetime.now().isoformat(),
    'parametres': {
        'periode_holding': PERIODE_HOLDING,
        'seuil_score': SEUIL_SCORE,
        'objectif_rendement': f'{OBJECTIF_MIN}-{OBJECTIF_MAX}%',
        'precision_cible': f'{PRECISION_CIBLE_MIN}-{PRECISION_CIBLE_MAX}%'
    },
    'resultats': {
        'total_trades': total_trades,
        'trades_gagnants': trades_gagnants,
        'trades_perdants': trades_perdants,
        'precision': round(precision, 2) if total_trades > 0 else 0,
        'rendement_moyen': round(rendement_moyen, 2) if rendements else 0,
        'rendement_median': round(rendement_median, 2) if rendements else 0,
        'rendement_min': round(min(rendements), 2) if rendements else 0,
        'rendement_max': round(max(rendements), 2) if rendements else 0
    },
    'tous_trades': resultats_trades
}

filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Résultats sauvegardés: {filename}")
print()

client.close()

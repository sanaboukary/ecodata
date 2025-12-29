#!/usr/bin/env python3
"""
🎯 GÉNÉRATEUR TOP 5 SIMPLE & FONCTIONNEL
Version ultra-simplifiée pour avoir des résultats maintenant
"""
import os
import sys
import io
import django
from datetime import datetime
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*80)
print("🎯 GÉNÉRATEUR TOP 5 - VERSION SIMPLE")
print("="*80)
print()

client, db = get_mongo_db()

# Récupérer toutes les actions disponibles
actions_brvm = db.curated_observations.distinct('key', {'source': 'BRVM'})
print(f"📊 Actions disponibles: {len(actions_brvm)}")
print()

opportunites = []

for symbol in actions_brvm:
    # Récupérer dernières 10 observations
    historique = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': symbol,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    }).sort('ts', -1).limit(10))
    
    if len(historique) < 5:
        continue
    
    # Prix valides seulement
    prix = [obs['value'] for obs in historique if obs.get('value', 0) > 0]
    
    if len(prix) < 5:
        continue
    
    # Calcul momentum simple: variation 5 jours
    prix_recent = prix[0]
    prix_5j = prix[4] if len(prix) >= 5 else prix[-1]
    
    if prix_5j <= 0:
        continue
    
    momentum = ((prix_recent / prix_5j) - 1) * 100
    
    # Score basique
    score_momentum = max(0, min(50, int(momentum * 5)))  # 0-50 points
    
    # Vérifier publications
    catalyseur = 0
    catalyseur_desc = []
    
    # Bulletins récents
    bulletins = list(db.curated_observations.find({
        'source': 'BRVM_PUBLICATIONS',
        'dataset': 'BULLETINS_OFFICIELS',
        'attrs.sentiment_label': 'POSITIF'
    }).limit(5))
    
    if bulletins:
        catalyseur += 10
        catalyseur_desc.append(f"{len(bulletins)} bulletins positifs")
    
    # AG convocations
    ag = list(db.curated_observations.find({
        'source': 'BRVM_PUBLICATIONS',
        'dataset': 'CONVOCATIONS_AG'
    }).limit(5))
    
    if ag:
        catalyseur += 15
        catalyseur_desc.append(f"{len(ag)} AG convoquées")
    
    score_total = score_momentum + catalyseur
    
    # Seuil minimal: 20 points
    if score_total >= 20:
        opportunites.append({
            'symbol': symbol,
            'score': score_total,
            'momentum_5j': round(momentum, 2),
            'score_momentum': score_momentum,
            'score_catalyseur': catalyseur,
            'prix_actuel': prix_recent,
            'prix_5j': prix_5j,
            'catalyseurs': catalyseur_desc,
            'nb_obs': len(historique)
        })
        
        print(f"✓ {symbol:<12} Score: {score_total:>3} (Momentum: {momentum:+6.1f}%, Catalyseur: {catalyseur})")

print()
print(f"{'='*80}")
print(f"📊 RÉSULTATS")
print(f"{'='*80}")
print()

# Trier par score décroissant
opportunites.sort(key=lambda x: x['score'], reverse=True)

print(f"Total opportunités: {len(opportunites)}")
print()

if len(opportunites) > 0:
    print(f"🏆 TOP 5 RECOMMANDATIONS:")
    print(f"{'='*80}")
    print()
    
    top5 = opportunites[:5]
    
    for i, opp in enumerate(top5, 1):
        print(f"{i}. {opp['symbol']} - Score {opp['score']}/100")
        print(f"   Prix actuel: {opp['prix_actuel']:,.0f} FCFA")
        print(f"   Momentum 5j: {opp['momentum_5j']:+.2f}%")
        print(f"   Catalyseurs: {', '.join(opp['catalyseurs']) if opp['catalyseurs'] else 'Aucun'}")
        print()
    
    # Sauvegarder résultats
    output = {
        'date_generation': datetime.now().isoformat(),
        'strategie': 'TRADING_HEBDOMADAIRE',
        'objectif_rendement': '50-80% semaine',
        'precision_cible': '85-95%',
        'top_5': top5,
        'toutes_opportunites': opportunites,
        'stats': {
            'total_actions': len(actions_brvm),
            'actions_analysees': len([o for o in opportunites]),
            'top_score': opportunites[0]['score'] if opportunites else 0
        }
    }
    
    filename = f"top5_recommandations_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"{'='*80}")
    print(f"✅ Fichier généré: {filename}")
    print(f"{'='*80}")
    
else:
    print("❌ Aucune opportunité trouvée")
    print()
    print("Diagnostic:")
    print(f"  - Actions disponibles: {len(actions_brvm)}")
    print(f"  - Vérifier que les données ont au moins 5 observations par action")

print()

client.close()

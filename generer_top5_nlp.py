#!/usr/bin/env python3
"""
🎯 GÉNÉRATEUR TOP 5 AVEC NLP SENTIMENT INTÉGRÉ
Version améliorée avec scoring publications (100 points max)
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
print("🎯 GÉNÉRATEUR TOP 5 - VERSION NLP SENTIMENT")
print("="*80)
print()

client, db = get_mongo_db()

# Récupérer toutes les actions
actions_brvm = db.curated_observations.distinct('key', {'source': 'BRVM'})
print(f"📊 Actions disponibles: {len(actions_brvm)}")

# Récupérer publications avec sentiment
bulletins = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS',
    'attrs.sentiment_label': {'$exists': True}
}))

ag_convocations = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'CONVOCATIONS_AG'
}))

print(f"📰 Publications NLP: {len(bulletins)} bulletins analysés, {len(ag_convocations)} AG")
print()

# Calculer sentiment global du marché
if bulletins:
    sentiments = [b['attrs'].get('sentiment_score', 0) for b in bulletins if 'sentiment_score' in b.get('attrs', {})]
    sentiment_marche = sum(sentiments) / len(sentiments) if sentiments else 0
    print(f"📈 Sentiment marché: {sentiment_marche:+.1f}/10 ({len(sentiments)} bulletins)")
else:
    sentiment_marche = 0
    print(f"⚠️  Aucun sentiment analysé - scoring NLP désactivé")

print()
print("="*80)
print("🔍 ANALYSE EN COURS...")
print("="*80)
print()

opportunites = []

for symbol in actions_brvm:
    # Récupérer historique
    historique = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': symbol,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    }).sort('ts', -1).limit(10))
    
    if len(historique) < 5:
        continue
    
    # Prix valides
    prix = [obs['value'] for obs in historique if obs.get('value', 0) > 0]
    
    if len(prix) < 5:
        continue
    
    # === 1. MOMENTUM (40 points max) ===
    prix_recent = prix[0]
    prix_5j = prix[4] if len(prix) >= 5 else prix[-1]
    
    if prix_5j <= 0:
        continue
    
    momentum = ((prix_recent / prix_5j) - 1) * 100
    score_momentum = max(0, min(40, int(momentum * 4)))  # 10% = 40pts
    
    # === 2. VOLATILITÉ (10 points) ===
    # Bonus si volatilité favorable (range élevé = opportunité)
    if len(prix) >= 3:
        high = max(prix[:3])
        low = min(prix[:3])
        volatility_pct = ((high - low) / low * 100) if low > 0 else 0
        score_volatility = min(10, int(volatility_pct / 2))  # 20% vol = 10pts
    else:
        score_volatility = 0
    
    # === 3. CATALYSEURS PUBLICATIONS (25 points) ===
    catalyseurs_desc = []
    score_catalyseurs = 0
    
    # Bulletins positifs (15 points max)
    bulletins_positifs = [b for b in bulletins if b['attrs'].get('sentiment_label') == 'POSITIF']
    if bulletins_positifs:
        score_catalyseurs += min(15, len(bulletins_positifs) * 3)
        catalyseurs_desc.append(f"{len(bulletins_positifs)} bulletins positifs")
    
    # AG convocations (10 points)
    if ag_convocations:
        score_catalyseurs += 10
        catalyseurs_desc.append(f"{len(ag_convocations)} AG convoquées")
    
    # === 4. SENTIMENT NLP (20 points) ===
    score_sentiment = 0
    
    if sentiment_marche > 0:
        # Sentiment général du marché
        score_sentiment = int((sentiment_marche / 10) * 15)  # Max 15pts
        
        # Bonus si bulletins récents très positifs
        bulletins_recents_tres_positifs = [
            b for b in bulletins_positifs 
            if b['attrs'].get('sentiment_score', 0) >= 7
        ]
        if bulletins_recents_tres_positifs:
            score_sentiment += 5
            catalyseurs_desc.append(f"{len(bulletins_recents_tres_positifs)} bulletins +7/10")
    
    # === 5. TENDANCE (5 points) ===
    # Bonus si prix croissant sur 3 derniers jours
    if len(prix) >= 3:
        tendance_haussiere = all(prix[i] <= prix[i-1] for i in range(1, min(3, len(prix))))
        score_tendance = 5 if tendance_haussiere else 0
    else:
        score_tendance = 0
    
    # === SCORE TOTAL (100 points max) ===
    score_total = score_momentum + score_volatility + score_catalyseurs + score_sentiment + score_tendance
    
    # Seuil minimal: 50 points
    if score_total >= 50:
        opportunites.append({
            'symbol': symbol,
            'score': score_total,
            'momentum_5j': round(momentum, 2),
            'volatilite_3j': round(volatility_pct, 2) if len(prix) >= 3 else 0,
            'prix_actuel': prix_recent,
            'prix_5j': prix_5j,
            'score_momentum': score_momentum,
            'score_volatility': score_volatility,
            'score_catalyseurs': score_catalyseurs,
            'score_sentiment': score_sentiment,
            'score_tendance': score_tendance,
            'catalyseurs': catalyseurs_desc,
            'nb_obs': len(historique),
            'sentiment_marche': round(sentiment_marche, 1)
        })
        
        print(f"✓ {symbol:<12} Score: {score_total:>3} (M:{score_momentum} V:{score_volatility} C:{score_catalyseurs} S:{score_sentiment} T:{score_tendance})")

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
        print(f"   Prix: {opp['prix_actuel']:,.0f} FCFA | Momentum 5j: {opp['momentum_5j']:+.2f}%")
        print(f"   Scoring: Momentum({opp['score_momentum']}) + Volatilité({opp['score_volatility']}) + Catalyseurs({opp['score_catalyseurs']}) + Sentiment({opp['score_sentiment']}) + Tendance({opp['score_tendance']})")
        print(f"   Catalyseurs: {', '.join(opp['catalyseurs']) if opp['catalyseurs'] else 'Aucun'}")
        print()
    
    # Sauvegarder
    output = {
        'date_generation': datetime.now().isoformat(),
        'strategie': 'TRADING_HEBDOMADAIRE',
        'objectif_rendement': '50-80% semaine',
        'precision_cible': '85-95%',
        'sentiment_marche': round(sentiment_marche, 1),
        'scoring_schema': {
            'momentum': '40 points max (10% = 40pts)',
            'volatility': '10 points max (20% vol = 10pts)',
            'catalyseurs': '25 points (bulletins + AG)',
            'sentiment_nlp': '20 points (marché + bulletins)',
            'tendance': '5 points (prix croissant 3j)',
            'total': '100 points',
            'seuil_min': '50 points'
        },
        'top_5': top5,
        'toutes_opportunites': opportunites,
        'stats': {
            'total_actions': len(actions_brvm),
            'actions_analysees': len(opportunites),
            'top_score': opportunites[0]['score'] if opportunites else 0,
            'bulletins_analyses': len(bulletins),
            'ag_convocations': len(ag_convocations)
        }
    }
    
    filename = f"top5_nlp_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"{'='*80}")
    print(f"✅ Fichier généré: {filename}")
    print(f"{'='*80}")
    
else:
    print("❌ Aucune opportunité trouvée (seuil 50/100)")

print()

client.close()

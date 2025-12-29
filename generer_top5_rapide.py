#!/usr/bin/env python3
"""Génération rapide Top 5 avec données disponibles"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import statistics

print("="*80)
print("TOP 5 RECOMMANDATIONS - DONNÉES DISPONIBLES")
print("="*80)

# Connexion MongoDB
client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin')
db = client['centralisation_db']

# Dernière date disponible
dates = sorted(db.curated_observations.distinct('ts', {'source': 'BRVM'}))
date_recent = dates[-1][:10]  # Format YYYY-MM-DD
print(f"\nDernière date: {date_recent}")

# Récupérer actions du jour le plus récent
data = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': {'$regex': f'^{date_recent}'}
}))

print(f"Actions disponibles: {len(data)}")

# Analyser et scorer chaque action
scores = []

for obs in data:
    symbol = obs['key']
    
    # Skip indices
    if 'BRVM-' in symbol or symbol in ['BRVM-C.BC', 'BRVM-30.BC']:
        continue
    
    price = obs.get('value', 0)
    if price <= 0:
        continue
    
    attrs = obs.get('attrs', {})
    
    # Critères de scoring
    score = 0
    raisons = []
    
    # 1. Variation positive
    variation = attrs.get('variation', 0)
    if variation > 0:
        score += min(variation * 5, 30)
        raisons.append(f"Hausse {variation:+.1f}%")
    
    # 2. Volume élevé
    volume = attrs.get('volume', 0)
    if volume > 1000:
        score += 20
        raisons.append(f"Volume {volume}")
    elif volume > 500:
        score += 10
    
    # 3. Momentum (YTD)
    ytd = attrs.get('ytd', 0)
    if ytd > 10:
        score += 15
        raisons.append(f"YTD +{ytd:.1f}%")
    elif ytd > 0:
        score += 5
    
    # 4. Capitalisation (grande cap = plus stable)
    mcap = attrs.get('market_cap', 0)
    if mcap > 100_000_000_000:  # >100B FCFA
        score += 10
        raisons.append("Grande cap")
    
    # 5. Secteur porteur
    secteur = attrs.get('sector', '')
    if secteur in ['Telecommunications', 'Finance', 'Banque']:
        score += 10
        raisons.append(f"Secteur {secteur}")
    
    # 6. Prix abordable (facilite diversification)
    if 1000 <= price <= 10000:
        score += 5
    
    # Score bonus si plusieurs critères
    if len(raisons) >= 3:
        score += 10
    
    # Calcul historique 7 jours (si disponible)
    date_7j = (datetime.strptime(date_recent, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
    hist_7j = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': symbol,
        'ts': {'$gte': date_7j, '$lte': date_recent}
    }).sort('ts', 1))
    
    tendance_7j = "stable"
    if len(hist_7j) >= 3:
        prices = [h.get('value', 0) for h in hist_7j if h.get('value', 0) > 0]
        if len(prices) >= 3:
            # Momentum
            momentum = ((prices[-1] - prices[0]) / prices[0]) * 100
            if momentum > 5:
                score += 15
                tendance_7j = f"+{momentum:.1f}%"
                raisons.append(f"Momentum 7j {tendance_7j}")
            elif momentum > 0:
                score += 5
                tendance_7j = f"+{momentum:.1f}%"
            
            # Volatilité faible = bonus
            if len(prices) > 1:
                volatilite = (statistics.stdev(prices) / statistics.mean(prices)) * 100
                if volatilite < 10:
                    score += 10
                    raisons.append("Faible volatilité")
    
    scores.append({
        'symbol': symbol,
        'score': round(score),
        'prix': price,
        'variation_j': variation,
        'volume': volume,
        'ytd': ytd,
        'secteur': secteur,
        'tendance_7j': tendance_7j,
        'raisons': raisons,
        'market_cap': mcap,
        'nb_jours_7j': len(hist_7j)
    })

# Top 5
top5 = sorted(scores, key=lambda x: x['score'], reverse=True)[:5]

print("\n" + "="*80)
print("TOP 5 RECOMMANDATIONS")
print("="*80)

for i, reco in enumerate(top5, 1):
    print(f"\n{i}. {reco['symbol']}")
    print(f"   Score:       {reco['score']}/100")
    print(f"   Prix:        {reco['prix']:,.0f} FCFA")
    print(f"   Variation:   {reco['variation_j']:+.2f}%")
    print(f"   Volume:      {reco['volume']:,}")
    print(f"   Secteur:     {reco['secteur']}")
    print(f"   Tendance 7j: {reco['tendance_7j']}")
    print(f"   Historique:  {reco['nb_jours_7j']} jours disponibles")
    if reco['raisons']:
        print(f"   Raisons:     {', '.join(reco['raisons'][:3])}")

# Sauvegarder
output = {
    'date_generation': datetime.now().isoformat(),
    'date_donnees': date_recent,
    'nb_actions_analysees': len(scores),
    'top5': [{
        'symbol': r['symbol'],
        'score': r['score'],
        'prix_actuel': r['prix'],
        'variation_jour': r['variation_j'],
        'volume': r['volume'],
        'secteur': r['secteur'],
        'stop_loss': round(r['prix'] * 0.93),  # -7%
        'take_profit_1': round(r['prix'] * 1.15),  # +15%
        'take_profit_2': round(r['prix'] * 1.30),  # +30%
        'raisons': r['raisons']
    } for r in top5]
}

filename = f"top5_disponible_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Sauvegardé: {filename}")
print("\n" + "="*80)
print("PROCHAINES ÉTAPES:")
print("="*80)
print("1. Valider ces recommandations:")
print("   .venv/Scripts/python.exe valider_simple.py")
print("\n2. Afficher les résultats:")
print("   .venv/Scripts/python.exe afficher_validations.py")
print("="*80)

client.close()

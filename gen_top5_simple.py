#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génération Top 5 SIMPLE - Sans aggregation"""

from pymongo import MongoClient
from datetime import datetime
import json

print("="*80)
print("TOP 5 RAPIDE")
print("="*80)

# MongoDB
client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin', 
                    serverSelectionTimeoutMS=5000)
db = client['centralisation_db']

# Récupérer TOUTES les observations BRVM récentes
print("\nRecuperation donnees...")
all_obs = list(db.curated_observations.find(
    {'source': 'BRVM', 'value': {'$gt': 0}},
    {'key': 1, 'ts': 1, 'value': 1, 'attrs': 1}
).sort('ts', -1).limit(200))  # 200 plus récentes

print(f"Observations recuperees: {len(all_obs)}")

# Garder la plus récente par symbole
last_by_symbol = {}
for obs in all_obs:
    symbol = obs['key']
    if symbol not in last_by_symbol:
        last_by_symbol[symbol] = obs

print(f"Actions distinctes: {len(last_by_symbol)}")

# Scorer
scores = []
for symbol, obs in last_by_symbol.items():
    # Skip indices
    if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC', 'BRVM10.BC']:
        continue
    
    price = obs['value']
    attrs = obs.get('attrs', {})
    
    # Score
    score = 50
    raisons = []
    
    var = attrs.get('variation', 0)
    if var > 2:
        score += 20
        raisons.append(f"+{var:.1f}%")
    elif var > 0:
        score += 10
    
    vol = attrs.get('volume', 0)
    if vol > 1000:
        score += 15
        raisons.append(f"Vol {vol}")
    elif vol > 500:
        score += 8
    
    ytd = attrs.get('ytd', 0)
    if ytd > 10:
        score += 15
        raisons.append(f"YTD +{ytd:.1f}%")
    elif ytd > 0:
        score += 5
    
    secteur = attrs.get('sector', attrs.get('secteur', '?'))
    if secteur in ['Telecommunications', 'Finance', 'Banque']:
        score += 10
        raisons.append(secteur)
    
    scores.append({
        'symbol': symbol,
        'score': score,
        'prix': price,
        'variation': var,
        'volume': vol,
        'ytd': ytd,
        'secteur': secteur,
        'raisons': raisons
    })

# Top 5
top5 = sorted(scores, key=lambda x: x['score'], reverse=True)[:5]

print("\n" + "="*80)
print("TOP 5 RECOMMANDATIONS")
print("="*80)

for i, r in enumerate(top5, 1):
    print(f"\n{i}. {r['symbol']:<15} Score: {r['score']}/100")
    print(f"   Prix:      {r['prix']:>10,.0f} FCFA")
    print(f"   Variation: {r['variation']:>+10.2f}%")
    print(f"   Volume:    {r['volume']:>10,}")
    print(f"   Secteur:   {r['secteur']}")
    if r['raisons']:
        print(f"   Points:    {', '.join(r['raisons'])}")

# Sauvegarder
output = {
    'date_generation': datetime.now().isoformat(),
    'nb_actions_analysees': len(scores),
    'top5': [{
        'symbol': r['symbol'],
        'score': r['score'],
        'prix_actuel': r['prix'],
        'variation_jour': r['variation'],
        'volume': r['volume'],
        'secteur': r['secteur'],
        'ytd': r['ytd'],
        'stop_loss': round(r['prix'] * 0.93),
        'take_profit_1': round(r['prix'] * 1.15),
        'take_profit_2': round(r['prix'] * 1.30),
        'take_profit_3': round(r['prix'] * 1.50),
        'raisons': r['raisons']
    } for r in top5]
}

filename = f"top5_nlp_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Sauvegarde: {filename}")
print("\n" + "="*80)
print("VALIDATION:")
print(f"  .venv/Scripts/python.exe valider_simple.py")
print("="*80)

client.close()

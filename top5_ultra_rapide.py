#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TOP 5 ULTRA RAPIDE - Dernières données disponibles"""

from pymongo import MongoClient
from datetime import datetime
import json

print("="*80)
print("GENERATION TOP 5 - DONNEES DISPONIBLES")
print("="*80)

# MongoDB
client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin', 
                    serverSelectionTimeoutMS=5000)
db = client['centralisation_db']

# Prendre les données les plus récentes (peu importe la date exacte)
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$sort': {'ts': -1}},
    {'$group': {
        '_id': '$key',
        'last_ts': {'$first': '$ts'},
        'price': {'$first': '$value'},
        'attrs': {'$first': '$attrs'}
    }},
    {'$match': {'price': {'$gt': 0}}}
]

print("\nAnalyse des actions BRVM...")
actions = list(db.curated_observations.aggregate(pipeline, allowDiskUse=True))
print(f"Actions trouvees: {len(actions)}")

# Scorer
scores = []
for action in actions:
    symbol = action['_id']
    
    # Skip indices
    if 'BRVM' in symbol and ('.BC' in symbol or 'BRVM-' in symbol):
        if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC', 'BRVM10.BC']:
            continue
    
    price = action['price']
    attrs = action.get('attrs', {})
    
    # Scoring simple
    score = 50  # Base
    raisons = []
    
    # Variation
    var = attrs.get('variation', 0)
    if var > 2:
        score += 20
        raisons.append(f"Hausse {var:.1f}%")
    elif var > 0:
        score += 10
    
    # Volume
    vol = attrs.get('volume', 0)
    if vol > 1000:
        score += 15
        raisons.append(f"Volume {vol}")
    elif vol > 500:
        score += 8
    
    # YTD
    ytd = attrs.get('ytd', 0)
    if ytd > 10:
        score += 15
        raisons.append(f"YTD +{ytd:.1f}%")
    elif ytd > 0:
        score += 5
    
    # Secteur
    secteur = attrs.get('sector', attrs.get('secteur', 'Autre'))
    if secteur in ['Telecommunications', 'Finance', 'Banque', 'Agriculture']:
        score += 10
        raisons.append(secteur)
    
    # Market cap
    mcap = attrs.get('market_cap', 0)
    if mcap > 50_000_000_000:
        score += 10
        raisons.append("Grande cap")
    
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
    print(f"   Variation: {r['variation']:>10.2f}%")
    print(f"   Volume:    {r['volume']:>10,}")
    print(f"   Secteur:   {r['secteur']}")
    if r['raisons']:
        print(f"   Points:    {', '.join(r['raisons'][:3])}")

# Sauvegarde
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

print(f"\n✅ Fichier sauvegarde: {filename}")
print("\n" + "="*80)
print("VALIDATION:")
print("="*80)
print(f".venv/Scripts/python.exe valider_simple.py")
print("="*80)

client.close()

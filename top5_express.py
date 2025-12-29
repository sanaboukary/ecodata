#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Top 5 Express - Pattern Valider Simple"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import json

print("="*80)
print("TOP 5 EXPRESS")
print("="*80)

# Même connexion que valider_simple.py
client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin')
db = client['centralisation_db']

# Date récente
today = datetime.now()
date_check = today.strftime('%Y-%m-%d')

print(f"\nRecherche donnees du {date_check}...")

# Données du jour
obs_today = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': date_check,
    'value': {'$gt': 0}
}))

if len(obs_today) == 0:
    # Essayer J-1
    yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    obs_today = list(db.curated_observations.find({
        'source': 'BRVM',
        'ts': yesterday,
        'value': {'$gt': 0}
    }))
    date_check = yesterday
    print(f"Utilisation donnees J-1: {date_check}")

if len(obs_today) == 0:
    # Essayer J-2
    day2 = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    obs_today = list(db.curated_observations.find({
        'source': 'BRVM',
        'ts': day2,
        'value': {'$gt': 0}
    }))
    date_check = day2
    print(f"Utilisation donnees J-2: {date_check}")

print(f"Actions trouvees: {len(obs_today)}")

# Scorer
scores = []
for obs in obs_today:
    symbol = obs['key']
    
    # Skip indices
    if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC']:
        continue
    
    price = obs['value']
    attrs = obs.get('attrs', {})
    
    score = 50
    raisons = []
    
    # Variation
    var = attrs.get('variation', 0)
    if var > 2:
        score += 25
        raisons.append(f"Hausse {var:.1f}%")
    elif var > 0:
        score += 12
    elif var < -5:
        score -= 20
    
    # Volume
    vol = attrs.get('volume', 0)
    if vol > 1000:
        score += 15
        raisons.append(f"Volume {vol}")
    elif vol > 500:
        score += 8
    
    # YTD
    ytd = attrs.get('ytd', 0)
    if ytd > 15:
        score += 20
        raisons.append(f"YTD +{ytd:.1f}%")
    elif ytd > 5:
        score += 10
    
    # Secteur
    secteur = attrs.get('sector', attrs.get('secteur', '?'))
    if secteur in ['Telecommunications', 'Finance', 'Banque', 'Agriculture']:
        score += 10
    
    # Market cap
    mcap = attrs.get('market_cap', 0)
    if mcap > 100_000_000_000:
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
        'mcap': mcap,
        'raisons': raisons
    })

# Top 5
top5 = sorted(scores, key=lambda x: x['score'], reverse=True)[:5]

print("\n" + "="*80)
print("TOP 5 RECOMMANDATIONS")
print("="*80)
print(f"Date: {date_check}\n")

for i, r in enumerate(top5, 1):
    print(f"{i}. {r['symbol']:<12} Score: {r['score']}/100")
    print(f"   Prix:      {r['prix']:>10,.0f} FCFA")
    print(f"   Variation: {r['variation']:>+10.2f}%")
    print(f"   Volume:    {r['volume']:>10,}")
    print(f"   Secteur:   {r['secteur']}")
    if r['raisons']:
        print(f"   Points:    {', '.join(r['raisons'])}\n")

# Sauvegarde
output = {
    'date_generation': datetime.now().isoformat(),
    'date_donnees': date_check,
    'nb_actions_analysees': len(scores),
    'top5': [{
        'symbol': r['symbol'],
        'score': r['score'],
        'prix_actuel': r['prix'],
        'variation_jour': r['variation'],
        'volume': r['volume'],
        'secteur': r['secteur'],
        'ytd': r['ytd'],
        'market_cap': r['mcap'],
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

print(f"Sauvegarde: {filename}")
print("\n" + "="*80)
print("VALIDATION:")
print("  .venv/Scripts/python.exe valider_simple.py")
print("="*80)

client.close()

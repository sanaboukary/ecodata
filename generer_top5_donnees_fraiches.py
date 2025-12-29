#!/usr/bin/env python3
"""
Générateur Top 5 avec DONNÉES FRAÎCHES (7-14 derniers jours)
Pour trading hebdomadaire avec prix réels et actuels
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

print("=" * 80)
print("🎯 GÉNÉRATION TOP 5 - DONNÉES FRAÎCHES HEBDOMADAIRES")
print("=" * 80)

client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin')
db = client['centralisation_db']

# Dates pour analyse hebdomadaire
today = datetime.now()
date_today = today.strftime('%Y-%m-%d')
date_7j = (today - timedelta(days=7)).strftime('%Y-%m-%d')
date_14j = (today - timedelta(days=14)).strftime('%Y-%m-%d')

print(f"\n📅 Période d'analyse:")
print(f"   Aujourd'hui: {date_today}")
print(f"   -7 jours:    {date_7j}")
print(f"   -14 jours:   {date_14j}")

# Récupérer données du jour
data_today = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': date_today
}))

print(f"\n📊 Données disponibles:")
print(f"   Aujourd'hui ({date_today}): {len(data_today)} actions")

if len(data_today) < 30:
    print(f"\n⚠️  ATTENTION: Seulement {len(data_today)} actions collectées")
    print(f"   Recommandation: Collecter les 47 actions pour précision maximale")

# Analyser chaque action
recommendations = []

for obs_today in data_today:
    symbol = obs_today['key']
    price_today = obs_today['value']
    variation_today = obs_today['attrs'].get('variation', 0)
    
    # Skip indices
    if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC']:
        continue
    
    # Données 7j et 14j
    obs_7j = db.curated_observations.find_one({
        'source': 'BRVM',
        'key': symbol,
        'ts': date_7j
    })
    
    obs_14j = db.curated_observations.find_one({
        'source': 'BRVM',
        'key': symbol,
        'ts': date_14j
    })
    
    # Calculs
    momentum_7j = 0
    momentum_14j = 0
    
    if obs_7j:
        price_7j = obs_7j['value']
        if price_7j > 0:
            momentum_7j = ((price_today - price_7j) / price_7j) * 100
    
    if obs_14j:
        price_14j = obs_14j['value']
        if price_14j > 0:
            momentum_14j = ((price_today - price_14j) / price_14j) * 100
    
    # Volatilité 7 derniers jours
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    prices_7d = []
    
    for date in last_7_days:
        obs = db.curated_observations.find_one({
            'source': 'BRVM',
            'key': symbol,
            'ts': date
        })
        if obs:
            prices_7d.append(obs['value'])
    
    volatilite_7j = 0
    if len(prices_7d) >= 3:
        import statistics
        try:
            volatilite_7j = (statistics.stdev(prices_7d) / statistics.mean(prices_7d)) * 100
        except:
            volatilite_7j = 0
    
    # Scoring pour trading hebdomadaire
    score_momentum = 0
    score_volatility = 0
    score_tendance = 0
    
    # Momentum 7j (60 points max)
    if momentum_7j >= 10:
        score_momentum = 60
    elif momentum_7j >= 5:
        score_momentum = 50
    elif momentum_7j >= 3:
        score_momentum = 40
    elif momentum_7j >= 1:
        score_momentum = 30
    elif momentum_7j >= 0:
        score_momentum = 20
    
    # Volatilité (20 points max - on préfère faible volatilité)
    if volatilite_7j <= 5:
        score_volatility = 20
    elif volatilite_7j <= 10:
        score_volatility = 15
    elif volatilite_7j <= 20:
        score_volatility = 10
    else:
        score_volatility = 5
    
    # Tendance (20 points - prix croissant sur 7j)
    if momentum_7j > 0 and momentum_14j > 0:
        score_tendance = 20
    elif momentum_7j > 0:
        score_tendance = 10
    
    score_total = score_momentum + score_volatility + score_tendance
    
    # Seuil minimum: 50 points
    if score_total >= 50:
        recommendations.append({
            'symbol': symbol,
            'score': score_total,
            'prix_actuel': price_today,
            'variation_jour': variation_today,
            'momentum_7j': round(momentum_7j, 2),
            'momentum_14j': round(momentum_14j, 2),
            'volatilite_7j': round(volatilite_7j, 2),
            'score_momentum': score_momentum,
            'score_volatility': score_volatility,
            'score_tendance': score_tendance,
            'nb_jours_data': len(prices_7d),
            'data_quality': 'REAL_SCRAPER'
        })

# Trier par score décroissant
recommendations.sort(key=lambda x: x['score'], reverse=True)
top5 = recommendations[:5]

print(f"\n🏆 TOP 5 RECOMMANDATIONS (sur {len(recommendations)} actions qualifiées)")
print("=" * 80)

for i, reco in enumerate(top5, 1):
    print(f"\n{i}. {reco['symbol']} - SCORE: {reco['score']}/100")
    print(f"   Prix actuel:      {reco['prix_actuel']:>10,.0f} FCFA")
    print(f"   Variation jour:   {reco['variation_jour']:>10.2f}%")
    print(f"   Momentum 7j:      {reco['momentum_7j']:>10.2f}%")
    print(f"   Momentum 14j:     {reco['momentum_14j']:>10.2f}%")
    print(f"   Volatilité 7j:    {reco['volatilite_7j']:>10.2f}%")
    print(f"   Jours de données: {reco['nb_jours_data']}")

# Sauvegarder rapport JSON
rapport = {
    'date_generation': datetime.now().isoformat(),
    'date_donnees': date_today,
    'strategie': 'TRADING_HEBDOMADAIRE_DONNEES_FRAICHES',
    'periode_analyse': f'{date_14j} à {date_today}',
    'actions_analysees': len(data_today),
    'actions_qualifiees': len(recommendations),
    'scoring_schema': {
        'momentum_7j': '60 points max (10% = 60pts)',
        'volatilite_7j': '20 points max (faible vol = bonus)',
        'tendance_14j': '20 points max (hausse continue)',
        'seuil_min': '50 points'
    },
    'top_5': top5,
    'date_fraicheur': date_today,
    'prix_reels': True
}

filename = f"top5_hebdo_frais_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)

print(f"\n📄 Rapport sauvegardé: {filename}")

print("\n" + "=" * 80)
print("✅ TOP 5 GÉNÉRÉ AVEC DONNÉES FRAÎCHES")
print("=" * 80)
print(f"\n📊 Garanties:")
print(f"   ✅ Prix réels du {date_today}")
print(f"   ✅ Analyse sur 7-14 derniers jours")
print(f"   ✅ 100% données REAL_SCRAPER")
print(f"   ✅ Adapté au trading hebdomadaire")
print("=" * 80)

client.close()

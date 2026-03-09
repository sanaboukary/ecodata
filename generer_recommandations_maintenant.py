#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Générateur de Recommandations IA - Exécution Immédiate
Analyse technique + fondamentale + sentiment pour recommandations Buy/Hold/Sell
"""
import os
import sys
import django
from datetime import datetime, timedelta
import statistics
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# 📊 DICTIONNAIRE DE SENTIMENT
SENTIMENT_WORDS = {
    'positive': [
        'hausse', 'augmentation', 'croissance', 'amélioration', 'progression',
        'bénéfice', 'profit', 'dividende', 'record', 'succès', 'performance',
        'solide', 'excellent', 'fort', 'dynamique', 'expansion'
    ],
    'negative': [
        'baisse', 'diminution', 'chute', 'perte', 'déficit', 'recul',
        'difficultés', 'crise', 'suspension', 'retard', 'échec', 'faible',
        'dégradation', 'risque', 'incertitude'
    ]
}

def calculate_rsi(prices, period=14):
    """Calcul RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def analyser_sentiment_publications(db, symbol, jours_recents=90):
    """
    Analyser sentiment des publications récentes pour une action
    """
    date_limite = (datetime.now() - timedelta(days=jours_recents)).strftime('%Y-%m-%d')
    
    # Récupérer publications récentes mentionnant le symbole
    publications = list(db.curated_observations.find({
        'source': 'BRVM_PUBLICATIONS',
        'ts': {'$gte': date_limite},
        '$or': [
            {'attrs.emetteur': {'$regex': symbol, '$options': 'i'}},
            {'attrs.titre': {'$regex': symbol, '$options': 'i'}},
            {'attrs.description': {'$regex': symbol, '$options': 'i'}}
        ]
    }).sort('ts', -1))
    
    if not publications:
        return {
            'score': 0,
            'publications_count': 0,
            'sentiment': 'neutral',
            'impact': 'NONE'
        }
    
    # Calculer score de sentiment
    score_total = 0
    positive_count = 0
    negative_count = 0
    
    for pub in publications:
        titre = pub.get('attrs', {}).get('titre', '').lower()
        description = pub.get('attrs', {}).get('description', '').lower()
        texte = f"{titre} {description}"
        
        # Compter mots positifs/négatifs
        pos_count = sum(1 for word in SENTIMENT_WORDS['positive'] if word in texte)
        neg_count = sum(1 for word in SENTIMENT_WORDS['negative'] if word in texte)
        
        if pos_count > neg_count:
            score_total += (pos_count - neg_count) * 10
            positive_count += 1
        elif neg_count > pos_count:
            score_total -= (neg_count - pos_count) * 10
            negative_count += 1
    
    # Déterminer sentiment global
    if score_total > 20:
        sentiment = 'positive'
        impact = 'HIGH' if score_total > 50 else 'MEDIUM'
    elif score_total < -20:
        sentiment = 'negative'
        impact = 'HIGH' if score_total < -50 else 'MEDIUM'
    else:
        sentiment = 'neutral'
        impact = 'LOW'
    
    return {
        'score': score_total,
        'publications_count': len(publications),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'sentiment': sentiment,
        'impact': impact,
        'recent_publications': [
            {
                'titre': p.get('attrs', {}).get('titre', ''),
                'date': p.get('ts', '')[:10],
                'categorie': p.get('attrs', {}).get('categorie', '')
            }
            for p in publications[:3]  # Top 3 plus récentes
        ]
    }

def generer_recommandation(symbol, data, sentiment_analysis):
    """
    Génère recommandation BUY/HOLD/SELL basée sur:
    - RSI (surachat/survente)
    - SMA (tendance)
    - Volatilité
    - Liquidité
    - SENTIMENT des publications (NOUVEAU)
    """
    score = 0
    raisons = []
    
    # RSI Analysis
    rsi = data.get('rsi')
    if rsi:
        if rsi < 30:
            score += 2
            raisons.append(f"RSI survente ({rsi:.1f})")
        elif rsi > 70:
            score -= 2
            raisons.append(f"RSI surachat ({rsi:.1f})")
        elif 40 <= rsi <= 60:
            raisons.append(f"RSI neutre ({rsi:.1f})")
    
    # SMA Trend
    close = data.get('close')
    sma_20 = data.get('sma_20')
    sma_50 = data.get('sma_50')
    
    if close and sma_20 and sma_50:
        if close > sma_20 > sma_50:
            score += 2
            raisons.append("Tendance haussiere (prix > SMA20 > SMA50)")
        elif close < sma_20 < sma_50:
            score -= 2
            raisons.append("Tendance baissiere (prix < SMA20 < SMA50)")
        elif close > sma_20:
            score += 1
            raisons.append("Au-dessus SMA20")
    
    # Liquidité
    liquidity = data.get('liquidity_score', 0)
    if liquidity >= 8:
        score += 1
        raisons.append(f"Excellente liquidite ({liquidity}/10)")
    elif liquidity <= 3:
        score -= 1
        raisons.append(f"Faible liquidite ({liquidity}/10)")
    
    # Beta (volatilité relative)
    beta = data.get('beta')
    if beta:
        if beta > 1.5:
            raisons.append(f"Haute volatilite (beta={beta:.2f})")
        elif beta < 0.8:
            raisons.append(f"Faible volatilite (beta={beta:.2f})")
    
    # 🆕 SENTIMENT des publications (impact direct sur score)
    sentiment = sentiment_analysis.get('sentiment', 'neutral')
    sentiment_score = sentiment_analysis.get('score', 0)
    pub_count = sentiment_analysis.get('publications_count', 0)
    
    if pub_count > 0:
        if sentiment == 'positive':
            boost = 2 if sentiment_score > 50 else 1
            score += boost
            raisons.append(f"📰 Sentiment positif ({pub_count} pub., score: +{sentiment_score})")
        elif sentiment == 'negative':
            penalty = 2 if sentiment_score < -50 else 1
            score -= penalty
            raisons.append(f"📰 Sentiment negatif ({pub_count} pub., score: {sentiment_score})")
        else:
            raisons.append(f"📰 Sentiment neutre ({pub_count} publications)")
    
    # Décision finale (score ajusté avec sentiment)
    if score >= 3:
        decision = "BUY"
        confiance = min(90, 60 + score * 5)
    elif score <= -3:
        decision = "SELL"
        confiance = min(90, 60 + abs(score) * 5)
    else:
        decision = "HOLD"
        confiance = 50 + abs(score) * 5
    
    # Prix cible (simplifié)
    if close:
        if decision == "BUY":
            target = close * 1.15  # +15%
        elif decision == "SELL":
            target = close * 0.90  # -10%
        else:
            target = close * 1.05  # +5%
    else:
        target = None
    
    return {
        'symbol': symbol,
        'decision': decision,
        'confiance': confiance,
        'score': score,
        'raisons': raisons,
        'prix_actuel': close,
        'prix_cible': target,
        'rsi': rsi,
        'sentiment': sentiment_analysis,  # 🆕 Ajout données sentiment
        'sma_20': sma_20,
        'sma_50': sma_50,
        'liquidite': liquidity,
        'beta': beta,
        'timestamp': datetime.now().isoformat()
    }

def main():
    print("=" * 80)
    print("ANALYSE IA - GENERATION RECOMMANDATIONS BRVM")
    print("=" * 80)
    
    client, db = get_mongo_db()
    
    # Récupérer dernières données par action
    print("\n1. Recuperation donnees BRVM...")
    
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$sort': {'ts': -1}},
        {'$group': {
            '_id': '$key',
            'latest': {'$first': '$$ROOT'}
        }}
    ]
    
    actions_data = list(db.curated_observations.aggregate(pipeline))
    print(f"   {len(actions_data)} actions trouvees")
    
    # Générer recommandations
    print("\n2. Generation des recommandations IA...")
    print("-" * 80)
    
    recommandations = []
    
    for action in actions_data:
        symbol = action['_id']
        obs = action['latest']
        
        # Skip indices
        if 'BRVM_' in symbol:
            continue
        
        # 🆕 1. ANALYSER SENTIMENT des publications
        sentiment_analysis = analyser_sentiment_publications(db, symbol, jours_recents=90)
        
        # 2. Extraire données techniques
        data = {
            'close': obs.get('value'),
            'rsi': obs.get('attrs', {}).get('rsi'),
            'sma_20': obs.get('attrs', {}).get('sma_20'),
            'sma_50': obs.get('attrs', {}).get('sma_50'),
            'beta': obs.get('attrs', {}).get('beta'),
            'liquidity_score': obs.get('attrs', {}).get('liquidity_score', 5)
        }
        
        # 3. Générer recommandation (avec sentiment intégré)
        reco = generer_recommandation(symbol, data, sentiment_analysis)
        recommandations.append(reco)
        
        # Afficher
        icon = "🟢" if reco['decision'] == 'BUY' else "🔴" if reco['decision'] == 'SELL' else "🟡"
        print(f"\n{icon} {symbol:10s} - {reco['decision']:4s} ({reco['confiance']}% confiance)")
        print(f"   Prix actuel: {reco['prix_actuel']:,.0f} FCFA")
        if reco['prix_cible']:
            print(f"   Prix cible:  {reco['prix_cible']:,.0f} FCFA")
        print(f"   Score:       {reco['score']:+d}")
        
        # 🆕 Afficher sentiment si disponible
        if sentiment_analysis['publications_count'] > 0:
            sent = sentiment_analysis['sentiment']
            sent_icon = "📈" if sent == 'positive' else "📉" if sent == 'negative' else "📊"
            print(f"   {sent_icon} Sentiment: {sent.upper()} ({sentiment_analysis['publications_count']} publications)")
            if sentiment_analysis.get('recent_publications'):
                print(f"   Publications récentes:")
                for pub in sentiment_analysis['recent_publications'][:2]:
                    print(f"      • {pub['date']}: {pub['titre'][:60]}...")
        
        print(f"   Raisons:")
        for raison in reco['raisons']:
            print(f"      - {raison}")
    
    # Sauvegarder dans MongoDB
    print("\n" + "=" * 80)
    print("3. Sauvegarde des recommandations...")
    
    if recommandations:
        # Préparer pour MongoDB
        date_today = datetime.now().strftime('%Y-%m-%d')
        
        for reco in recommandations:
            db.curated_observations.insert_one({
                'source': 'AI_ANALYSIS',
                'dataset': 'RECOMMENDATIONS',
                'key': reco['symbol'],
                'ts': date_today,
                'value': reco['score'],
                'attrs': {
                    'decision': reco['decision'],
                    'confiance': reco['confiance'],
                    'prix_actuel': reco['prix_actuel'],
                    'prix_cible': reco['prix_cible'],
                    'raisons': reco['raisons'],
                    'rsi': reco['rsi'],
                    'sma_20': reco['sma_20'],
                    'sma_50': reco['sma_50'],
                    'liquidite': reco.get('liquidite'),
                    'beta': reco.get('beta'),
                    'sentiment': reco.get('sentiment', {}),  # 🆕 Sauvegarder sentiment
                    'timestamp': reco['timestamp']
                }
            })
        
        print(f"   {len(recommandations)} recommandations sauvegardees")
    
    # Résumé
    print("\n" + "=" * 80)
    print("RESUME DES RECOMMANDATIONS")
    print("=" * 80)
    
    buy_count = sum(1 for r in recommandations if r['decision'] == 'BUY')
    hold_count = sum(1 for r in recommandations if r['decision'] == 'HOLD')
    sell_count = sum(1 for r in recommandations if r['decision'] == 'SELL')
    
    print(f"\nTotal: {len(recommandations)} actions analysees")
    print(f"  BUY:  {buy_count:2d} ({buy_count/len(recommandations)*100:.1f}%)")
    print(f"  HOLD: {hold_count:2d} ({hold_count/len(recommandations)*100:.1f}%)")
    print(f"  SELL: {sell_count:2d} ({sell_count/len(recommandations)*100:.1f}%)")
    
    # Top 5 BUY
    print("\n" + "-" * 80)
    print("TOP 5 RECOMMANDATIONS BUY")
    print("-" * 80)
    
    top_buy = sorted([r for r in recommandations if r['decision'] == 'BUY'], 
                     key=lambda x: x['confiance'], reverse=True)[:5]
    
    for i, reco in enumerate(top_buy, 1):
        print(f"\n{i}. {reco['symbol']} - {reco['confiance']}% confiance")
        print(f"   Prix: {reco['prix_actuel']:,.0f} -> {reco['prix_cible']:,.0f} FCFA")
        print(f"   Raisons: {', '.join(reco['raisons'][:2])}")
    
    print("\n" + "=" * 80)
    print("ANALYSE IA TERMINEE")
    print("=" * 80)

if __name__ == '__main__':
    main()

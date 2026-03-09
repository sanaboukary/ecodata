#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trouver où sont stockées les publications et pourquoi les scores sont à 0
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("=" * 80)
print("CURATED_OBSERVATIONS (Examiner 10 derniers)")
print("=" * 80)

recent_obs = list(db.curated_observations.find(
    {},
    {'titre': 1, 'source': 1, 'date_collecte': 1, 'sentiment': 1, 'tickers': 1, 'score_base': 1}
).sort('date_collecte', -1).limit(10))

if recent_obs:
    for obs in recent_obs:
        titre = obs.get('titre', 'Sans titre')[:50]
        source = obs.get('source', '?')
        sentiment = obs.get('sentiment', '?')
        score = obs.get('score_base', '?')
        tickers = obs.get('tickers', [])
        date = obs.get('date_collecte', 'N/A')
        print(f"{date} | {source:12} | Sentiment: {sentiment:8} | Score: {score:6} | Tickers: {tickers} | {titre}")
else:
    print("Aucune observation")

print()
print("=" * 80)
print("RAW_EVENTS (Examiner 10 derniers)")
print("=" * 80)

recent_events = list(db.raw_events.find(
    {},
    {'titre': 1, 'type': 1, 'date': 1, 'ticker': 1, 'sentiment_score': 1}
).sort('date', -1).limit(10))

if recent_events:
    for event in recent_events:
        titre = event.get('titre', 'Sans titre')[:50]
        type_event = event.get('type', '?')
        ticker = event.get('ticker', '?')
        sentiment = event.get('sentiment_score', '?')
        date = event.get('date', 'N/A')
        print(f"{date} | {type_event:15} | Ticker: {ticker:6} | Sentiment: {sentiment:6} | {titre}")
else:
    print("Aucun event")

print()
print("=" * 80)
print("SEMANTIC_AGGREGATION_ACTIONS - EXISTE?")
print("=" * 80)

try:
    # Vérifier si la collection existe
    if 'semantic_aggregation_actions' in db.list_collection_names():
        agg_count = db.semantic_aggregation_actions.count_documents({})
        print(f"Collection existe avec {agg_count} documents")
        
        # Examiner quelques documents
        samples = list(db.semantic_aggregation_actions.find({}, {
            'ticker': 1, 
            'score_court_terme': 1, 
            'score_moyen_terme': 1, 
            'score_long_terme': 1,
            'publications_count': 1,
            'last_semantic_update': 1
        }).limit(10))
        
        for sample in samples:
            ticker = sample.get('ticker', '?')
            ct = sample.get('score_court_terme', 0)
            mt = sample.get('score_moyen_terme', 0)
            lt = sample.get('score_long_terme', 0)
            count = sample.get('publications_count', 0)
            update = sample.get('last_semantic_update', 'N/A')
            print(f"  {ticker:6} | CT: {ct:6.1f} | MT: {mt:6.1f} | LT: {lt:6.1f} | Pubs: {count:3} | Update: {update}")
    else:
        print("Collection N'EXISTE PAS!")
        print("  -> agregateur_semantique_actions.py ne fonctionne pas correctement")
except Exception as e:
    print(f"Erreur: {e}")

print()
print("=" * 80)
print("ANALYSE DU PIPELINE - FLUX DES DONNEES")
print("=" * 80)

# Vérifier le flux
print("1. COLLECTE:")
print(f"   - curated_observations: {db.curated_observations.count_documents({})} documents")
print(f"   - raw_events: {db.raw_events.count_documents({})} documents")

print()
print("2. ANALYSE SEMANTIQUE:")
if 'semantic_aggregation_actions' in db.list_collection_names():
    sem_agg = db.semantic_aggregation_actions.count_documents({})
    print(f"   - semantic_aggregation_actions: {sem_agg} documents")
    
    # Vérifier dates de mise à jour
    recent_update = db.semantic_aggregation_actions.find_one(
        {}, 
        {'ticker': 1, 'last_semantic_update': 1},
        sort=[('last_semantic_update', -1)]
    )
    if recent_update:
        print(f"   - Derniere mise a jour: {recent_update.get('last_semantic_update', 'N/A')} ({recent_update.get('ticker', '?')})")
else:
    print("   - semantic_aggregation_actions: N'EXISTE PAS")

print()
print("3. DECISIONS:")
decisions = db.decisions_finales_brvm.count_documents({})
print(f"   - decisions_finales_brvm: {decisions} documents")

# Examiner une décision
sample_decision = db.decisions_finales_brvm.find_one({}, {
    'ticker': 1,
    'wos_score': 1,
    'score_technique': 1,
    'score_semantique': 1,
    'timestamp': 1
})

if sample_decision:
    print()
    print("   Exemple de decision:")
    print(f"     Ticker: {sample_decision.get('ticker', '?')}")
    print(f"     WOS: {sample_decision.get('wos_score', 0)}")
    print(f"     Score technique: {sample_decision.get('score_technique', 0)}")
    print(f"     Score semantique: {sample_decision.get('score_semantique', 0)}")
    print(f"     Timestamp: {sample_decision.get('timestamp', 'N/A')}")

print()
print("=" * 80)
print("DIAGNOSTIC FINAL")
print("=" * 80)

if db.curated_observations.count_documents({}) > 0:
    print("Publications collectees: OUI (curated_observations)")
    
    # Vérifier si elles ont des sentiments
    with_sentiment = db.curated_observations.count_documents({'sentiment': {'$exists': True}})
    print(f"Publications avec sentiment: {with_sentiment}/{db.curated_observations.count_documents({})}")
    
    if 'semantic_aggregation_actions' not in db.list_collection_names():
        print()
        print("PROBLEME: agregateur_semantique_actions.py ne cree pas la collection!")
        print("  -> Verifier le script agregateur_semantique_actions.py")
    elif db.semantic_aggregation_actions.count_documents({}) == 0:
        print()
        print("PROBLEME: semantic_aggregation_actions existe mais est VIDE!")
        print("  -> L'agregateur ne trouve pas les publications")
    else:
        # Vérifier si les scores sont tous à 0
        non_zero = db.semantic_aggregation_actions.count_documents({
            '$or': [
                {'score_court_terme': {'$ne': 0}},
                {'score_moyen_terme': {'$ne': 0}},
                {'score_long_terme': {'$ne': 0}}
            ]
        })
        if non_zero == 0:
            print()
            print("PROBLEME: semantic_aggregation_actions existe mais TOUS les scores sont a 0!")
            print("  -> L'agregateur ne calcule pas correctement les scores")
            print("  -> Ou les publications n'ont pas de sentiment/score_base")

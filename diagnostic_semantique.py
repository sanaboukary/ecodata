#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic du système d'analyse sémantique
Pourquoi les scores sont-ils tous à 0.0 ?
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("=" * 80)
print("PUBLICATIONS DES 7 DERNIERS JOURS")
print("=" * 80)

# Publications récentes
week_ago = datetime.now() - timedelta(days=7)
recent_pubs = list(db.publications_brutes.find(
    {'date_collecte': {'$gte': week_ago}},
    {'titre': 1, 'source': 1, 'date_collecte': 1, 'sentiment_score': 1, 'tickers': 1}
).sort('date_collecte', -1).limit(10))

if recent_pubs:
    for pub in recent_pubs:
        titre = pub.get('titre', 'Sans titre')[:60]
        source = pub.get('source', '?')
        score = pub.get('sentiment_score', 'NON ANALYSE')
        tickers = pub.get('tickers', [])
        date = pub.get('date_collecte', 'N/A')
        print(f"{date} | {source:12} | Score: {score:6} | Tickers: {tickers} | {titre}")
else:
    print("AUCUNE publication collectee dans les 7 derniers jours!")

print()
print("=" * 80)
print("ANALYSE SEMANTIQUE - STATISTIQUES")
print("=" * 80)

# Actions avec scores non-zéro
actions_with_scores = list(db.semantic_aggregation_actions.find(
    {'$or': [
        {'score_court_terme': {'$ne': 0}},
        {'score_moyen_terme': {'$ne': 0}},
        {'score_long_terme': {'$ne': 0}}
    ]},
    {'ticker': 1, 'score_court_terme': 1, 'score_moyen_terme': 1, 'score_long_terme': 1, 'publications_count': 1}
))

if actions_with_scores:
    print(f"Actions avec scores NON-ZERO: {len(actions_with_scores)}")
    for action in actions_with_scores[:10]:
        ticker = action['ticker']
        ct = action.get('score_court_terme', 0)
        mt = action.get('score_moyen_terme', 0)
        lt = action.get('score_long_terme', 0)
        pubs = action.get('publications_count', 0)
        print(f"  {ticker:6} | CT: {ct:6.1f} | MT: {mt:6.1f} | LT: {lt:6.1f} | Pubs: {pubs}")
else:
    print("AUCUNE action avec score semantique > 0")
    print("  -> L'analyse semantique NE FONCTIONNE PAS!")

# Statistiques globales
total_pubs = db.publications_brutes.count_documents({})
pubs_with_sentiment = db.publications_brutes.count_documents({'sentiment_score': {'$exists': True}})
pubs_with_tickers = db.publications_brutes.count_documents({'tickers': {'$exists': True, '$ne': []}})

print()
print(f"Total publications en base: {total_pubs}")
print(f"Publications avec sentiment_score: {pubs_with_sentiment}")
print(f"Publications avec tickers identifies: {pubs_with_tickers}")
print(f"Publications SANS analyse: {total_pubs - pubs_with_sentiment}")

print()
print("=" * 80)
print("EXEMPLE DE PUBLICATIONS BRUTES (DEBUG)")
print("=" * 80)

# Examiner une publication en détail
sample_pub = db.publications_brutes.find_one(
    {'source': {'$in': ['BRVM', 'RICHBOURSE']}},
    {'titre': 1, 'source': 1, 'sentiment_score': 1, 'tickers': 1, 'contenu': 1}
)

if sample_pub:
    print(f"Source: {sample_pub.get('source', 'N/A')}")
    print(f"Titre: {sample_pub.get('titre', 'N/A')[:100]}")
    print(f"Sentiment: {sample_pub.get('sentiment_score', 'NON ANALYSE')}")
    print(f"Tickers: {sample_pub.get('tickers', [])}")
    contenu = sample_pub.get('contenu', '')
    if contenu:
        print(f"Contenu: {contenu[:200]}...")
    else:
        print("Contenu: VIDE")
else:
    print("Aucune publication trouvee")

print()
print("=" * 80)
print("RECOMMENDATIONS ACTUELLES")
print("=" * 80)

# Vérifier les recommandations
decisions = list(db.decisions_finales_brvm.find(
    {'horizon': 'SEMAINE'},
    {'ticker': 1, 'action': 1, 'wos_score': 1, 'score_technique': 1, 'score_semantique': 1, 'timestamp': 1}
).sort('wos_score', -1).limit(5))

if decisions:
    print(f"Nombre de decisions SEMAINE: {len(decisions)}")
    for dec in decisions:
        ticker = dec.get('ticker', '?')
        action = dec.get('action', '?')
        wos = dec.get('wos_score', 0)
        tech = dec.get('score_technique', 0)
        sem = dec.get('score_semantique', 0)
        ts = dec.get('timestamp', 'N/A')
        print(f"  {ticker:6} | {action:4} | WOS: {wos:5.1f} | Tech: {tech:5.1f} | Sem: {sem:5.1f} | {ts}")
    
    # Check si les scores sémantiques sont utilisés
    sem_scores = [d.get('score_semantique', 0) for d in decisions]
    if all(s == 0 for s in sem_scores):
        print()
        print("PROBLEME IDENTIFIE: Scores semantiques = 0 dans les decisions!")
        print("  -> Les recommandations sont basees UNIQUEMENT sur l'analyse technique")
        print("  -> C'est pourquoi elles ne changent jamais!")
else:
    print("Aucune decision trouvee")

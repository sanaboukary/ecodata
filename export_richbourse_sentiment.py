#!/usr/bin/env python3
"""
Exporte les titres, dates et scores d'analyse de sentiment pour toutes les publications RICHBOURSE avec texte intégral.
"""
from plateforme_centralisation.mongo import get_mongo_db
import csv

_, db = get_mongo_db()

with open('export_richbourse_sentiment.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Titre', 'Date', 'Score SEMAINE', 'Score MOIS', 'Score TRIMESTRE', 'Score ANNUEL', 'Risques', 'Raisons'])
    for doc in db.curated_observations.find({"source": "RICHBOURSE"}):
        attrs = doc.get('attrs', {})
        titre = attrs.get('titre', '')
        date = doc.get('ts', '')
        sentiment = attrs.get('semantic_v2', {})
        scores = sentiment.get('scores', {})
        risques = ', '.join(sentiment.get('risks', []))
        raisons = str(sentiment.get('reasons', {}))
        writer.writerow([
            titre,
            date,
            scores.get('SEMAINE', ''),
            scores.get('MOIS', ''),
            scores.get('TRIMESTRE', ''),
            scores.get('ANNUEL', ''),
            risques,
            raisons
        ])
print('Export terminé : export_richbourse_sentiment.csv')

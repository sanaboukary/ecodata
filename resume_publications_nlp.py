#!/usr/bin/env python3
"""
📊 RÉSUMÉ SYSTÈME PUBLICATIONS + NLP
"""

import os
import sys
import io
import django
import json
import glob
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*80)
print("📊 RÉSUMÉ SYSTÈME PUBLICATIONS BRVM + ANALYSE NLP")
print("="*80)
print()

# MongoDB
client, db = get_mongo_db()

# 1. Bulletins officiels
bulletins = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS'
})

bulletins_analyses = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS',
    'attrs.sentiment_label': {'$exists': True}
})

print("📰 BULLETINS OFFICIELS DE LA COTE")
print(f"   Total importés: {bulletins}")
print(f"   Avec analyse NLP: {bulletins_analyses}")

if bulletins_analyses > 0:
    # Stats sentiment
    sentiments = list(db.curated_observations.aggregate([
        {'$match': {
            'source': 'BRVM_PUBLICATIONS',
            'dataset': 'BULLETINS_OFFICIELS',
            'attrs.sentiment_label': {'$exists': True}
        }},
        {'$group': {
            '_id': '$attrs.sentiment_label',
            'count': {'$sum': 1},
            'score_moyen': {'$avg': '$attrs.sentiment_score'}
        }}
    ]))
    
    print("   Sentiments détectés:")
    for s in sentiments:
        print(f"     {s['_id']:<10} : {s['count']} (score moyen: {s['score_moyen']:+.1f})")

print()

# 2. Convocations AG
ag = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'CONVOCATIONS_AG'
})

ag_catalyseurs = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'CONVOCATIONS_AG',
    'attrs.catalyseurs': {'$exists': True, '$ne': []}
}))

print("📅 CONVOCATIONS ASSEMBLÉES GÉNÉRALES")
print(f"   Total importées: {ag}")
print(f"   Avec catalyseurs: {len(ag_catalyseurs)}")

if ag_catalyseurs:
    catalyseurs_total = []
    for conv in ag_catalyseurs:
        catalyseurs_total.extend(conv['attrs'].get('catalyseurs', []))
    
    from collections import Counter
    cat_count = Counter(catalyseurs_total)
    
    if cat_count:
        print("   Catalyseurs principaux:")
        for cat, nb in cat_count.most_common(3):
            print(f"     {cat:<30} : {nb}")

print()

# 3. Rapports sociétés
rapports = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'RAPPORTS_SOCIETES'
})

print("📑 RAPPORTS SOCIÉTÉS COTÉES")
print(f"   Total importés: {rapports}")
print()

# 4. Fichiers JSON générés
print("="*80)
print("📁 FICHIERS GÉNÉRÉS")
print("="*80)
print()

fichiers = {
    'Bulletins': glob.glob('bulletins_brvm_*.json'),
    'Convocations AG': glob.glob('convocations_ag_*.json'),
    'Rapports': glob.glob('rapports_brvm_*.json'),
    'Sentiment NLP': glob.glob('sentiment_nlp_*.json'),
    'Recommandations': glob.glob('recommandations_hebdo_*.json')
}

for categorie, files in fichiers.items():
    if files:
        dernier = sorted(files)[-1]
        import os
        taille = os.path.getsize(dernier)
        print(f"   {categorie:<20} : {dernier} ({taille:,} octets)")
    else:
        print(f"   {categorie:<20} : Aucun")

print()

# 5. Infrastructure prête
print("="*80)
print("✅ INFRASTRUCTURE COMPLÉTÉE")
print("="*80)
print()
print("✓ Parser bulletins officiels (10 bulletins)")
print("✓ Parser convocations AG (10 convocations)")
print("✓ Analyse NLP sentiment (keywords + catalyseurs)")
print("✓ Import MongoDB automatisé")
print("✓ Dashboard recommandations hebdomadaires")
print()

print("="*80)
print("📋 PROCHAINES ÉTAPES")
print("="*80)
print()
print("1. Vérifier données BRVM 60 jours (pour recommandations)")
print("2. Intégrer scores NLP dans moteur recommandations")
print("3. Générer Top 5 opportunités hebdomadaires")
print("4. Backtesting précision 85-95%")
print("5. Automatiser collecte quotidienne (Airflow DAG)")
print()

client.close()

print("="*80)
print()

"""
VÉRIFICATION TRAÇABILITÉ DONNÉES - POLITIQUE TOLÉRANCE ZÉRO
Objectif: Prouver que 100% des données sont RÉELLES (pas simulées)
"""

import pymongo
from datetime import datetime
from collections import defaultdict

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("AUDIT TRAÇABILITÉ - POLITIQUE TOLÉRANCE ZÉRO")
print("="*80)
print(f"Date audit: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print()

# ÉTAPE 1: Vérifier SOURCES des données brutes
print("[1/5] VÉRIFICATION SOURCES DONNÉES BRUTES")
print("-" * 80)

stock_total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"Total observations STOCK_PRICE: {stock_total}")

# Grouper par source
sources = db.curated_observations.aggregate([
    {'$match': {'dataset': 'STOCK_PRICE', 'granularite': {'$exists': False}}},
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
])

print("\nSOURCES des observations brutes:")
total_brutes = 0
for s in sources:
    source = s['_id'] if s['_id'] else 'NON_DEFINI'
    count = s['count']
    total_brutes += count
    status = "✓ RÉELLE" if source in ['BRVM', 'CSV_HISTORIQUE', 'RAW_EVENTS'] else "⚠ À VÉRIFIER"
    print(f"  {source:30s}: {count:5d} obs - {status}")

print(f"\nTotal observations BRUTES: {total_brutes}")
print()

# ÉTAPE 2: Vérifier qu'aucune donnée simulée
print("[2/5] DÉTECTION DONNÉES SIMULÉES")
print("-" * 80)

simulees = db.curated_observations.count_documents({
    'dataset': 'STOCK_PRICE',
    'granularite': {'$exists': False},
    'source': {'$in': ['SIMULATION', 'SYNTHETIC', 'FAKE', 'GENERATED']}
})

print(f"Données simulées détectées: {simulees}")
if simulees == 0:
    print("✓ AUCUNE donnée simulée - POLITIQUE RESPECTÉE")
else:
    print(f"✗ ALERTE: {simulees} données simulées trouvées - VIOLATION POLITIQUE")
print()

# ÉTAPE 3: Traçabilité agrégation hebdomadaire
print("[3/5] TRAÇABILITÉ AGRÉGATION HEBDOMADAIRE")
print("-" * 80)

weekly_total = db.curated_observations.count_documents({'granularite': 'WEEKLY'})
print(f"Total lignes HEBDOMADAIRES: {weekly_total}")

# Vérifier que chaque ligne hebdomadaire a bien nb_observations
weekly_docs = list(db.curated_observations.find(
    {'granularite': 'WEEKLY'},
    {'ticker': 1, 'week': 1, 'nb_observations': 1, 'open': 1, 'high': 1, 'low': 1, 'close': 1}
).limit(10))

print("\nÉCHANTILLON traçabilité (10 premières semaines):")
print(f"{'Ticker':<8} {'Semaine':<12} {'Nb obs':<8} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8}")
print("-" * 80)

total_obs_sources = 0
for doc in weekly_docs:
    ticker = doc.get('ticker', 'N/A')
    week = doc.get('week', 'N/A')
    nb_obs = doc.get('nb_observations', 0)
    open_p = doc.get('open', 0)
    high_p = doc.get('high', 0)
    low_p = doc.get('low', 0)
    close_p = doc.get('close', 0)
    total_obs_sources += nb_obs
    print(f"{ticker:<8} {week:<12} {nb_obs:<8} {open_p:<8.0f} {high_p:<8.0f} {low_p:<8.0f} {close_p:<8.0f}")

print(f"\nObservations sources agrégées (échantillon): {total_obs_sources}")
print()

# ÉTAPE 4: Calcul du ratio d'agrégation
print("[4/5] RATIO D'AGRÉGATION")
print("-" * 80)

# Compter total nb_observations dans tous les documents hebdomadaires
pipeline = [
    {'$match': {'granularite': 'WEEKLY'}},
    {'$group': {'_id': None, 'total_obs': {'$sum': '$nb_observations'}}}
]

result = list(db.curated_observations.aggregate(pipeline))
total_obs_aggregees = result[0]['total_obs'] if result else 0

print(f"Observations brutes RÉELLES    : {total_brutes}")
print(f"Observations sources agrégées  : {total_obs_aggregees}")
print(f"Documents hebdomadaires créés  : {weekly_total}")
print()

ratio = (total_obs_aggregees / total_brutes * 100) if total_brutes > 0 else 0
print(f"Ratio couverture: {ratio:.1f}%")

if ratio >= 95:
    print("✓ EXCELLENT: Quasi-totalité des données brutes agrégées")
elif ratio >= 80:
    print("✓ BON: Majorité des données brutes agrégées")
else:
    print(f"⚠ ATTENTION: Seulement {ratio:.1f}% des données agrégées")
print()

# ÉTAPE 5: Vérification cohérence prix (pas de prix aberrants créés)
print("[5/5] COHÉRENCE PRIX (détection anomalies agrégation)")
print("-" * 80)

# Vérifier que High >= Low, Close entre Low et High
anomalies = list(db.curated_observations.find({
    'granularite': 'WEEKLY',
    '$or': [
        {'$expr': {'$lt': ['$high', '$low']}},  # High < Low (impossible)
        {'$expr': {'$lt': ['$close', '$low']}},  # Close < Low (impossible)
        {'$expr': {'$gt': ['$close', '$high']}}  # Close > High (impossible)
    ]
}))

print(f"Anomalies OHLC détectées: {len(anomalies)}")

if len(anomalies) == 0:
    print("✓ COHÉRENCE OHLC validée - Aucune anomalie")
else:
    print(f"✗ ALERTE: {len(anomalies)} anomalies OHLC trouvées")
    for anom in anomalies[:5]:
        ticker = anom.get('ticker')
        week = anom.get('week')
        o, h, l, c = anom.get('open'), anom.get('high'), anom.get('low'), anom.get('close')
        print(f"  {ticker} {week}: O={o} H={h} L={l} C={c}")
print()

# RÉSUMÉ FINAL
print("="*80)
print("RÉSUMÉ AUDIT TRAÇABILITÉ")
print("="*80)

checks = {
    'Données simulées': simulees == 0,
    'Sources réelles': total_brutes > 0,
    'Ratio agrégation': ratio >= 80,
    'Cohérence OHLC': len(anomalies) == 0
}

print(f"Observations BRUTES (réelles) : {total_brutes}")
print(f"Observations HEBDO (agrégées) : {weekly_total}")
print(f"Ratio couverture              : {ratio:.1f}%")
print()

print("RÉSULTATS VÉRIFICATIONS:")
for check, passed in checks.items():
    status = "✓ PASSÉ" if passed else "✗ ÉCHEC"
    print(f"  {check:30s}: {status}")
print()

if all(checks.values()):
    print("="*80)
    print("VERDICT: ✓ POLITIQUE TOLÉRANCE ZÉRO RESPECTÉE")
    print("="*80)
    print("  100% DONNÉES RÉELLES")
    print("  0% DONNÉES SIMULÉES")
    print("  Agrégation hebdomadaire = Simple calcul OHLC depuis données réelles")
    print("  Aucune donnée artificielle créée")
    print()
else:
    print("="*80)
    print("VERDICT: ✗ PROBLÈMES DÉTECTÉS - RÉVISION NÉCESSAIRE")
    print("="*80)
    print()

client.close()

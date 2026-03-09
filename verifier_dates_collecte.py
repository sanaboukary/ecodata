"""Vérifier les vraies dates de collecte"""
from pymongo import MongoClient
from collections import Counter
from datetime import datetime

c = MongoClient('mongodb://localhost:27017/')
db = c.centralisation_db

# Examiner toutes les observations STOCK_PRICE (pas les agrégées)
obs = list(db.curated_observations.find({
    'dataset': 'STOCK_PRICE',
    'granularite': {'$exists': False}
}))

print("="*70)
print("ANALYSE DES DATES RÉELLES DE COLLECTE")
print("="*70)
print(f"\nTotal observations: {len(obs)}")

# Extraire les dates
dates_list = []
for o in obs:
    ts = o.get('ts') or o.get('timestamp')
    if ts:
        if isinstance(ts, str):
            date_part = ts[:10]  # YYYY-MM-DD
        else:
            date_part = str(ts)[:10]
        dates_list.append(date_part)

dates = Counter(dates_list)

print(f"Dates uniques: {len(dates)}")

if dates:
    print(f"\nPLAGE DE DATES:")
    print(f"  Première: {min(dates.keys())}")
    print(f"  Dernière: {max(dates.keys())}")
    
    # Calculer nombre de semaines réelles
    try:
        first = datetime.strptime(min(dates.keys()), '%Y-%m-%d')
        last = datetime.strptime(max(dates.keys()), '%Y-%m-%d')
        days = (last - first).days
        weeks = days // 7 + 1
        print(f"\nDURÉE DE COLLECTE:")
        print(f"  {days} jours")
        print(f"  ≈ {weeks} semaines")
    except:
        pass
    
    print(f"\nDISTRIBUTION PAR DATE (top 20):")
    for date, count in sorted(dates.items())[:20]:
        print(f"  {date}: {count:4d} observations")

# Vérifier les données hebdomadaires créées
weekly = db.curated_observations.count_documents({'granularite': 'WEEKLY'})
print(f"\n{'='*70}")
print(f"DONNÉES HEBDOMADAIRES CRÉÉES: {weekly}")

# Examiner les semaines créées
weeks_created = db.curated_observations.distinct('week', {'granularite': 'WEEKLY'})
print(f"Semaines distinctes: {len(weeks_created)}")

if len(weeks_created) <= 30:
    print(f"\nSemaines créées:")
    for w in sorted(weeks_created):
        count = db.curated_observations.count_documents({'granularite': 'WEEKLY', 'week': w})
        print(f"  {w}: {count} actions")
else:
    print(f"\nPremières 15 semaines:")
    for w in sorted(weeks_created)[:15]:
        count = db.curated_observations.count_documents({'granularite': 'WEEKLY', 'week': w})
        print(f"  {w}: {count} actions")
    print(f"\nDernières 15 semaines:")
    for w in sorted(weeks_created)[-15:]:
        count = db.curated_observations.count_documents({'granularite': 'WEEKLY', 'week': w})
        print(f"  {w}: {count} actions")

c.close()

from pymongo import MongoClient
db = MongoClient()['centralisation_db']

weeks = sorted(db.prices_weekly.distinct('week'))
print(f"Semaines: {len(weeks)}")
print(f"{weeks[0]} -> {weeks[-1]}")
print()

for week in weeks:
    total = db.prices_weekly.count_documents({'week': week})
    with_ind = db.prices_weekly.count_documents({'week': week, 'indicators_computed': True})
    pct = 100 * with_ind / total if total > 0 else 0
    quality = "EXCELLENT" if pct >= 90 else "BON" if pct >= 70 else "MOYEN" if pct >= 50 else "FAIBLE"
    print(f"{week} {total:2d}A {with_ind:2d}IND {pct:5.1f}% {quality}")

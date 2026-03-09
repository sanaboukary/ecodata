import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

print("=== 1. DATES DANS LES PUBLICATIONS ===")
# Champs de date dans curated_observations
sample = list(db.curated_observations.find(
    {'source': {'$in': ['BRVM_PUBLICATION', 'RICHBOURSE']}},
    {'source': 1, 'ts': 1, 'attrs': 1, 'key': 1}
).sort('ts', -1).limit(10))

for d in sample:
    print(f"  source={d.get('source','?'):20s} ts={d.get('ts','ABSENT')[:25] if d.get('ts') else 'ABSENT'}")

print()
# Stats sur les champs de date
total = db.curated_observations.count_documents({'source': {'$in': ['BRVM_PUBLICATION', 'RICHBOURSE']}})
with_ts = db.curated_observations.count_documents({'source': {'$in': ['BRVM_PUBLICATION', 'RICHBOURSE']}, 'ts': {'$exists': True, '$ne': None}})
print(f"  Total publications BRVM/RICHBOURSE : {total}")
print(f"  Avec 'ts' renseigne : {with_ts} ({with_ts/total*100:.0f}%)" if total > 0 else "  Aucune")

# Types de dates
import re
future_dates = db.curated_observations.count_documents({'ts': {'$regex': '^2026-12-31'}})
print(f"  Dates sentinelle 2026-12-31 restantes : {future_dates}")

print()
print("=== 2. SCORES SEMANTIQUES REELS ===")
# Scores dans AGREGATION_SEMANTIQUE_ACTION
sem_docs = list(db.curated_observations.find(
    {'dataset': 'AGREGATION_SEMANTIQUE_ACTION'},
    {'symbol': 1, 'score_semantique_7j': 1, 'signal_explosion': 1, 'catalyseur_recent_72h': 1}
).sort('score_semantique_7j', -1))

print(f"  Docs AGREGATION_SEMANTIQUE : {len(sem_docs)}")
nonzero = [d for d in sem_docs if d.get('score_semantique_7j', 0) != 0]
print(f"  Scores != 0 : {len(nonzero)}")
print(f"  Scores = 0  : {len(sem_docs) - len(nonzero)}")
print()
for d in sem_docs[:15]:
    score = d.get('score_semantique_7j', 0)
    expl = '[EXPL]' if d.get('signal_explosion') else ''
    cat = '[CAT]' if d.get('catalyseur_recent_72h') else ''
    print(f"  {d.get('symbol','?'):8s} score_7j={score:+7.2f} {expl}{cat}")

print()
print("=== 3. NORMALISATION DANS TOP5 ===")
print("  Formule actuelle : sem_norm = clamp((score_7j + 30) / 60 * 100, 0, 100)")
print("  Contribution TOP5 : 0.10 x sem_norm")
print("  Exemples :")
for val in [-30, -15, 0, 5, 10, 15, 20, 30]:
    norm = max(0, min(100, (val + 30) / 60 * 100))
    contrib = 0.10 * norm
    print(f"    score_7j={val:+4.0f} -> sem_norm={norm:5.1f} -> contrib TOP5={contrib:4.1f}pts")

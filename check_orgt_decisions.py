#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

# Chercher les BUY decisions actives (non archivées)
query = {'decision': 'BUY', 'archived': {'$ne': True}}
docs = list(db.decisions_finales_brvm.find(
    query,
    {'symbol': 1, 'decision': 1, 'horizon': 1, 'score_total_mf': 1, 'mf_label': 1, '_id': 0}
).sort('score_total_mf', -1))

print(f"BUY actifs (non archivés) : {len(docs)}")
for d in docs[:20]:
    print(f"  {d.get('symbol','?'):<8} horizon={d.get('horizon','?'):<8} MF={d.get('score_total_mf','N/A')}")

print()

# Total par décision
all_decisions = list(db.decisions_finales_brvm.find({'archived': {'$ne': True}}, {'decision': 1}))
from collections import Counter
cnt = Counter(d.get('decision') for d in all_decisions)
print(f"Distribution décisions (actives) : {dict(cnt)}")

print()

# Chercher ORGT spécifiquement
orgt_docs = list(db.decisions_finales_brvm.find({'symbol': 'ORGT'}))
print(f"ORGT dans decisions_finales_brvm : {len(orgt_docs)} doc(s)")
for d in orgt_docs:
    print(f"  decision={d.get('decision')} horizon={d.get('horizon')} MF={d.get('score_total_mf')} archived={d.get('archived')} date={d.get('date_decision','?')}")

print()

# Chercher les symboles avec MF >= 70 (SWING_FORT ou EXPLOSION)
strong = list(db.decisions_finales_brvm.find(
    {'score_total_mf': {'$gte': 70}, 'archived': {'$ne': True}},
    {'symbol': 1, 'decision': 1, 'score_total_mf': 1, 'mf_label': 1, 'horizon': 1}
).sort('score_total_mf', -1))
print(f"Symboles MF >= 70 (actifs) : {len(strong)}")
for d in strong:
    print(f"  {d.get('symbol','?'):<8} decision={d.get('decision','?'):<6} MF={d.get('score_total_mf','?'):.1f} {d.get('mf_label','?')} horizon={d.get('horizon','?')}")

#!/usr/bin/env python3
"""Afficher TOP 10 ALPHA V2"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

docs = list(db.curated_observations.find({
    'dataset': 'ALPHA_V2_SHADOW',
    'attrs.categorie': {'$ne': 'REJECTED'}
}).sort('value', -1).limit(10))

week_source = None
week_target = None
week_target_start = None
if docs:
    attrs0 = docs[0].get('attrs', {}) or {}
    week_source = attrs0.get('week_source')
    week_target = attrs0.get('week_target')
    week_target_start = attrs0.get('week_target_start')

print("\n" + "=" * 85)
print("TOP 10 ALPHA V2 (Shadow - Formule 4 Facteurs Hebdomadaire)")  
print("=" * 85)
if week_source and week_target:
    print(f"📅 Semaine source (données) : {week_source}")
    print(f"🎯 Semaine cible (trading)  : {week_target} (début {week_target_start})")
print(f"{'#':>3} | {'Symbol':<6} | {'Alpha':>6} | {'Cat':<6} | {'EM':>5} | {'VS':>5} | {'Ev':>5} | {'Sent':>5}")
print("-" * 85)

for i, d in enumerate(docs, 1):
    details = d['attrs']['details']
    print(f"{i:3d} | {d['key']:<6} | {d['value']:6.1f} | {d['attrs']['categorie']:<6} | "
          f"{details.get('early_momentum', 0):5.1f} | {details.get('volume_spike', 0):5.1f} | "
          f"{details.get('event', 0):5.1f} | {details.get('sentiment', 0):5.1f}")

print("=" * 85)
print("\n📊 COMPARAISON avec V1 (pipeline_brvm.py):")
print("-" * 85)
print("V1 TOP 3 (référence): SEMC (82.7), UNXC (75.4), SIBC (64.0)")
print()

# Symboles v2 TOP 10
symbols_v2 = [d['key'] for d in docs]
print(f"V2 TOP 10: {', '.join(symbols_v2)}")
print()

# Actions communes
v1_top3 = ['SEMC', 'UNXC', 'SIBC']
common = [s for s in symbols_v2 if s in v1_top3]
print(f"✅ Actions communes (V1 TOP 3 ∩ V2 TOP 10): {', '.join(common) if common else 'Aucune'}")

# Scores v2 pour actions v1
print("\n📈 Scores V2 pour TOP 3 V1:")
for symbol in v1_top3:
    doc = db.curated_observations.find_one({'dataset': 'ALPHA_V2_SHADOW', 'key': symbol})
    if doc:
        alpha_v2 = doc['value']
        cat = doc['attrs']['categorie']
        rank = symbols_v2.index(symbol) + 1 if symbol in symbols_v2[:10] else '?'
        print(f"  • {symbol}: Alpha V2 = {alpha_v2:.1f} ({cat}) - Rang V2: #{rank}")
    else:
        print(f"  • {symbol}: Pas de score V2 (rejeté ou erreur)")

print("\n" + "=" * 85)
print("FORMULE V2: 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment")
print("=" * 85 + "\n")

client.close()

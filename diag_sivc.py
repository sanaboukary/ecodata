#!/usr/bin/env python3
"""Diagnostic complet du signal SIVC — pourquoi rejeté par decision_finale_brvm."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# 1. Signal brut stocké par analyse_ia_simple.py (ANALYSE_TECHNIQUE_SETUP)
print("=" * 60)
print("SIGNAL BRUT — analyse_ia_simple.py")
print("=" * 60)
docs = list(db.curated_observations.find(
    {"symbol": "SIVC", "dataset": "ANALYSE_TECHNIQUE_SETUP"},
    sort=[("timestamp", -1)],
    limit=1
))
if docs:
    attrs = docs[0].get("attrs", {})
    for k, v in attrs.items():
        print(f"  {k}: {v}")
else:
    print("  Aucun doc ANALYSE_TECHNIQUE_SETUP pour SIVC")

# 2. Décision finale stockée (decisions_finales_brvm)
print()
print("=" * 60)
print("DECISION FINALE STOCKEE — decisions_finales_brvm")
print("=" * 60)
d = db.decisions_finales_brvm.find_one(
    {"symbol": "SIVC", "archived": {"$ne": True}}
)
if d:
    keys_interest = [
        "decision", "horizon", "signal", "motif_principal",
        "motifs_bloquants", "score_wos", "atr_pct", "rsi",
        "rs_percentile", "confidence", "generated_by",
        "score_total_mf", "mf_label", "setup_type",
        "prix_entree", "stop", "gain_attendu"
    ]
    for k in keys_interest:
        if k in d:
            print(f"  {k}: {d[k]}")
else:
    print("  Aucune decision active pour SIVC")

# 3. Données brutes prix last week (pour diagnostic ATR/RSI)
print()
print("=" * 60)
print("PRIX RECENTS — prices_weekly (5 dernières semaines)")
print("=" * 60)
semaines = list(db.prices_weekly.find(
    {"symbol": "SIVC"},
    sort=[("date", -1)],
    limit=5
))
for s in semaines:
    print(f"  {s.get('date','?')}  close={s.get('close','?')}  "
          f"vol={s.get('volume','?')}  "
          f"atr={s.get('atr_pct','?')}")

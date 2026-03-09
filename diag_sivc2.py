#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

doc = db.curated_observations.find_one(
    {"dataset": "AGREGATION_SEMANTIQUE_ACTION", "$or": [{"key": "SIVC"}, {"attrs.symbol": "SIVC"}]}
)
if not doc:
    print("PAS DE DOC AGREGATION_SEMANTIQUE_ACTION pour SIVC")
else:
    attrs = doc.get("attrs", {})
    print("=== AGREGATION_SEMANTIQUE_ACTION / SIVC ===")
    print(f"signal          : {attrs.get('signal')}")
    print(f"motif_principal : {attrs.get('motif_principal')}")
    print(f"score           : {attrs.get('score')}")
    print(f"rsi             : {attrs.get('rsi')}")
    print(f"atr_pct         : {attrs.get('atr_pct')}")
    print(f"SMA5            : {attrs.get('SMA5')}")
    print(f"SMA10           : {attrs.get('SMA10')}")
    print()
    print("-- Details (liste des flags) --")
    for d in (attrs.get("details") or []):
        marker = " <<<< BLOQUANT" if "[BLOQUANT]" in d else ""
        print(f"  {d}{marker}")

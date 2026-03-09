#!/usr/bin/env python3
"""Diagnostic état MongoDB pour pipeline BRVM"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

try:
    import django
    django.setup()
    from plateforme_centralisation.mongo import get_mongo_db
    
    _, db = get_mongo_db()
    
    print("\n=== DIAGNOSTIC MONGODB ===\n")
    
    # Collections critiques
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
    decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE", "decision": "BUY"}))
    top5 = list(db.top5_weekly_brvm.find())
    
    print(f"AGREGATION_SEMANTIQUE_ACTION : {len(analyses)} documents")
    print(f"decisions_finales_brvm (BUY) : {len(decisions)} documents")
    print(f"top5_weekly_brvm             : {len(top5)} documents")
    
    if analyses:
        print("\n--- Exemple analyse ---")
        ex = analyses[0]
        attrs = ex.get("attrs", {})
        print(f"Symbol: {attrs.get('symbol')}")
        print(f"Score CT: {attrs.get('score_ct', attrs.get('score', 0))}")
        print(f"Volume: {attrs.get('volume_moyen', attrs.get('volume', 0))}")
    
    if decisions:
        print("\n--- Exemple decision ---")
        d = decisions[0]
        print(f"Symbol: {d.get('symbol')}")
        print(f"Classe: {d.get('classe')}")
        print(f"WOS: {d.get('wos')}")
        print(f"Confidence: {d.get('confidence')}")
        print(f"RR: {d.get('rr')}")
    
    print("\n")
    
except Exception as e:
    print(f"\nERREUR: {e}\n")
    import traceback
    traceback.print_exc()

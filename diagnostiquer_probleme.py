#!/usr/bin/env python3
"""
Diagnostiquer pourquoi le système dit "données insuffisantes"
"""

from pymongo import MongoClient
from collections import Counter

def main():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    print("=" * 80)
    print("DIAGNOSTIC DONNÉES INSUFFISANTES")
    print("=" * 80)
    
    # 1. État global
    print("\n[1] ÉTAT GLOBAL DE LA BASE")
    print(f"  prices_weekly      : {db.prices_weekly.count_documents({})}")
    print(f"  prices_daily       : {db.prices_daily.count_documents({})}")
    print(f"  curated_observations: {db.curated_observations.count_documents({})}")
    
    # 2. Nombre de semaines par action
    print("\n[2] ANALYSE PAR ACTION (prices_weekly)")
    pipeline = [
        {'$group': {'_id': '$symbol', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    result = list(db.prices_weekly.aggregate(pipeline))
    
    print(f"\n  Total actions      : {len(result)}")
    
    ok_count = sum(1 for r in result if r['count'] >= 5)
    ko_count = sum(1 for r in result if r['count'] < 5)
    
    print(f"  Actions >= 5 sem   : {ok_count} ✓")
    print(f"  Actions < 5 sem    : {ko_count} ✗")
    
    # 3. Actions problématiques
    if ko_count > 0:
        print("\n[3] ACTIONS AVEC DONNÉES INSUFFISANTES (<5 semaines)")
        ko_actions = [r for r in result if r['count'] < 5]
        for r in ko_actions[:30]:
            print(f"    {r['_id']:10s}: {r['count']} semaines")
    
    # 4. Top 10 actions avec plus de données
    print("\n[4] TOP 10 ACTIONS (plus de données)")
    for r in result[:10]:
        print(f"    {r['_id']:10s}: {r['count']} semaines")
    
    # 5. Vérifier les semaines disponibles
    print("\n[5] SEMAINES DISPONIBLES")
    weeks = db.prices_weekly.distinct('week')
    weeks_sorted = sorted(weeks)
    print(f"  Nombre de semaines : {len(weeks_sorted)}")
    if weeks_sorted:
        print(f"  Première semaine   : {weeks_sorted[0]}")
        print(f"  Dernière semaine   : {weeks_sorted[-1]}")
        print(f"  Dernières 5 semaines: {weeks_sorted[-5:]}")
    
    # 6. Vérifier si indicators_computed
    print("\n[6] INDICATEURS CALCULÉS")
    with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    total = db.prices_weekly.count_documents({})
    print(f"  Avec indicateurs   : {with_indicators}/{total} ({100*with_indicators/total:.1f}%)")
    
    # 7. Vérifier les prix de clôture
    print("\n[7] QUALITÉ DES DONNÉES")
    docs_with_close = db.prices_weekly.count_documents({'close': {'$exists': True, '$ne': None}})
    docs_with_volume = db.prices_weekly.count_documents({'volume': {'$exists': True}})
    print(f"  Avec prix 'close'  : {docs_with_close}/{total}")
    print(f"  Avec volume        : {docs_with_volume}/{total}")
    
    # 8. Tester une action spécifique
    print("\n[8] TEST ACTION SPÉCIFIQUE")
    sample_action = result[0]['_id'] if result else None
    if sample_action:
        docs = list(db.prices_weekly.find({'symbol': sample_action}).sort('week', 1))
        print(f"  Action testée      : {sample_action}")
        print(f"  Nombre de semaines : {len(docs)}")
        if docs:
            print(f"  Première semaine   : {docs[0].get('week')}")
            print(f"  Dernière semaine   : {docs[-1].get('week')}")
            print(f"  Dernier prix       : {docs[-1].get('close')}")
            print(f"  Indicators computed: {docs[-1].get('indicators_computed')}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

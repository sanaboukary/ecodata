#!/usr/bin/env python3
"""
Diagnostic complet des données disponibles pour le système de recommandation
"""

from plateforme_centralisation.mongo import get_mongo_db
from collections import Counter

def main():
    _, db = get_mongo_db()
    
    print("=" * 80)
    print("DIAGNOSTIC DES DONNEES BRVM")
    print("=" * 80)
    
    # 1. Statistiques générales
    print("\n1. COLLECTIONS MONGODB")
    print("-" * 80)
    collections = {
        "prices_weekly": db.prices_weekly.count_documents({}),
        "prices_daily": db.prices_daily.count_documents({}),
        "curated_observations": db.curated_observations.count_documents({}),
        "publications_officielles": db.publications_officielles.count_documents({}),
        "decisions_finales_brvm": db.decisions_finales_brvm.count_documents({})
    }
    
    for coll, count in collections.items():
        print(f"  {coll:30s} : {count:6d} documents")
    
    # 2. Analyse prices_weekly par action
    print("\n2. DONNEES HEBDOMADAIRES (prices_weekly)")
    print("-" * 80)
    
    actions = db.prices_weekly.distinct("symbol")
    indices_brvm = ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']
    actions = [a for a in actions if a and a not in indices_brvm]
    
    print(f"  Total actions tradables : {len(actions)}\n")
    
    semaines_par_action = {}
    for symbol in sorted(actions):
        count = db.prices_weekly.count_documents({"symbol": symbol})
        semaines_par_action[symbol] = count
        
        # Récupérer les semaines disponibles
        docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", 1))
        semaines = [d.get("week") for d in docs if d.get("week")]
        
        status = "OK" if count >= 5 else "INSUFFISANT"
        marker = "✓" if count >= 5 else "✗"
        
        if semaines:
            premiere = semaines[0]
            derniere = semaines[-1]
            print(f"  {marker} {symbol:8s} : {count:3d} semaines  [{premiere} → {derniere}]  {status}")
        else:
            print(f"  {marker} {symbol:8s} : {count:3d} semaines  [Pas de dates]  {status}")
    
    # 3. Statistiques résumées
    print("\n3. RESUME")
    print("-" * 80)
    
    actions_ok = [s for s, c in semaines_par_action.items() if c >= 5]
    actions_insuffisantes = [s for s, c in semaines_par_action.items() if c < 5]
    
    print(f"  Actions avec ≥ 5 semaines (UTILISABLES)   : {len(actions_ok)}")
    print(f"  Actions avec < 5 semaines (INSUFFISANT)   : {len(actions_insuffisantes)}")
    
    if actions_insuffisantes:
        print(f"\n  Actions insuffisantes : {', '.join(sorted(actions_insuffisantes))}")
    
    # 4. Analyse par semaine (coverage)
    print("\n4. COUVERTURE PAR SEMAINE")
    print("-" * 80)
    
    semaines = db.prices_weekly.distinct("week")
    semaines_sorted = sorted(semaines) if semaines else []
    
    print(f"  Semaines disponibles : {len(semaines_sorted)}")
    if semaines_sorted:
        print(f"  Première semaine     : {semaines_sorted[0]}")
        print(f"  Dernière semaine     : {semaines_sorted[-1]}")
    
    # Compter combien d'actions par semaine
    print("\n  Actions par semaine (dernières 10):")
    for week in semaines_sorted[-10:]:
        count = db.prices_weekly.count_documents({"week": week})
        print(f"    {week} : {count:3d} actions")
    
    # 5. Vérifier AGREGATION_SEMANTIQUE_ACTION
    print("\n5. AGREGATION SEMANTIQUE (pour décision finale)")
    print("-" * 80)
    
    agg_count = db.curated_observations.count_documents({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
    print(f"  Documents AGREGATION_SEMANTIQUE_ACTION : {agg_count}")
    
    if agg_count > 0:
        sample = db.curated_observations.find_one({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
        if sample and "attrs" in sample:
            attrs = sample["attrs"]
            print(f"\n  Exemple de champs disponibles dans attrs :")
            for key in sorted(attrs.keys())[:15]:
                print(f"    - {key}")
    
    # 6. Dernière collecte
    print("\n6. DERNIERE COLLECTE")
    print("-" * 80)
    
    derniere_weekly = db.prices_weekly.find_one(sort=[("week", -1)])
    if derniere_weekly:
        print(f"  Dernière semaine collectée : {derniere_weekly.get('week')} ({derniere_weekly.get('symbol')})")
    
    derniere_daily = db.prices_daily.find_one(sort=[("date", -1)])
    if derniere_daily:
        print(f"  Dernier jour collecté      : {derniere_daily.get('date')} ({derniere_daily.get('symbol')})")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TERMINE")
    print("=" * 80)

if __name__ == "__main__":
    main()

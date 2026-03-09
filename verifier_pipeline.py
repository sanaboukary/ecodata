#!/usr/bin/env python3
"""
Verifier l'etat des collections MongoDB pour comprendre
pourquoi "donnees insuffisantes"
"""

from pymongo import MongoClient

def main():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    print("=" * 80)
    print("VERIFICATION PIPELINE COMPLET")
    print("=" * 80)
    
    # 1. Publications collectees
    print("\n[ETAPE 1] COLLECTE PUBLICATIONS")
    pubs = db.publications_officielles.count_documents({})
    print(f"  Publications officielles    : {pubs}")
    
    # 2. Analyses semantiques
    print("\n[ETAPE 2] ANALYSE SEMANTIQUE")
    semantiques = db.curated_observations.count_documents({
        "attrs.semantic_tags": {"$exists": True}
    })
    print(f"  Documents avec tags semantiques : {semantiques}")
    
    # 3. Agregation par action
    print("\n[ETAPE 3] AGREGATION PAR ACTION")
    agregation = db.curated_observations.count_documents({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION"
    })
    print(f"  Documents agregation action : {agregation}")
    if agregation > 0:
        sample = db.curated_observations.find_one({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
        print(f"  Exemple action              : {sample.get('attrs', {}).get('symbol')}")
    
    # 4. Analyses IA techniques
    print("\n[ETAPE 4] ANALYSE TECHNIQUE IA")
    brvm_ai = db.brvm_ai_analysis.count_documents({})
    print(f"  Documents brvm_ai_analysis  : {brvm_ai}")
    
    # 5. Decisions finales
    print("\n[ETAPE 5] DECISIONS FINALES")
    decisions_weekly = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE"})
    decisions_total = db.decisions_finales_brvm.count_documents({})
    print(f"  Decisions hebdomadaires     : {decisions_weekly}")
    print(f"  Decisions totales           : {decisions_total}")
    
    if decisions_total > 0:
        derniere = db.decisions_finales_brvm.find_one(sort=[("_id", -1)])
        print(f"  Derniere decision           : {derniere.get('symbol')} - {derniere.get('decision')}")
    
    # 6. Prix hebdomadaires avec indicateurs
    print("\n[ETAPE 6] INDICATEURS TECHNIQUES")
    total_weekly = db.prices_weekly.count_documents({})
    with_indicators = db.prices_weekly.count_documents({"indicators_computed": True})
    pct = (100 * with_indicators / total_weekly) if total_weekly > 0 else 0
    print(f"  Total documents weekly      : {total_weekly}")
    print(f"  Avec indicateurs calcules   : {with_indicators} ({pct:.1f}%)")
    
    # Diagnostic
    print("\n" + "=" * 80)
    print("DIAGNOSTIC")
    print("=" * 80)
    
    problemes = []
    
    if pubs == 0:
        problemes.append("Pas de publications collectees")
    
    if agregation == 0:
        problemes.append("Agregation semantique n'a pas ete executee")
    
    if with_indicators < total_weekly * 0.9:  # Moins de 90%
        problemes.append(f"Indicateurs manquants ({with_indicators}/{total_weekly})")
    
    if decisions_weekly == 0:
        problemes.append("Aucune decision hebdomadaire generee")
    
    if problemes:
        print("\n[!] PROBLEMES DETECTES:")
        for i, p in enumerate(problemes, 1):
            print(f"  {i}. {p}")
        
        print("\n[SOLUTION] Reexecuter le pipeline complet:")
        print("  python pipeline_brvm.py")
    else:
        print("\n[OK] Pipeline complet fonctionnel")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

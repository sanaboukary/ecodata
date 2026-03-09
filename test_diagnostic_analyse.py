#!/usr/bin/env python3
"""
Tester l'analyse IA pour comprendre pourquoi "données insuffisantes"
"""

from pymongo import MongoClient
import sys

def get_mongo_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    return client, db

def main():
    print("=" * 80)
    print("TEST ANALYSE IA - DIAGNOSTIC DONNÉES INSUFFISANTES")
    print("=" * 80)
    
    _, db = get_mongo_db()
    
    # Récupérer les actions
    actions = db.prices_weekly.distinct("symbol")
    indices_brvm = ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']
    actions = [a for a in actions if a and a not in indices_brvm]
    
    print(f"\n[1] {len(actions)} actions BRVM tradables détectées")
    
    # Tester chaque action
    print("\n[2] ANALYSE PAR ACTION")
    actions_ok = []
    actions_ko = []
    
    for symbol in sorted(actions):
        docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", 1))
        nb_semaines = len(docs)
        
        # Vérifier le minimum de 5 semaines
        if nb_semaines < 5:
            actions_ko.append((symbol, nb_semaines, "< 5 semaines"))
            print(f"  {symbol:10s}: {nb_semaines:2d} semaines [KO] (< 5 minimum)")
            continue
        
        # Extraire les prix
        prix = [d.get("close") for d in docs if d.get("close")]
        if len(prix) < 5:
            actions_ko.append((symbol, nb_semaines, "prix insuffisants"))
            print(f"  {symbol:10s}: {nb_semaines:2d} semaines, {len(prix)} prix [KO] (prix manquants)")
            continue
        
        # Vérifier si indicators_computed
        last_doc = docs[-1]
        has_indicators = last_doc.get("indicators_computed", False)
        
        if has_indicators:
            actions_ok.append((symbol, nb_semaines, "avec indicateurs"))
            print(f"  {symbol:10s}: {nb_semaines:2d} semaines [OK] (indicateurs calcules)")
        else:
            actions_ok.append((symbol, nb_semaines, "sans indicateurs"))
            print(f"  {symbol:10s}: {nb_semaines:2d} semaines [!!] (indicateurs manquants)")
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"  Actions analysables (>= 5 sem) : {len(actions_ok)}")
    print(f"  Actions insuffisantes          : {len(actions_ko)}")
    
    # Détail des actions OK
    avec_indic = sum(1 for _, _, status in actions_ok if "avec" in status)
    sans_indic = sum(1 for _, _, status in actions_ok if "sans" in status)
    print(f"\n  Avec indicateurs calculés      : {avec_indic}")
    print(f"  Sans indicateurs (à calculer)  : {sans_indic}")
    
    # Conclusion
    print("\n" + "=" * 80)
    print("DIAGNOSTIC")
    print("=" * 80)
    if sans_indic > 0:
        print(f"[!] PROBLEME IDENTIFIE:")
        print(f"  {sans_indic} actions n'ont PAS leurs indicateurs techniques calcules")
        print(f"  (RSI, ATR, volatilite, etc.)")
        print(f"\n  SOLUTION:")
        print(f"  1. Executer le script de recalcul des indicateurs")
        print(f"  2. Ou modifier analyse_ia_simple.py pour calculer a la volee")
    else:
        print(f"[OK] Toutes les actions ont leurs indicateurs calcules")

if __name__ == "__main__":
    main()

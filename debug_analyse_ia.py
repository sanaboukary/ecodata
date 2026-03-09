#!/usr/bin/env python3
"""Debug analyse_ia_simple.py"""

import sys
import traceback
from pymongo import MongoClient

try:
    print("1. Connexion MongoDB...")
    db = MongoClient('mongodb://localhost:27017').centralisation_db
    print("   ✓ Connecté\n")
    
    print("2. Chargement des actions hebdomadaires...")
    actions = db.curated_observations.distinct("ticker", {
        "dataset": "STOCK_PRICE",
        "granularite": "WEEKLY"
    })
    indices_brvm = ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']
    actions = [a for a in actions if a and a not in indices_brvm]
    print(f"   ✓ {len(actions)} actions trouvées\n")
    
    print("3. Import du module RecommendationEngine...")
    from analyse_ia_simple import RecommendationEngine
    print("   ✓ Module importé\n")
    
    print("4. Initialisation de l'engine...")
    engine = RecommendationEngine(db)
    print("   ✓ Engine créé\n")
    
    print("5. Test analyse d'une action (ABJC)...")
    result = engine.analyser_une_action("ABJC")
    print(f"   Résultat: {result}\n")
    
    if result:
        print("   ✓ Analyse réussie!")
        print(f"   Signal: {result.get('signal')}")
        print(f"   Score: {result.get('score')}")
        print(f"   Confiance: {result.get('confiance')}%")
    else:
        print("   ✗ Analyse échouée (donnéesinsuffisantes?)")
    
except Exception as e:
    print(f"\n❌ ERREUR:")
    print(f"   {str(e)}\n")
    print("Traceback complet:")
    traceback.print_exc()

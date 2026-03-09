#!/usr/bin/env python3
"""Test rapide ALPHA v2 - TOP 5 uniquement"""

import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("\n=== TEST RAPIDE ALPHA V2 ===\n")
    
    # Vérifier si v2 existe déjà
    count_v2 = db.curated_observations.count_documents({"dataset": "ALPHA_V2_SHADOW"})
    
    if count_v2 > 0:
        print(f"Donnees v2 trouvees: {count_v2} actions\n")
        
        # Afficher TOP 5 v2
        top5_v2 = list(db.curated_observations.find({
            "dataset": "ALPHA_V2_SHADOW",
            "attrs.categorie": {"$ne": "REJECTED"}
        }).sort("value", -1).limit(5))
        
        print("TOP 5 ALPHA V2 (Shadow Mode):")
        print("-" * 50)
        for i, doc in enumerate(top5_v2, 1):
            symbol = doc["key"]
            alpha = doc["value"]
            cat = doc.get("attrs", {}).get("categorie", "?")
            print(f"{i}. {symbol:6s} | Alpha v2: {alpha:5.1f} | {cat}")
        
        print("\nSauvegarde: MongoDB collection ALPHA_V2_SHADOW")
        
    else:
        print("Aucune donnee v2 trouvee")
        print("\nExecuter: .venv\\Scripts\\python.exe alpha_score_v2_shadow.py")
    
    # Vérifier v1 aussi
    print("\n" + "=" * 50)
    count_v1 = db.curated_observations.count_documents({"dataset": "DECISION_FINALE_BRVM"})
    
    if count_v1 > 0:
        print(f"Donnees v1 (production): {count_v1} actions\n")
        
        top5_v1 = list(db.curated_observations.find({
            "dataset": "DECISION_FINALE_BRVM"
        }).sort("attrs.ALPHA_SCORE", -1).limit(5))
        
        print("TOP 5 ALPHA V1 (Production):")
        print("-" * 50)
        for i, doc in enumerate(top5_v1, 1):
            symbol = doc["key"]
            alpha = doc.get("attrs", {}).get("ALPHA_SCORE", 0)
            signal = doc.get("attrs", {}).get("SIGNAL", "?")
            print(f"{i}. {symbol:6s} | Alpha v1: {alpha:5.1f} | {signal}")
    else:
        print("Aucune donnee v1 (production) trouvee\n")
    
    # Comparaison
    if count_v1 > 0 and count_v2 > 0:
        symbols_v1 = set(d["key"] for d in top5_v1)
        symbols_v2 = set(d["key"] for d in top5_v2)
        
        common = symbols_v1.intersection(symbols_v2)
        turnover = len(symbols_v1.symmetric_difference(symbols_v2)) / 5.0
        
        print("\n" + "=" * 50)
        print("COMPARAISON V1 vs V2:")
        print("-" * 50)
        print(f"Symboles communs: {len(common)}/5")
        if common:
            print(f"                  {', '.join(sorted(common))}")
        print(f"Turnover:         {turnover*100:.0f}%")
    
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    main()

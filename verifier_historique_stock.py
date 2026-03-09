#!/usr/bin/env python3
"""Vérifier l'historique STOCK_PRICE pour calcul SMA/RSI"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

actions_buy = ["BICC", "SGBC", "SLBC", "SNTS", "STBC"]

print("\n" + "="*100)
print(" VERIFICATION HISTORIQUE STOCK_PRICE ".center(100))
print("="*100 + "\n")

for symbol in actions_buy:
    # Compter l'historique disponible
    count = db.curated_observations.count_documents({
        "source": "BRVM",
        "dataset": "STOCK_PRICE",
        "key": symbol
    })
    
    if count == 0:
        print(f"{symbol:6} : AUCUN HISTORIQUE")
        continue
    
    # Récupérer les derniers prix
    docs = list(db.curated_observations.find({
        "source": "BRVM",
        "dataset": "STOCK_PRICE",
        "key": symbol
    }).sort("ts", -1).limit(30))
    
    # Extraire les prix
    prix = []
    for d in docs:
        p = d.get("attrs", {}).get("cours") or d.get("value", 0)
        if p and p > 0:
            prix.append(p)
    
    prix.reverse()  # Ordre chronologique
    
    print(f"{symbol:6} : {count:3} jours d'historique | {len(prix):2} prix valides")
    
    if len(prix) >= 5:
        print(f"         Derniers prix : {prix[-5:]}")
        
        # Calculer SMA5 si possible
        if len(prix) >= 5:
            sma5 = sum(prix[-5:]) / 5
            print(f"         SMA5 calculable : {sma5:.2f}")
        
        # Calculer SMA10 si possible
        if len(prix) >= 10:
            sma10 = sum(prix[-10:]) / 10
            print(f"         SMA10 calculable : {sma10:.2f}")
        
        # RSI calculable ?
        if len(prix) >= 15:
            print(f"         RSI calculable : OUI (15+ prix)")
        else:
            print(f"         RSI calculable : NON (besoin 15+, a {len(prix)})")
    else:
        print(f"         INSUFFISANT pour SMA/RSI")
    
    print()

print("="*100 + "\n")

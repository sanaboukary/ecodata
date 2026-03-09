#!/usr/bin/env python3
"""Vérifier les données complètes de toutes les actions BUY"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Actions BUY détectées
actions_buy = ["BICC", "SGBC", "SLBC", "SNTS", "STBC"]

print("\n" + "="*100)
print(" VERIFICATION DONNEES COMPLETES ".center(100))
print("="*100 + "\n")

for symbol in actions_buy:
    analyse = db.curated_observations.find_one({
        "source": "AI_ANALYSIS",
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if not analyse:
        print(f"{symbol:6} : AUCUNE ANALYSE")
        continue
    
    attrs = analyse.get("attrs", {})
    
    print(f"\n--- {symbol} ---")
    print(f"  Prix actuel       : {attrs.get('prix_actuel', 'N/A')}")
    print(f"  Volatility (ATR%) : {attrs.get('volatility', 'N/A')}")
    print(f"  Volume            : {attrs.get('volume', 'N/A')}")
    print(f"  SMA5              : {attrs.get('SMA5', 'N/A')}")
    print(f"  SMA10             : {attrs.get('SMA10', 'N/A')}")
    print(f"  RSI               : {attrs.get('rsi', 'N/A')}")
    print(f"  Signal            : {attrs.get('signal', 'N/A')}")
    print(f"  Score             : {attrs.get('score', 'N/A')}")
    print(f"  Close prices      : {len(attrs.get('close_prices', [])) if attrs.get('close_prices') else 'N/A'} valeurs")
    
    # Vérifier complétude
    complet = all([
        attrs.get('prix_actuel'),
        attrs.get('volatility') is not None,
        attrs.get('SMA5'),
        attrs.get('SMA10'),
        attrs.get('rsi') is not None
    ])
    
    print(f"  Complétude        : {'OK COMPLET' if complet else 'INCOMPLET'}")

print("\n" + "="*100 + "\n")

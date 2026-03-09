#!/usr/bin/env python3
"""Vérifier données complètes des 5 BUY"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

buy_symbols = ["BICC", "SGBC", "SLBC", "SNTS", "STBC"]

print("\n" + "="*80)
print(" AUDIT DONNÉES COMPLÈTES - 5 ACTIONS BUY ".center(80))
print("="*80 + "\n")

for symbol in buy_symbols:
    analyse = db.curated_observations.find_one({
        "source": "AI_ANALYSIS",
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if not analyse:
        print(f"{symbol} : ANALYSE INTROUVABLE !")
        continue
    
    attrs = analyse.get("attrs", {})
    
    print(f"\n{symbol}")
    print("-" * 80)
    print(f"  signal           : {attrs.get('signal', 'N/A')}")
    print(f"  score            : {attrs.get('score', 'N/A')}")
    print(f"  prix_actuel      : {attrs.get('prix_actuel', 'N/A')}")
    print(f"  volatility       : {attrs.get('volatility', 'N/A')}")
    print(f"  rsi              : {attrs.get('rsi', 'N/A')}")
    print(f"  SMA5             : {attrs.get('SMA5', 'N/A')}")
    print(f"  SMA10            : {attrs.get('SMA10', 'N/A')}")
    print(f"  trend            : {attrs.get('trend', 'N/A')}")
    print(f"  volume_ratio     : {attrs.get('volume_ratio', 'N/A')}")
    print(f"  close_prices     : {len(attrs.get('close_prices', [])) if attrs.get('close_prices') else 0} prix")
    
    # Détails
    details = attrs.get("details", [])
    if details:
        print(f"\n  Détails ({len(details)}) :")
        for d in details[:3]:
            print(f"    - {d}")
    
    # Calcul ATR% si close_prices disponible
    close_prices = attrs.get("close_prices", [])
    if close_prices and len(close_prices) >= 15:
        # ATR% simplifié
        true_ranges = [abs(close_prices[i] - close_prices[i-1]) for i in range(1, len(close_prices))]
        atr = sum(true_ranges[-14:]) / 14 if len(true_ranges) >= 14 else None
        current_price = close_prices[-1]
        atr_pct = (atr / current_price * 100) if atr and current_price > 0 else None
        print(f"  ATR% calculé     : {atr_pct:.2f}%" if atr_pct else "  ATR% calculé     : N/A")

print("\n" + "="*80 + "\n")

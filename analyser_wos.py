#!/usr/bin/env python3
"""Vérifier pourquoi certains restent Classe C"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

symbols = ["BICC", "SGBC", "SLBC", "SNTS", "STBC"]

print("\n" + "="*100)
print(" COMPARAISON DONNEES BRVM ".center(100))
print("="*100 + "\n")

for symbol in symbols:
    doc = db.curated_observations.find_one({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "attrs.symbol": symbol
    })
    
    if doc:
        attrs = doc.get("attrs", {})
        
        prix = attrs.get("prix_actuel", 0)
        vol_abs = attrs.get("volatility", 0)
        atr_pct = (vol_abs / prix * 100) if prix > 0 and vol_abs else 0
        rsi = attrs.get("rsi")
        sma5 = attrs.get("SMA5")
        sma10 = attrs.get("SMA10")
        score = attrs.get("score", 0)
        
        print(f"{symbol:6} | Prix: {prix:7.0f} | ATR%: {atr_pct:5.1f} | RSI: {rsi if rsi else 'None':>5} | SMA5: {sma5 if sma5 else 'None':>8} | SMA10: {sma10 if sma10 else 'None':>8} | Score: {score:3}")
        
        # Calcul WOS simulé
        wos_base = 30.0
        
        # ATR bonus
        if atr_pct >= 8 and atr_pct <= 15:
            wos_base += 20
            bonus_atr = 20
        elif (atr_pct >= 5 and atr_pct < 8) or (atr_pct > 15 and atr_pct <= 22):
            wos_base += 10
            bonus_atr = 10
        else:
            bonus_atr = 0
        
        # Score bonus
        if score >= 70:
            wos_base += 15
            bonus_score = 15
        else:
            bonus_score = 0
        
        if score >= 85:
            wos_base += 10
            bonus_score2 = 10
        else:
            bonus_score2 = 0
        
        # SMA bonus
        if sma5 and sma10 and sma5 > sma10:
            bonus_sma = "(SMA5>SMA10)"
        else:
            bonus_sma = "(SMA problème)"
        
        print(f"         WOS: {wos_base:.1f} = 30 + {bonus_atr}(ATR) + {bonus_score}+{bonus_score2}(score) {bonus_sma}")
        print()
    else:
        print(f"{symbol:6} | AUCUNE DONNEE\n")

print("="*100 + "\n")

#!/usr/bin/env python3
"""Verification des decisions dans MongoDB"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))

print(f"\n[VERIF] {len(decisions)} decisions BUY dans MongoDB\n")

for d in decisions:
    symbol = d.get("symbol")
    classe = d.get("classe")
    conf = d.get("confidence")
    wos = d.get("wos")
    rr = d.get("rr")
    gain = d.get("gain_attendu")
    
    print(f"  - {symbol:6} | Classe {classe} | Conf {conf:.0f}% | WOS {wos:.1f} | RR {rr:.2f} | Gain {gain:.1f}%")

print()

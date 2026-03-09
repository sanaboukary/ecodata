#!/usr/bin/env python3
"""
TEST ATR% – Vérification des calculs de volatilité
==================================================

Objectif : Vérifier que 70% des actions ont ATR% entre 5 et 20
"""

import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from analyse_ia_simple import calculer_volatilite

_, db = get_mongo_db()

print("\n=== 🔍 TEST CALCUL ATR% ===\n")

# Récupérer les données agrégées
docs = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))

if not docs:
    print("❌ Aucune donnée AGREGATION_SEMANTIQUE_ACTION")
    print("   Exécutez d'abord : agregateur_semantique_actions.py\n")
    sys.exit(1)

print(f"📊 {len(docs)} actions à analyser\n")

results = []

for doc in docs:
    symbol = doc.get("key")
    attrs = doc.get("attrs", {})
    
    # Tenter de récupérer les prix
    close_prices = attrs.get("close_prices", [])
    
    if not close_prices or len(close_prices) < 15:
        print(f"⚠️  {symbol:10s} : Pas assez de données prix ({len(close_prices)} valeurs)")
        continue
    
    # Calcul ATR%
    atr_pct = calculer_volatilite(close_prices, 14)
    current_price = close_prices[-1]
    
    # Diagnostic
    status = "✅"
    verdict = "NORMAL"
    
    if atr_pct is None:
        status = "❌"
        verdict = "ERREUR CALCUL"
    elif atr_pct < 5:
        status = "❄️"
        verdict = "MARCHÉ MORT"
    elif atr_pct > 25:
        status = "🔥"
        verdict = "EXCESSIF"
    elif atr_pct > 18:
        status = "⚡"
        verdict = "ÉLEVÉ"
    
    results.append({
        "symbol": symbol,
        "atr_pct": atr_pct,
        "price": current_price,
        "verdict": verdict
    })
    
    print(f"{status} {symbol:10s} | Prix: {current_price:10.2f} | ATR%: {atr_pct:6.2f}% | {verdict}")

# Statistiques
print("\n" + "="*70)
print("📈 STATISTIQUES ATR%")
print("="*70 + "\n")

valides = [r for r in results if r["atr_pct"] is not None]
normales = [r for r in valides if 5 <= r["atr_pct"] <= 18]
mortes = [r for r in valides if r["atr_pct"] < 5]
excessives = [r for r in valides if r["atr_pct"] > 25]
elevees = [r for r in valides if 18 < r["atr_pct"] <= 25]

total = len(valides)
if total > 0:
    print(f"Actions analysées : {total}")
    print(f"  ✅ Normales (5-18%)    : {len(normales):3d} ({100*len(normales)/total:5.1f}%)")
    print(f"  ⚡ Élevées (18-25%)    : {len(elevees):3d} ({100*len(elevees)/total:5.1f}%)")
    print(f"  ❄️  Mortes (< 5%)       : {len(mortes):3d} ({100*len(mortes)/total:5.1f}%)")
    print(f"  🔥 Excessives (> 25%)  : {len(excessives):3d} ({100*len(excessives)/total:5.1f}%)")
    
    print(f"\n🎯 **OBJECTIF : >= 70% normales**")
    pct_normal = 100 * len(normales) / total
    if pct_normal >= 70:
        print(f"   ✅ SUCCÈS : {pct_normal:.1f}% sont dans la plage normale\n")
    else:
        print(f"   ❌ ÉCHEC : Seulement {pct_normal:.1f}% dans la plage normale")
        print(f"   👉 Bug dans les données prix ou calcul ATR%\n")
    
    # Top 5 plus volatiles
    print("\n🔥 TOP 5 PLUS VOLATILES :")
    top_vol = sorted(valides, key=lambda x: x["atr_pct"], reverse=True)[:5]
    for r in top_vol:
        print(f"   {r['symbol']:10s} : {r['atr_pct']:6.2f}%")
    
    # Top 5 moins volatiles
    print("\n❄️  TOP 5 MOINS VOLATILES :")
    bottom_vol = sorted(valides, key=lambda x: x["atr_pct"])[:5]
    for r in bottom_vol:
        print(f"   {r['symbol']:10s} : {r['atr_pct']:6.2f}%")

else:
    print("❌ Aucune donnée valide pour calculer ATR%")

print()

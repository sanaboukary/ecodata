#!/usr/bin/env python3
"""Diagnostic aberration prix BICC"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["centralisation_db"]

print("\n" + "="*80)
print("DIAGNOSTIC ABERRATION PRIX BICC")
print("="*80 + "\n")

# 1. Prix dans prices_weekly (données fraîches collectées)
print("📊 PRICES_WEEKLY (données collectées 9h-16h):")
print("─" * 80)
bicc_weekly = list(db.prices_weekly.find(
    {"symbol": "BICC"}
).sort("week", -1).limit(5))

if bicc_weekly:
    for doc in bicc_weekly:
        week = doc.get("week", "N/A")
        close = doc.get("close", 0)
        volume = doc.get("volume", 0)
        var = doc.get("variation_pct", 0)
        print(f"  {week} | Close: {close:,.0f} FCFA | Volume: {volume:,.0f} | Var: {var:+.1f}%")
else:
    print("  ❌ Aucune donnée BICC trouvée")

# 2. Dernière décision finale
print("\n📋 DECISIONS_FINALES_BRVM (recommandations V1):")
print("─" * 80)
derniere_decision = db.decisions_finales_brvm.find_one(
    sort=[("date_decision", -1)]
)

if derniere_decision:
    date_dec = derniere_decision.get("date_decision", "N/A")
    print(f"  Date décision: {date_dec}")
    
    recos = derniere_decision.get("recommandations", [])
    bicc_reco = next((r for r in recos if r.get("symbol") == "BICC"), None)
    
    if bicc_reco:
        prix_entree = bicc_reco.get("prix_entree", 0)
        prix_cible = bicc_reco.get("prix_cible", 0)
        print(f"  BICC prix_entree: {prix_entree:,.0f} FCFA")
        print(f"  BICC prix_cible: {prix_cible:,.0f} FCFA")
        
        if bicc_weekly:
            prix_actuel = bicc_weekly[0].get("close", 0)
            ecart = ((prix_actuel - prix_entree) / prix_entree * 100) if prix_entree else 0
            print(f"\n  ⚠️  ÉCART: {ecart:+.1f}% ({prix_entree:,.0f} → {prix_actuel:,.0f} FCFA)")
    else:
        print("  ℹ️  BICC pas dans cette décision")
else:
    print("  ❌ Aucune décision trouvée")

# 3. TOP5 weekly BRVM (top5_engine)
print("\n📈 TOP5_WEEKLY_BRVM (top5_engine):")
print("─" * 80)
top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))

if top5:
    for t in top5:
        symbol = t.get("symbol", "")
        prix = t.get("prix_entree", 0)
        rank = t.get("rank", 0)
        print(f"  #{rank} {symbol} | Prix: {prix:,.0f} FCFA")
else:
    print("  ℹ️  Collection vide")

print("\n" + "="*80)
print("🔍 DIAGNOSTIC:")
print("="*80)

if bicc_weekly:
    prix_actuel = bicc_weekly[0].get("close", 0)
    print(f"✅ Prix actuel BICC (prices_weekly): {prix_actuel:,.0f} FCFA")
    
    if derniere_decision and bicc_reco:
        prix_decision = bicc_reco.get("prix_entree", 0)
        if abs(prix_actuel - prix_decision) > prix_actuel * 0.1:  # >10% écart
            print(f"🚨 ABERRATION: Décision basée sur prix {prix_decision:,.0f} FCFA")
            print(f"   → Écart: {((prix_actuel - prix_decision) / prix_decision * 100):+.0f}%")
            print(f"   → Les recommandations sont OBSOLÈTES/ERRONÉES")
            print(f"\n💡 SOLUTION: Re-exécuter decision_finale_brvm.py avec données fraîches")
        else:
            print("✅ Prix cohérent entre collecte et recommandations")

print()

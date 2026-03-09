#!/usr/bin/env python3
"""Vérifier les prix BICC dans la base"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["centralisation_db"]

print("\n" + "="*100)
print("VÉRIFICATION PRIX BICC")
print("="*100 + "\n")

# Vérifier prices_weekly
print("📊 PRICES_WEEKLY (source principale):")
print("-" * 100)
bicc_weekly = list(db.prices_weekly.find(
    {"symbol": "BICC"}
).sort("week", -1).limit(10))

if bicc_weekly:
    print(f"{'Semaine':<15} {'Close':<12} {'Volume':<12} {'Variation%':<12}")
    print("-" * 100)
    for doc in bicc_weekly:
        week = doc.get("week", "N/A")
        close = doc.get("close", 0)
        volume = doc.get("volume", 0)
        var = doc.get("variation_pct", 0)
        print(f"{week:<15} {close:<12.0f} {volume:<12.0f} {var:<12.1f}")
    
    dernier_prix = bicc_weekly[0].get("close", 0)
    print(f"\n💰 Dernier prix enregistré: {dernier_prix:.0f} FCFA")
    print(f"💰 Prix réel actuel: 23500 FCFA")
    print(f"⚠️  ÉCART: {abs(dernier_prix - 23500):.0f} FCFA ({abs(dernier_prix - 23500)/23500*100:.1f}%)")
else:
    print("❌ Aucune donnée BICC dans prices_weekly\n")

# Vérifier decisions_finales_brvm
print("\n📊 DECISIONS_FINALES_BRVM (recommandations):")
print("-" * 100)
derniere_decision = db.decisions_finales_brvm.find_one(sort=[("date_decision", -1)])

if derniere_decision:
    recos = derniere_decision.get("recommandations", [])
    bicc_reco = [r for r in recos if r.get("symbol") == "BICC"]
    
    if bicc_reco:
        for r in bicc_reco:
            print(f"Date décision: {derniere_decision.get('date_decision', 'N/A')}")
            print(f"Prix entrée: {r.get('prix_entree', 0):.0f} FCFA")
            print(f"Prix cible: {r.get('prix_cible', 0):.0f} FCFA")
            print(f"Gain attendu: {r.get('gain_attendu_pct', 0):.1f}%")
            print(f"Alpha/WOS: {r.get('alpha_score', r.get('wos', 0)):.1f}")
    else:
        print("BICC non trouvé dans recommandations")
else:
    print("❌ Aucune décision trouvée\n")

# Vérifier brvm_prices (autre source potentielle)
print("\n📊 BRVM_PRICES (si existe):")
print("-" * 100)
if "brvm_prices" in db.list_collection_names():
    bicc_brvm = list(db.brvm_prices.find(
        {"symbol": "BICC"}
    ).sort("date", -1).limit(5))
    
    if bicc_brvm:
        for doc in bicc_brvm:
            print(f"Date: {doc.get('date', 'N/A')} | Close: {doc.get('close', 0):.0f} FCFA")
    else:
        print("❌ Aucune donnée BICC dans brvm_prices")
else:
    print("Collection brvm_prices n'existe pas")

print("\n" + "="*100)
print("DIAGNOSTIC:")
print("="*100)
print("Si prix 1400 FCFA alors que réel est 23500 FCFA:")
print("  ➜ ABERRATION DE DONNÉES (~1580% d'écart)")
print("  ➜ Cause probable: Erreur de collecte ou confusion symbole")
print("  ➜ Impact: Tous calculs faussés (ATR, gain, percentiles)")
print("  ➜ Action: Corriger prices_weekly puis relancer decision_finale_brvm.py")
print("="*100 + "\n")

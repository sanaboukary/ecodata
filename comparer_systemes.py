#!/usr/bin/env python3
"""Comparaison des 2 systèmes de recommandations"""
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["centralisation_db"]

print("\n" + "="*120)
print("COMPARAISON DES DEUX SYSTÈMES DE RECOMMANDATIONS".center(120))
print("="*120 + "\n")

# Système 1: TOP5 ENGINE
print("📊 SYSTÈME 1 : TOP5 ENGINE (Classement Surperformance)")
print("─" * 120)
top5_engine = list(db.top5_weekly_brvm.find().sort("rank", 1))

if top5_engine:
    symbols_top5 = [t.get('symbol') for t in top5_engine]
    print(f"   Recommandations: {', '.join(symbols_top5)}")
    print(f"   Nombre: {len(top5_engine)}")
    print(f"   Logique: Ranking RS 4 semaines + Discipline régime")
else:
    symbols_top5 = []
    print("   ❌ Aucune recommandation (exécutez: python top5_engine_brvm.py)")

# Système 2: DECISION FINALE
print("\n📋 SYSTÈME 2 : DECISION FINALE (MODE INSTITUTIONAL + ELITE)")
print("─" * 120)
decision = db.decisions_finales_brvm.find_one(sort=[("date_decision", -1)])

if decision and decision.get('recommandations'):
    recos = decision.get('recommandations', [])
    symbols_decision = [r.get('symbol') for r in recos]
    print(f"   Recommandations: {', '.join(symbols_decision)}")
    print(f"   Nombre: {len(recos)}")
    print(f"   Logique: 6 filtres ELITE → ALPHA INSTITUTIONAL")
    print(f"   Régime: {decision.get('regime', 'N/A')}")
else:
    symbols_decision = []
    print("   ❌ Aucune recommandation (exécutez: python decision_finale_brvm.py)")

# Analyse de convergence
print("\n" + "="*120)
print("ANALYSE DE CONVERGENCE")
print("="*120 + "\n")

if symbols_top5 and symbols_decision:
    # Intersection
    communs = set(symbols_top5) & set(symbols_decision)
    
    # Divergence
    uniques_top5 = set(symbols_top5) - set(symbols_decision)
    uniques_decision = set(symbols_decision) - set(symbols_top5)
    
    print(f"🔗 Actions COMMUNES aux 2 systèmes: {len(communs)}")
    if communs:
        print(f"   → {', '.join(communs)}")
    else:
        print("   → Aucune")
    
    print(f"\n🔵 Uniquement TOP5 ENGINE: {len(uniques_top5)}")
    if uniques_top5:
        print(f"   → {', '.join(uniques_top5)}")
    
    print(f"\n🟢 Uniquement DECISION FINALE: {len(uniques_decision)}")
    if uniques_decision:
        print(f"   → {', '.join(uniques_decision)}")
    
    # Taux de convergence
    total_unique = len(set(symbols_top5) | set(symbols_decision))
    convergence_rate = (len(communs) / total_unique * 100) if total_unique > 0 else 0
    
    print(f"\n📈 Taux de convergence: {convergence_rate:.1f}%")
    
    if convergence_rate >= 60:
        print("   ✅ Forte convergence - Les 2 systèmes s'accordent")
    elif convergence_rate >= 30:
        print("   ⚠️  Convergence modérée - Approches complémentaires")
    else:
        print("   🔴 Faible convergence - Logiques très différentes")
    
    print("\n" + "─" * 120)
    print("💡 INTERPRÉTATION:")
    print("─" * 120)
    print("• Si convergence forte (≥60%) → Consensus des 2 approches = haute confiance")
    print("• Si convergence modérée (30-60%) → Les 2 systèmes captent des signaux différents")
    print("• Si divergence forte (<30%) → Revoir calibration ou accepter diversité d'approches")
    
else:
    print("❌ Impossible de comparer - Au moins un système n'a pas de recommandations")
    print("\nExécutez:")
    if not symbols_top5:
        print("  python top5_engine_brvm.py")
    if not symbols_decision:
        print("  python decision_finale_brvm.py")

print("\n" + "="*120 + "\n")

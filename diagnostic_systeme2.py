#!/usr/bin/env python3
"""Diagnostic SYSTÈME 2 - Pourquoi decision_finale_brvm.py bloque"""
import sys

print("\n" + "="*80)
print("DIAGNOSTIC SYSTÈME 2 (MODE INSTITUTIONAL + ELITE)")
print("="*80 + "\n")

# Test 1: Import modules
print("[TEST 1] Vérification imports des modules institutional...")
print("-" * 80)

try:
    from brvm_institutional_regime import compute_market_regime, get_tradable_universe
    print("✅ brvm_institutional_regime.py importé")
except Exception as e:
    print(f"❌ ERREUR import brvm_institutional_regime: {e}")
    sys.exit(1)

try:
    from brvm_institutional_alpha import compute_alpha_score_institutional, compute_portfolio_allocation
    print("✅ brvm_institutional_alpha.py importé")
except Exception as e:
    print(f"❌ ERREUR import brvm_institutional_alpha: {e}")
    sys.exit(1)

# Test 2: Vérifier scipy (requis par compute_market_regime)
print("\n[TEST 2] Vérification dépendances (scipy)...")
print("-" * 80)

try:
    from scipy.stats import gmean
    print("✅ scipy installé")
except ImportError:
    print("❌ scipy NON installé - REQUIS pour compute_market_regime()")
    print("   Solution: pip install scipy")
    sys.exit(1)

# Test 3: Connexion MongoDB
print("\n[TEST 3] Connexion MongoDB...")
print("-" * 80)

try:
    from plateforme_centralisation.mongo import get_mongo_db
    _, db = get_mongo_db()
    
    # Vérifier collection
    analyses = list(db.curated_observations.find(
        {"dataset": "AGREGATION_SEMANTIQUE_ACTION"}
    ).limit(1))
    
    count = db.curated_observations.count_documents({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
    
    print(f"✅ MongoDB connecté")
    print(f"   centralisation_db.curated_observations: {count} docs AGREGATION_SEMANTIQUE_ACTION")
    
    if count == 0:
        print("   ⚠️  Collection vide - decision_finale_brvm.py va échouer")
    
except Exception as e:
    print(f"❌ ERREUR MongoDB: {e}")
    sys.exit(1)

# Test 4: Exécution compute_market_regime()
print("\n[TEST 4] Test compute_market_regime()...")
print("-" * 80)

try:
    regime_data = compute_market_regime(db)
    
    print(f"✅ compute_market_regime() exécuté avec succès")
    print(f"   Régime: {regime_data.get('regime')}")
    print(f"   Performance BRVM 4w: {regime_data.get('brvm_perf_4w', 0):.1f}%")
    print(f"   Breadth: {regime_data.get('breadth_pct', 0):.1f}%")
    print(f"   Exposition: {regime_data.get('exposure_factor', 0):.0%}")
    
except Exception as e:
    print(f"❌ ERREUR compute_market_regime(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Vérifier prices_weekly
print("\n[TEST 5] Vérification données prices_weekly...")
print("-" * 80)

try:
    count_prices = db.prices_weekly.count_documents({})
    symbols = db.prices_weekly.distinct("symbol")
    
    print(f"✅ prices_weekly: {count_prices} docs, {len(symbols)} symboles")
    
    if count_prices < 100:
        print(f"   ⚠️  Données limitées ({count_prices} docs) - résultats peuvent être incomplets")
    
except Exception as e:
    print(f"❌ ERREUR prices_weekly: {e}")

print("\n" + "="*80)
print("RÉSUMÉ DIAGNOSTIC")
print("="*80)
print("\nSi tous les tests passent ✅, decision_finale_brvm.py devrait fonctionner.")
print("Si scipy manque ❌, installez: pip install scipy")
print("Si données manquent ⚠️, exécutez collecte complète d'abord.\n")

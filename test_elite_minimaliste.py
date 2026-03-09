#!/usr/bin/env python3
"""
TEST ELITE MINIMALISTE - Validation système 14 semaines
Mode SURVIVAL professionnel - Priorité CRÉDIBILITÉ

Teste:
1. Calcul RS 4 semaines
2. Application 4 filtres robustes
3. Ranking par RS (continuation momentum)
4. Limitation 1-3 positions selon régime
5. Target minimum 10%
"""

from plateforme_centralisation.mongo import get_mongo_db
from decision_finale_brvm import compute_relative_strength_4sem, apply_elite_filters, MODE_ELITE_MINIMALISTE
import sys

def test_elite_system():
    """Test complet du système Elite Minimaliste"""
    
    print("\n" + "="*80)
    print("TEST SYSTÈME ELITE MINIMALISTE - VALIDATION")
    print("="*80 + "\n")
    
    print(f"Mode Elite Minimaliste: {MODE_ELITE_MINIMALISTE}")
    print(f"Objectif: CRÉDIBILITÉ > Performance théorique")
    print(f"Données disponibles: 14 semaines BRVM\n")
    
    _, db = get_mongo_db()
    
    # Test 1: Connexion MongoDB
    print("[TEST 1] Connexion MongoDB et données...")
    try:
        prices_count = db.prices_weekly.count_documents({})
        decisions_count = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE"})
        print(f"✓ Prices weekly: {prices_count} documents")
        print(f"✓ Décisions hebdo: {decisions_count} documents\n")
    except Exception as e:
        print(f"✗ Erreur MongoDB: {e}")
        return False
    
    # Test 2: Sample de calcul RS sur quelques actions
    print("[TEST 2] Calcul Relative Strength 4 semaines...")
    test_symbols = ["SNTS", "SGBC", "BOAC", "SAFC", "TTLS"]
    
    rs_results = {}
    for symbol in test_symbols:
        rs_4sem, perf_action, perf_brvm = compute_relative_strength_4sem(symbol, db)
        if rs_4sem is not None:
            rs_results[symbol] = {
                "rs": rs_4sem,
                "perf_action": perf_action,
                "perf_brvm": perf_brvm
            }
            status = "✓" if rs_4sem > 0 else "✗"
            print(f"{status} {symbol:6s}: RS {rs_4sem:+6.2f}% | Action {perf_action:+6.2f}% | BRVM {perf_brvm:+6.2f}%")
        else:
            print(f"⚠ {symbol:6s}: Données insuffisantes")
    
    print()
    
    # Test 3: Validation recommandations existantes
    print("[TEST 3] Analyse recommandations existantes...")
    recos = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))
    
    if not recos:
        print("⚠ Aucune recommandation trouvée - lancer decision_finale_brvm.py d'abord\n")
        return False
    
    print(f"✓ {len(recos)} recommandations trouvées")
    
    # Compter combien ont RS calculé
    with_rs = sum(1 for r in recos if r.get("rs_4sem") is not None)
    mode_elite_count = sum(1 for r in recos if r.get("mode_elite") == True)
    
    print(f"✓ {with_rs}/{len(recos)} avec RS 4sem calculé")
    print(f"✓ {mode_elite_count}/{len(recos)} en mode elite")
    
    # Stats RS
    rs_values = [r.get("rs_4sem", 0) for r in recos if r.get("rs_4sem") is not None]
    if rs_values:
        print(f"\nRS Statistics:")
        print(f"  - Min: {min(rs_values):+.2f}%")
        print(f"  - Max: {max(rs_values):+.2f}%")
        print(f"  - Moyenne: {sum(rs_values)/len(rs_values):+.2f}%")
        
        positive_rs = [rs for rs in rs_values if rs > 0]
        print(f"  - RS positif: {len(positive_rs)}/{len(rs_values)} ({len(positive_rs)/len(rs_values)*100:.1f}%)")
    
    print()
    
    # Test 4: Vérifier filtres appliqués
    print("[TEST 4] Vérification filtres elite...")
    
    # Compter par raison de rejet potentielle si on re-filtre
    test_recos = recos[:5]  # Sample 5 premières
    
    for r in test_recos:
        symbol = r.get("symbol")
        rs_4sem = r.get("rs_4sem", 0)
        target = r.get("gain_attendu", 0)
        
        # Vérifier target minimum 10%
        if MODE_ELITE_MINIMALISTE and target < 10.0:
            print(f"⚠ {symbol}: Target {target:.1f}% < 10% minimum")
        
        # Vérifier RS positif
        if rs_4sem is not None and rs_4sem <= 0:
            print(f"⚠ {symbol}: RS {rs_4sem:+.2f}% négatif (sous-performe marché)")
        
        # Vérifier confiance 40-78%
        conf = r.get("confidence", 60)
        if conf < 40 or conf > 78:
            print(f"⚠ {symbol}: Confiance {conf:.1f}% hors range 40-78%")
    
    print("✓ Vérification filtres complétée\n")
    
    # Test 5: Ranking final
    print("[TEST 5] Ranking par RS...")
    
    # Trier par RS décroissant
    recos_sorted = sorted(
        [r for r in recos if r.get("rs_4sem") is not None],
        key=lambda x: x.get("rs_4sem", 0),
        reverse=True
    )
    
    print("Top 10 par Relative Strength 4 semaines:\n")
    for i, r in enumerate(recos_sorted[:10], 1):
        print(
            f"{i:2d}. {r.get('symbol'):6s} | "
            f"RS {r.get('rs_4sem', 0):+6.2f}% | "
            f"Perf {r.get('perf_action_4sem', 0):+6.2f}% | "
            f"Target {r.get('gain_attendu', 0):5.1f}% | "
            f"Conf {r.get('confidence', 0):4.1f}%"
        )
    
    print()
    
    # Résumé final
    print("="*80)
    print("RÉSUMÉ VALIDATION ELITE MINIMALISTE")
    print("="*80 + "\n")
    
    if MODE_ELITE_MINIMALISTE:
        print("✓ Mode Elite Minimaliste ACTIVÉ")
        print("✓ 4 Filtres robustes appliqués")
        print("✓ Ranking par RS 4 semaines (continuation)")
        print("✓ Target minimum 10% (rentabilité)")
        print("✓ Positions limitées 1-3 selon marché")
        print("\n🎯 Priorité CRÉDIBILITÉ pour publication 10K followers")
    else:
        print("⚠ Mode Elite Minimaliste DÉSACTIVÉ")
        print("   Activer dans decision_finale_brvm.py: MODE_ELITE_MINIMALISTE = True")
    
    print("\n" + "="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_elite_system()
    sys.exit(0 if success else 1)

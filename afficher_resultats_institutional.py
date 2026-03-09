#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFICHER RESULTATS INSTITUTIONAL PIPELINE
Sans problèmes d'encodage Windows
"""

from plateforme_centralisation.mongo import get_mongo_db

def afficher_resultats():
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print(" RESULTATS PIPELINE INSTITUTIONNEL BRVM")
    print("="*80 + "\n")
    
    # Regime
    from brvm_institutional_regime import compute_market_regime
    regime_data = compute_market_regime(db)
    
    print(f"[REGIME] {regime_data['regime']}")
    print(f"  - BRVM 4 sem: {regime_data['brvm_perf_4w']:+.1f}%")
    print(f"  - Breadth: {regime_data['breadth_pct']:.1f}% UP")
    print(f"  - Exposition: {regime_data['exposure_factor']:.0%}\n")
    
    # Recommandations
    recos = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}).sort([("wos", -1)]))
    
    if recos:
        print(f"[RECOMMANDATIONS] {len(recos)} positions\n")
        
        for i, r in enumerate(recos, 1):
            symbol = r.get("symbol")
            alpha = r.get("alpha_score", r.get("wos", 0))
            rs_p = r.get("rs_percentile", 0)
            vol_p = r.get("volume_percentile", 0)
            size = r.get("position_size_factor", 1) * 100
            target = r.get("gain_attendu", 0)
            capital = r.get("capital_alloue")
            pct_ptf = r.get("pct_portfolio")
            
            print(f"{i}. {symbol:6s} - ALPHA: {alpha:>5.1f}/100")
            print(f"   RS: P{rs_p:.0f} | Vol: P{vol_p:.0f} | Sizing: {size:.0f}% | Target: +{target:.1f}%")
            
            if capital and pct_ptf:
                print(f"   Allocation: {capital:>10,.0f} FCFA ({pct_ptf:.1f}% portfolio)")
            
            print()
        
        # Capital total
        capital_total = sum(r.get("capital_alloue", 0) for r in recos)
        if capital_total > 0:
            print(f"CAPITAL TOTAL INVESTI: {capital_total:,.0f} FCFA")
            print(f"Facteur exposition applique: {regime_data['exposure_factor']:.0%}\n")
    else:
        print("[RECOMMANDATIONS] Aucune recommandation dans DB\n")
        print("Raisons possibles:")
        print("  - Filtres Elite trop stricts (RS P>=75, Vol P>=30)")
        print("  - Regime BEAR reduit drastiquement le nombre de candidats")
        print("  - Univers tradable limite a 20 actions top liquidite\n")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    afficher_resultats()

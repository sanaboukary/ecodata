#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST PIPELINE INSTITUTIONNEL BRVM
Test complet des 4 couches sans problèmes d'encodage Windows
"""

import sys
from plateforme_centralisation.mongo import get_mongo_db

def test_institutional_pipeline():
    """Test complet pipeline institutionnel SGI"""
    
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print(" TEST PIPELINE INSTITUTIONNEL BRVM (Mode SGI)")
    print("="*80 + "\n")
    
    # ========================================================================
    # LAYER 1: Regime Detection
    # ========================================================================
    print("[LAYER 1] Detection regime marche...")
    from brvm_institutional_regime import compute_market_regime
    
    regime_data = compute_market_regime(db)
    
    print(f"\n  REGIME: {regime_data['regime']}")
    print(f"  - Performance BRVM 4w: {regime_data['brvm_perf_4w']:+.1f}%")
    print(f"  - Volatilite moyenne: {regime_data['brvm_vol']:.1f}%")
    print(f"  - Breadth (% UP): {regime_data['breadth_pct']:.1f}%")
    print(f"  - Actions UP: {regime_data['nb_actions_up']}")
    print(f"  - Actions DOWN: {regime_data['nb_actions_down']}")
    print(f"  - Exposure factor: {regime_data['exposure_factor']:.0%}")
    
    # ========================================================================
    # LAYER 2: Tradable Universe
    # ========================================================================
    print(f"\n[LAYER 2] Filtrage univers tradable...")
    from brvm_institutional_regime import get_tradable_universe
    
    tradable_universe = get_tradable_universe(db, top_n=20)
    
    print(f"  UNIVERS: {len(tradable_universe)} actions liquides")
    print(f"  Top 10: {', '.join(tradable_universe[:10])}")
    
    # ========================================================================
    # LAYER 3: Test ALPHA_SCORE sur tout l'univers tradable
    # ========================================================================
    print(f"\n[LAYER 3] Calcul ALPHA_SCORE univers tradable...")
    from brvm_institutional_alpha import compute_alpha_score_institutional
    
    # Récupérer analyses pour actions tradables
    analyses = list(db.curated_observations.find({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "attrs.symbol": {"$in": tradable_universe}
    }))
    
    print(f"  Analyses disponibles: {len(analyses)}")
    
    alpha_scores = []
    
    for doc in analyses[:5]:  # Test sur top 5 pour debug
        attrs = doc.get("attrs", {})
        symbol = attrs.get("symbol")
        
        # Préparer action_data simplifié pour test
        action_data = {
            "symbol": symbol,
            "rs_4sem": attrs.get("relative_strength_4sem"),
            "rs_percentile": 85,  # Simulé
            "acceleration": attrs.get("acceleration_weekly", 5.0),
            "volume_percentile": 60,  # Simulé
            "prix_max_3w": attrs.get("prix_max_3sem"),
            "prix_actuel": attrs.get("prix_actuel"),
            "sentiment_score": attrs.get("score_semantique", 50),
            "atr_pct": attrs.get("volatility_pct", 15)
        }
        
        try:
            alpha, components, weights = compute_alpha_score_institutional(
                action_data=action_data,
                regime_data=regime_data
            )
            alpha_scores.append((symbol, alpha, components))
            print(f"  {symbol}: ALPHA={alpha:.1f}/100")
        except Exception as e:
            print(f"  {symbol}: ERREUR - {e}")
    
    # ========================================================================
    # LAYER 4: Portfolio Allocation
    # ========================================================================
    print(f"\n[LAYER 4] Allocation dynamique portfolio...")
    
    # Récupérer recommandations actuelles
    recommendations = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))
    
    if recommendations:
        from brvm_institutional_alpha import compute_portfolio_allocation
        
        portfolio = compute_portfolio_allocation(
            recommendations=recommendations,
            regime_data=regime_data,
            total_capital=100000
        )
        
        print(f"\n  PORTFOLIO ({regime_data['regime']} - Exposition {regime_data['exposure_factor']:.0%}):")
        print(f"  Nombre positions: {len(portfolio)}")
        
        capital_total = 0
        for alloc in portfolio:
            print(f"    {alloc['symbol']:6s}: {alloc['capital_alloue']:>10,.0f} FCFA ({alloc['pct_portfolio']:>5.1f}%)")
            capital_total += alloc['capital_alloue']
        
        print(f"\n  Capital investi: {capital_total:,.0f} FCFA ({capital_total/100000*100:.1f}% du total)")
    else:
        print("  AUCUNE recommandation disponible dans DB")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print(f" PIPELINE INSTITUTIONNEL TESTE")
    print(f"  - Regime: {regime_data['regime']} (exposition {regime_data['exposure_factor']:.0%})")
    print(f"  - Univers: {len(tradable_universe)} actions")
    print(f"  - ALPHA scores calcules: {len(alpha_scores)}")
    print(f"  - Portfolio: {len(portfolio) if recommendations else 0} positions")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_institutional_pipeline()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BRVM INSTITUTIONAL REGIME DETECTION
Expert SGI: Adaptation exposition selon régime macro
Philosophie: Ne pas trader pareil en BULL vs BEAR
"""

from plateforme_centralisation.mongo import get_mongo_db


def compute_market_regime(db):
    """
    COUCHE 1 INSTITUTIONNELLE: Détection régime de marché BRVM
    
    Calcule:
    - Performance BRVM 4 semaines
    - Volatilité BRVM (ATR composite)
    - Breadth (% actions en hausse vs baisse)
    
    Returns:
        dict {
            "regime": "BULL" | "RANGE" | "BEAR",
            "brvm_perf_4w": float,
            "brvm_vol": float,
            "breadth_pct": float (0-100),
            "nb_actions_up": int,
            "nb_actions_down": int,
            "exposure_factor": float (0.5 BEAR, 0.7 RANGE, 1.0 BULL)
        }
    """
    # 1. Récupérer toutes les analyses récentes
    analyses = list(db.curated_observations.find(
        {"dataset": "AGREGATION_SEMANTIQUE_ACTION"}
    ))
    
    if not analyses:
        return {
            "regime": "RANGE",
            "brvm_perf_4w": 0,
            "brvm_vol": 15.0,
            "breadth_pct": 50.0,
            "nb_actions_up": 0,
            "nb_actions_down": 0,
            "exposure_factor": 0.7,
            "note": "Données insuffisantes - régime RANGE par défaut"
        }
    
    # 2. Calculer performance moyenne marché (proxy BRVM Composite)
    from scipy.stats import gmean
    
    perfs_4w = []
    atrs = []
    nb_up = 0
    nb_down = 0
    nb_neutral = 0
    
    for doc in analyses:
        attrs = doc.get("attrs", {})
        symbol = attrs.get("symbol")
        
        if not symbol:
            continue
        
        # Récupérer prix 4 semaines
        prices = list(db.prices_weekly.find(
            {"symbol": symbol},
            {"close": 1}
        ).sort("week", -1).limit(5))
        
        if len(prices) >= 2:
            prices_sorted = sorted(prices, key=lambda x: x.get("week", ""))
            prix_debut = prices_sorted[0].get("close", 0)
            prix_fin = prices_sorted[-1].get("close", 0)
            
            if prix_debut > 0:
                perf_4w = ((prix_fin - prix_debut) / prix_debut) * 100
                perfs_4w.append(perf_4w)
                
                # Compter breadth
                if perf_4w > 2.0:
                    nb_up += 1
                elif perf_4w < -2.0:
                    nb_down += 1
                else:
                    nb_neutral += 1
        
        # Récupérer ATR si disponible
        atr = attrs.get("volatility")
        prix = attrs.get("prix_actuel")
        if atr and prix and prix > 0:
            atr_pct = (atr / prix) * 100
            if atr_pct < 60:  # Filtre aberrations
                atrs.append(atr_pct)
    
    # 3. Calculer métriques agrégées
    if perfs_4w:
        # Performance marché = moyenne géométrique (plus robuste)
        # Éviter valeurs négatives pour gmean
        perfs_ratio = [(1 + p/100) for p in perfs_4w]
        brvm_perf_ratio = gmean(perfs_ratio)
        brvm_perf_4w = (brvm_perf_ratio - 1) * 100
    else:
        brvm_perf_4w = 0
    
    if atrs:
        brvm_vol = sum(atrs) / len(atrs)
    else:
        brvm_vol = 15.0  # Fallback
    
    # 4. Breadth
    total_actions = nb_up + nb_down + nb_neutral
    breadth_pct = (nb_up / total_actions * 100) if total_actions > 0 else 50.0
    
    # 5. Déterminer régime
    """
    Règles institutionnelles BRVM:
    
    BULL: Performance >10% ET Breadth >60%
    BEAR: Performance <-5% OU Breadth <30%
    RANGE: Tout le reste
    """
    if brvm_perf_4w > 10 and breadth_pct > 60:
        regime = "BULL"
        exposure_factor = 1.0  # 100% capital
    elif brvm_perf_4w < -5 or breadth_pct < 30:
        regime = "BEAR"
        exposure_factor = 0.5  # 50% capital (protection)
    else:
        regime = "RANGE"
        exposure_factor = 0.7  # 70% capital (conservateur)
    
    return {
        "regime": regime,
        "brvm_perf_4w": round(brvm_perf_4w, 1),
        "brvm_vol": round(brvm_vol, 1),
        "breadth_pct": round(breadth_pct, 1),
        "nb_actions_up": nb_up,
        "nb_actions_down": nb_down,
        "nb_actions_neutral": nb_neutral,
        "exposure_factor": exposure_factor,
        "note": f"Régime {regime}: {nb_up} UP, {nb_down} DOWN, {nb_neutral} NEUTRAL"
    }


def get_tradable_universe(db, top_n=20):
    """
    COUCHE 2 INSTITUTIONNELLE: Univers investissable
    
    SGI ne trade que les actions liquides.
    Exclure bottom 50% liquidité = risque fictif
    
    Args:
        top_n: Nombre d'actions à garder (défaut 20 sur 47 BRVM)
    
    Returns:
        list[str]: Symboles actions liquides uniquement
    """
    # Récupérer volume moyen 8 semaines pour toutes actions
    all_symbols = []
    
    analyses = db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"})
    
    for doc in analyses:
        symbol = doc.get("attrs", {}).get("symbol")
        if not symbol:
            continue
        
        # Volume moyen 8 semaines
        volumes = list(db.prices_weekly.find(
            {"symbol": symbol},
            {"volume": 1}
        ).sort("week", -1).limit(8))
        
        if volumes:
            vol_list = [v.get("volume", 0) for v in volumes if v.get("volume")]
            vol_moyen = sum(vol_list) / len(vol_list) if vol_list else 0
            
            all_symbols.append({
                "symbol": symbol,
                "volume_moyen_8w": vol_moyen
            })
    
    # Trier par liquidité décroissante
    all_symbols.sort(key=lambda x: x["volume_moyen_8w"], reverse=True)
    
    # Garder top N
    tradable = [s["symbol"] for s in all_symbols[:top_n]]
    
    print(f"\n[UNIVERS INVESTISSABLE] Top {top_n} actions par liquidité:")
    for i, s in enumerate(all_symbols[:top_n], 1):
        print(f"  {i:2d}. {s['symbol']:6s} - Vol moyen: {s['volume_moyen_8w']:.0f}")
    
    print(f"\n[EXCLUS] {len(all_symbols) - top_n} actions illiquides exclues")
    
    return tradable


if __name__ == "__main__":
    _, db = get_mongo_db()
    
    print("\n" + "="*70)
    print("ANALYSE RÉGIME DE MARCHÉ BRVM (INSTITUTIONNEL)")
    print("="*70)
    
    regime_data = compute_market_regime(db)
    
    print(f"\n📊 RÉGIME DÉTECTÉ: {regime_data['regime']}")
    print(f"   - Performance BRVM 4 semaines: {regime_data['brvm_perf_4w']:+.1f}%")
    print(f"   - Volatilité moyenne marché: {regime_data['brvm_vol']:.1f}%")
    print(f"   - Breadth: {regime_data['breadth_pct']:.1f}% ({regime_data['nb_actions_up']} UP / {regime_data['nb_actions_down']} DOWN)")
    print(f"   - Facteur exposition: {regime_data['exposure_factor']*100:.0f}%")
    print(f"   - {regime_data['note']}")
    
    print("\n" + "="*70)
    
    tradable = get_tradable_universe(db, top_n=20)
    
    print("\n" + "="*70)

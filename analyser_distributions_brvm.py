#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE DISTRIBUTIONS BRVM RÉELLES
Expert 30 ans: Calibration par percentiles > Seuils fixes arbitraires

Calcule distributions sur 14 semaines disponibles:
1. RS (relative strength vs marché)
2. Volume ratio (volume / moyenne 8 sem)
3. ATR% (volatilité)
4. Performance 4 semaines

Objectif: Identifier percentiles pour filtres Elite adaptés BRVM
"""

from pymongo import MongoClient
import statistics
from datetime import datetime, timedelta
from collections import defaultdict

def compute_rs_for_action(symbol, db):
    """Calcule RS 4 semaines pour une action"""
    # Récupérer 4 dernières semaines action
    prices_action = list(db.prices_weekly.find(
        {"symbol": symbol},
        {"week": 1, "close": 1}
    ).sort("week", -1).limit(4))
    
    if len(prices_action) < 4:
        return None, None, None
    
    # Performance action 4 semaines
    p_recent = prices_action[0]["close"]
    p_4sem = prices_action[3]["close"]
    perf_action = ((p_recent - p_4sem) / p_4sem) * 100
    
    # Performance BRVM composite (moyenne géométrique approximation)
    all_actions = db.prices_weekly.distinct("symbol")
    perfs_brvm = []
    
    for sym in all_actions:
        prices_sym = list(db.prices_weekly.find(
            {"symbol": sym},
            {"close": 1}
        ).sort("week", -1).limit(4))
        
        if len(prices_sym) == 4:
            p_r = prices_sym[0]["close"]
            p_4 = prices_sym[3]["close"]
            perf_sym = ((p_r - p_4) / p_4) * 100
            perfs_brvm.append(perf_sym)
    
    if not perfs_brvm:
        return None, None, None
    
    perf_brvm = statistics.mean(perfs_brvm)
    rs = perf_action - perf_brvm
    
    return rs, perf_action, perf_brvm


def compute_volume_ratio(symbol, db):
    """Calcule ratio volume actuel / moyenne 8 semaines"""
    volumes = list(db.prices_weekly.find(
        {"symbol": symbol},
        {"volume": 1}
    ).sort("week", -1).limit(8))
    
    if len(volumes) < 2:
        return None
    
    volume_recent = volumes[0].get("volume", 0)
    volumes_hist = [v.get("volume", 0) for v in volumes[1:] if v.get("volume", 0) > 0]
    
    if not volumes_hist or volume_recent == 0:
        return None
    
    volume_moyen = statistics.mean(volumes_hist)
    if volume_moyen == 0:
        return None
    
    return volume_recent / volume_moyen


def compute_atr_pct(symbol, db):
    """Calcule ATR% depuis données weekly"""
    # Approximation: utiliser weekly range / close
    prices = list(db.prices_weekly.find(
        {"symbol": symbol},
        {"high": 1, "low": 1, "close": 1}
    ).sort("week", -1).limit(4))
    
    if len(prices) < 4:
        return None
    
    ranges = []
    for p in prices:
        if p.get("high") and p.get("low") and p.get("close"):
            tr = p["high"] - p["low"]
            ranges.append(tr)
    
    if not ranges or prices[0].get("close") is None:
        return None
    
    atr = statistics.mean(ranges)
    atr_pct = (atr / prices[0]["close"]) * 100
    
    return atr_pct


def analyser_distributions():
    """Analyse les distributions BRVM réelles"""
    client = MongoClient("mongodb://localhost:27017/")
    db = client.centralisation_db
    
    print("=" * 80)
    print("ANALYSE DISTRIBUTIONS BRVM RÉELLES (14 semaines)")
    print("Expert 30 ans: Marché concentré → Percentiles > Seuils fixes")
    print("=" * 80)
    print()
    
    # Récupérer toutes les actions
    all_symbols = db.prices_weekly.distinct("symbol")
    print(f"📊 {len(all_symbols)} actions trouvées\n")
    
    # Collections des métriques
    rs_values = []
    volume_ratios = []
    atr_values = []
    perf_4sem = []
    
    data_by_symbol = {}
    
    print("🔄 Calcul des métriques...")
    for symbol in all_symbols:
        # RS
        rs, perf_act, perf_mkt = compute_rs_for_action(symbol, db)
        
        # Volume ratio
        vol_ratio = compute_volume_ratio(symbol, db)
        
        # ATR%
        atr_pct = compute_atr_pct(symbol, db)
        
        # Stocker
        data_by_symbol[symbol] = {
            "rs": rs,
            "perf_action": perf_act,
            "perf_marche": perf_mkt,
            "volume_ratio": vol_ratio,
            "atr_pct": atr_pct
        }
        
        # Ajouter aux listes si disponible
        if rs is not None:
            rs_values.append(rs)
        if perf_act is not None:
            perf_4sem.append(perf_act)
        if vol_ratio is not None:
            volume_ratios.append(vol_ratio)
        if atr_pct is not None:
            atr_values.append(atr_pct)
    
    print(f"✅ Métriques calculées\n")
    
    # Afficher distributions
    print("=" * 80)
    print("DISTRIBUTIONS PERCENTILES")
    print("=" * 80)
    print()
    
    # 1. Relative Strength
    if rs_values:
        rs_sorted = sorted(rs_values)
        n = len(rs_sorted)
        print("📈 RELATIVE STRENGTH (RS 4 sem vs marché)")
        print(f"   Échantillon: {n} actions")
        print(f"   Min: {min(rs_values):.1f}%")
        print(f"   P10: {rs_sorted[int(n*0.1)]:.1f}%")
        print(f"   P25: {rs_sorted[int(n*0.25)]:.1f}%")
        print(f"   P50 (médiane): {rs_sorted[int(n*0.5)]:.1f}%")
        print(f"   P70: {rs_sorted[int(n*0.7)]:.1f}%  ← SEUIL ELITE 30%")
        print(f"   P75: {rs_sorted[int(n*0.75)]:.1f}%")
        print(f"   P90: {rs_sorted[int(n*0.9)]:.1f}%")
        print(f"   Max: {max(rs_values):.1f}%")
        print()
        
        # Compter combien ont RS > 0
        rs_positifs = [r for r in rs_values if r > 0]
        print(f"   ⚠️  RS > 0: {len(rs_positifs)}/{n} actions ({100*len(rs_positifs)/n:.0f}%)")
        print(f"   💡 Expert: Si < 20% ont RS+, marché TRÈS concentré")
        print()
    
    # 2. Volume Ratio
    if volume_ratios:
        vol_sorted = sorted(volume_ratios)
        n = len(vol_sorted)
        print("📊 VOLUME RATIO (volume / moyenne 8 sem)")
        print(f"   Échantillon: {n} actions")
        print(f"   Min: {min(volume_ratios):.2f}x")
        print(f"   P10: {vol_sorted[int(n*0.1)]:.2f}x")
        print(f"   P25: {vol_sorted[int(n*0.25)]:.2f}x")
        print(f"   P50 (médiane): {vol_sorted[int(n*0.5)]:.2f}x")
        print(f"   P75: {vol_sorted[int(n*0.75)]:.2f}x")
        print(f"   P90: {vol_sorted[int(n*0.9)]:.2f}x")
        print(f"   Max: {max(volume_ratios):.2f}x")
        print()
        
        # Comparer seuils
        above_15x = [v for v in volume_ratios if v >= 1.5]
        above_06x = [v for v in volume_ratios if v >= 0.6]
        print(f"   ⚠️  Volume ≥ 1.5x (Nasdaq): {len(above_15x)}/{n} actions ({100*len(above_15x)/n:.0f}%)")
        print(f"   ✅ Volume ≥ 0.6x (BRVM adapt): {len(above_06x)}/{n} actions ({100*len(above_06x)/n:.0f}%)")
        print()
    
    # 3. ATR %
    if atr_values:
        atr_sorted = sorted(atr_values)
        n = len(atr_sorted)
        print("📉 ATR % (volatilité hebdomadaire)")
        print(f"   Échantillon: {n} actions")
        print(f"   Min: {min(atr_values):.1f}%")
        print(f"   P10: {atr_sorted[int(n*0.1)]:.1f}%")
        print(f"   P25: {atr_sorted[int(n*0.25)]:.1f}%")
        print(f"   P50 (médiane): {atr_sorted[int(n*0.5)]:.1f}%")
        print(f"   P75: {atr_sorted[int(n*0.75)]:.1f}%")
        print(f"   P90: {atr_sorted[int(n*0.9)]:.1f}%")
        print(f"   Max: {max(atr_values):.1f}%")
        print()
        
        # Comparer plages
        in_range_8_25 = [a for a in atr_values if 8 <= a <= 25]
        in_range_8_30 = [a for a in atr_values if 8 <= a <= 30]
        print(f"   ⚠️  ATR 8-25% (strict): {len(in_range_8_25)}/{n} actions ({100*len(in_range_8_25)/n:.0f}%)")
        print(f"   ✅ ATR 8-30% (BRVM): {len(in_range_8_30)}/{n} actions ({100*len(in_range_8_30)/n:.0f}%)")
        print()
    
    # 4. Performance 4 semaines
    if perf_4sem:
        perf_sorted = sorted(perf_4sem)
        n = len(perf_sorted)
        print("💰 PERFORMANCE 4 SEMAINES (actions individuelles)")
        print(f"   Échantillon: {n} actions")
        print(f"   Min: {min(perf_4sem):.1f}%")
        print(f"   P25: {perf_sorted[int(n*0.25)]:.1f}%")
        print(f"   P50 (médiane): {perf_sorted[int(n*0.5)]:.1f}%")
        print(f"   P75: {perf_sorted[int(n*0.75)]:.1f}%")
        print(f"   Max: {max(perf_4sem):.1f}%")
        print()
        
        # Performance moyenne = proxy BRVM composite
        perf_moyenne = statistics.mean(perf_4sem)
        print(f"   📊 Performance moyenne (proxy indice): {perf_moyenne:.1f}%")
        print()
    
    # Top/Bottom actions
    print("=" * 80)
    print("TOP 10 RELATIVE STRENGTH (Elite candidates)")
    print("=" * 80)
    print()
    
    # Trier par RS
    symbols_with_rs = [(sym, data["rs"], data["perf_action"], data["volume_ratio"], data["atr_pct"]) 
                       for sym, data in data_by_symbol.items() 
                       if data["rs"] is not None]
    
    symbols_with_rs.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'SYMBOL':<8} {'RS%':>8} {'Perf%':>8} {'VolRatio':>9} {'ATR%':>7} {'Commentaire':<30}")
    print("-" * 80)
    
    for i, (sym, rs, perf, vol_r, atr) in enumerate(symbols_with_rs[:10], 1):
        vol_str = f"{vol_r:.2f}x" if vol_r is not None else "N/A"
        atr_str = f"{atr:.1f}%" if atr is not None else "N/A"
        
        # Détecter statut filtres
        comment = []
        if rs > 0:
            comment.append("RS+")
        else:
            comment.append(f"RS-")
        
        if vol_r and vol_r >= 0.6:
            comment.append("Vol✓")
        elif vol_r:
            comment.append("Vol✗")
        
        if atr and 8 <= atr <= 30:
            comment.append("ATR✓")
        elif atr:
            comment.append("ATR✗")
        
        comment_str = " ".join(comment)
        
        print(f"{sym:<8} {rs:>7.1f}% {perf:>7.1f}% {vol_str:>9} {atr_str:>7} {comment_str}")
    
    print()
    
    # Bottom 10
    print("=" * 80)
    print("BOTTOM 10 RELATIVE STRENGTH (Faibles)")
    print("=" * 80)
    print()
    
    print(f"{'SYMBOL':<8} {'RS%':>8} {'Perf%':>8} {'VolRatio':>9} {'ATR%':>7}")
    print("-" * 80)
    
    for sym, rs, perf, vol_r, atr in symbols_with_rs[-10:]:
        vol_str = f"{vol_r:.2f}x" if vol_r is not None else "N/A"
        atr_str = f"{atr:.1f}%" if atr is not None else "N/A"
        print(f"{sym:<8} {rs:>7.1f}% {perf:>7.1f}% {vol_str:>9} {atr_str:>7}")
    
    print()
    
    # Recommandations calibration
    print("=" * 80)
    print("🎯 RECOMMANDATIONS CALIBRATION ELITE")
    print("=" * 80)
    print()
    
    if rs_values:
        rs_sorted = sorted(rs_values)
        n = len(rs_sorted)
        p70 = rs_sorted[int(n*0.7)]
        
        print("📌 FILTRE RS (Relative Strength)")
        print(f"   Actuel: RS > 0 (bloque {100*(1-len(rs_positifs)/n):.0f}% actions)")
        print(f"   Recommandé: RS percentile > 70 (RS > {p70:.1f}% dans univers actuel)")
        print(f"   → Top 30% actions, même si toutes RS négatives")
        print()
    
    if volume_ratios:
        vol_sorted = sorted(volume_ratios)
        n = len(vol_sorted)
        p40 = vol_sorted[int(n*0.4)]
        
        print("📌 FILTRE VOLUME")
        print(f"   Actuel: ≥ 1.5x (bloque {100*len([v for v in volume_ratios if v < 1.5])/n:.0f}% actions)")
        print(f"   Recommandé: ≥ 0.6x (garde {100*len(above_06x)/n:.0f}% actions)")
        print(f"   Alternative: Percentile > 40 (≥ {p40:.2f}x dans univers actuel)")
        print()
    
    if atr_values:
        atr_sorted = sorted(atr_values)
        n = len(atr_sorted)
        p20 = atr_sorted[int(n*0.2)]
        p80 = atr_sorted[int(n*0.8)]
        
        print("📌 FILTRE ATR")
        print(f"   Actuel: 8-25% (garde {100*len(in_range_8_25)/n:.0f}% actions)")
        print(f"   Recommandé: 8-30% (garde {100*len(in_range_8_30)/n:.0f}% actions)")
        print(f"   Alternative: P20-P80 ({p20:.1f}%-{p80:.1f}% dans univers actuel)")
        print()
    
    print("=" * 80)
    print("💡 CONCLUSION EXPERT")
    print("=" * 80)
    print()
    print("✅ Passer en logique PERCENTILE au lieu de seuils fixes")
    print("✅ Top 5 Hebdo ≠ Battre l'indice (tolérer RS- si top 30%)")
    print("✅ BRVM marché concentré: Filtres adaptés réalité locale")
    print("✅ Éviter 'moteur parfait qui ne trade jamais'")
    print()


if __name__ == "__main__":
    analyser_distributions()

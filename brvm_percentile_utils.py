#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BRVM PERCENTILE UTILITIES
Calibration empirique marché BRVM (étroit, concentré, irrégulier)
Expert 30 ans: Percentiles > Seuils absolus
"""

def compute_percentiles(values):
    """
    Calcule le percentile de chaque valeur dans l'univers
    
    Args:
        values: dict {symbol: value} ou list de valeurs
    
    Returns:
        dict {symbol: percentile} ou dict {value: percentile}
        percentile = 0.0 (pire) à 1.0 (meilleur)
    """
    if isinstance(values, dict):
        symbols = list(values.keys())
        value_list = [values[s] for s in symbols]
    else:
        value_list = list(values)
        symbols = list(range(len(value_list)))
    
    # Gérer valeurs None
    valid_pairs = [(s, v) for s, v in zip(symbols, value_list) if v is not None]
    
    if not valid_pairs:
        return {}
    
    # Trier par valeur
    sorted_pairs = sorted(valid_pairs, key=lambda x: x[1])
    
    n = len(sorted_pairs)
    percentile_map = {}
    
    for rank, (symbol, value) in enumerate(sorted_pairs):
        # Percentile = rang / (n-1) pour avoir 0.0 et 1.0 aux extrêmes
        percentile = rank / (n - 1) if n > 1 else 0.5
        percentile_map[symbol] = percentile
    
    return percentile_map


def normalize_to_0_1(value, min_val, max_val):
    """
    Normalise une valeur entre 0 et 1
    
    Args:
        value: Valeur à normaliser
        min_val: Min de la distribution
        max_val: Max de la distribution
    
    Returns:
        float entre 0.0 et 1.0
    """
    if max_val == min_val:
        return 0.5
    
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def compute_distribution_stats(values):
    """
    Calcule statistiques de distribution
    
    Returns:
        dict avec min, p10, p25, p50, p75, p90, max
    """
    valid_values = [v for v in values if v is not None]
    
    if not valid_values:
        return None
    
    sorted_vals = sorted(valid_values)
    n = len(sorted_vals)
    
    def percentile(p):
        """Percentile p entre 0 et 1"""
        idx = int(p * (n - 1))
        return sorted_vals[idx]
    
    return {
        "min": sorted_vals[0],
        "p10": percentile(0.10),
        "p25": percentile(0.25),
        "p50": percentile(0.50),  # Médiane
        "p75": percentile(0.75),
        "p90": percentile(0.90),
        "max": sorted_vals[-1],
        "count": n
    }


def get_threshold_from_percentile(percentile_target, distribution):
    """
    Convertit un percentile cible en seuil de valeur
    
    Args:
        percentile_target: 0.75 pour top 25%, 0.60 pour top 40%, etc.
        distribution: dict avec p10, p25, p50, p75, p90
    
    Returns:
        Seuil de valeur correspondant au percentile
    """
    if percentile_target >= 0.90:
        return distribution["p90"]
    elif percentile_target >= 0.75:
        return distribution["p75"]
    elif percentile_target >= 0.50:
        return distribution["p50"]
    elif percentile_target >= 0.25:
        return distribution["p25"]
    elif percentile_target >= 0.10:
        return distribution["p10"]
    else:
        return distribution["min"]


# SEUILS EMPIRIQUES BRVM (14 semaines février 2026)
# Source: analyser_distributions_brvm.py

BRVM_EMPIRICAL_THRESHOLDS = {
    "rs_4sem": {
        "p10": -194.9,
        "p25": -172.5,
        "p50": -129.3,  # Médiane
        "p70": -43.3,   # Seuil Elite actuel
        "p75": 14.2,
        "p90": 183.3,
        "max": 3204.0,
        "note": "26% actions ont RS+, marché TRÈS concentré"
    },
    "atr_pct": {
        "p10": 3.3,
        "p25": 9.4,
        "p50": 31.6,  # Médiane
        "p75": 55.4,
        "p90": 121.3,
        "max": 452.9,
        "note": "8-30% garde 26% actions (vs 23% pour 8-25%)"
    },
    "volume_ratio": {
        "note": "À calculer dynamiquement chaque semaine (pas de distribution fixe)"
    },
    "acceleration": {
        "note": "À calculer depuis détails analyse (pas stocké direct)"
    }
}


def is_top_percentile(value, percentile_map, threshold_percentile=0.75):
    """
    Vérifie si une valeur est dans le top percentile
    
    Args:
        value: Valeur à tester
        percentile_map: dict retourné par compute_percentiles()
        threshold_percentile: 0.75 pour top 25%, 0.60 pour top 40%
    
    Returns:
        bool
    """
    symbol_percentile = percentile_map.get(value)
    
    if symbol_percentile is None:
        return False
    
    return symbol_percentile >= threshold_percentile

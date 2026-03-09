#!/usr/bin/env python3
"""
MOTEUR DE CORRÉLATION BRVM – VERSION EXPERTE
===========================================

Utilisation professionnelle de la corrélation :
- Gestion du risque
- Éviter la fausse diversification
- Confirmation conditionnelle
- Détection de décorrélation (alpha)

⚠️ La corrélation NE GÉNÈRE PAS de BUY.
Elle filtre, pénalise et alerte.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Set

# =====================================================
# 1. CONSTRUCTION DES CLUSTERS CORRÉLÉS
# =====================================================
def construire_clusters_correlation(
    corr_matrix: pd.DataFrame,
    seuil: float = 0.7
) -> List[Set[str]]:
    """
    Regroupe les actions fortement corrélées entre elles
    """
    clusters = []
    visited = set()

    for s in corr_matrix.columns:
        if s in visited:
            continue

        cluster = {s}
        for t in corr_matrix.columns:
            if s != t and corr_matrix.loc[s, t] >= seuil:
                cluster.add(t)

        clusters.append(cluster)
        visited |= cluster

    return clusters

# =====================================================
# 2. PÉNALISATION DE SUR-CORRÉLATION
# =====================================================
def penalite_correlation(
    symbol: str,
    portefeuille: List[str],
    corr_matrix: pd.DataFrame,
    seuil: float = 0.75
) -> int:
    """
    Applique une pénalité si le titre est trop corrélé
    à des positions déjà détenues
    """
    penalty = 0

    for s in portefeuille:
        if s in corr_matrix.columns and symbol in corr_matrix.columns:
            corr = corr_matrix.loc[symbol, s]
            if corr >= seuil:
                penalty += 15  # pénalité experte

    return penalty

# =====================================================
# 3. CONFIRMATION CONDITIONNELLE (FINE)
# =====================================================
def bonus_confirmation(
    symbol: str,
    watchlist_buy: List[str],
    corr_matrix: pd.DataFrame,
    seuil: float = 0.7
) -> int:
    """
    Petit bonus si corrélé à un BUY fort existant
    MAIS seulement si le score technique est déjà bon
    """
    bonus = 0

    for s in watchlist_buy:
        if s in corr_matrix.columns and symbol in corr_matrix.columns:
            if corr_matrix.loc[symbol, s] >= seuil:
                bonus += 5  # bonus léger, jamais décisif

    return bonus

# =====================================================
# 4. DÉTECTION DE DÉCOUPLAGE (ALERTE ANALYSTE)
# =====================================================
def detecter_decouplage(
    symbol_a: str,
    symbol_b: str,
    corr_matrix: pd.DataFrame,
    perf_a: float,
    perf_b: float,
    seuil_corr: float = 0.7,
    seuil_diff: float = 10.0
) -> Dict:
    """
    Détecte une divergence anormale entre deux titres corrélés
    """
    if (
        symbol_a in corr_matrix.columns
        and symbol_b in corr_matrix.columns
        and corr_matrix.loc[symbol_a, symbol_b] >= seuil_corr
    ):
        diff = abs(perf_a - perf_b)

        if diff >= seuil_diff:
            return {
                "flag": "DECOUPLAGE",
                "corr": round(corr_matrix.loc[symbol_a, symbol_b], 2),
                "performance_diff": round(diff, 2)
            }

    return {}

# =====================================================
# 5. INTÉGRATION DANS LE SCORE GLOBAL
# =====================================================
def ajuster_score_avec_correlation(
    symbol: str,
    score_initial: float,
    portefeuille: List[str],
    watchlist_buy: List[str],
    corr_matrix: pd.DataFrame
) -> float:
    """
    Ajuste le score final avec la corrélation
    """
    score = score_initial

    score -= penalite_correlation(symbol, portefeuille, corr_matrix)
    score += bonus_confirmation(symbol, watchlist_buy, corr_matrix)

    return max(0, min(100, round(score, 1)))

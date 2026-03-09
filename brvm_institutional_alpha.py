#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BRVM INSTITUTIONAL ALPHA SCORING & PORTFOLIO ALLOCATION
Expert SGI: Alpha mesurable + Contrôle risque + Allocation dynamique

ALPHA_SCORE = 
    0.35 × RS_percentile
    0.20 × Acceleration  
    0.15 × Volume_percentile
    0.15 × Breakout_strength
    0.05-0.20 × Sentiment_normalisé (DYNAMIQUE)
    0.05 × Volatility_efficiency

🔥 PONDÉRATION DYNAMIQUE SENTIMENT (trading hebdomadaire BRVM):
- Semaine normale (< 3 pubs): 5% (bruit)
- Semaine standard (3-8 pubs): 10% (accélérateur)
- Semaine événementielle (>8 pubs OU résultats/dividende): 20% (moteur)

Volatility Efficiency = perf_4w / atr_4w
→ Institutionnel préfère volatilité efficace vs juste volatilité
"""


def compute_dynamic_sentiment_weight(nb_publications, publication_keywords=None):
    """
    PONDÉRATION DYNAMIQUE DU SENTIMENT (Expert Trading Hebdomadaire)
    
    Sur BRVM, les publications sont RARES et ÉVÉNEMENTIELLES.
    Quand il y a un vrai événement (résultats, dividende, acquisition),
    le marché réagit pendant 1-3 semaines.
    
    Args:
        nb_publications (int): Nombre de publications dans la semaine
        publication_keywords (list): Mots-clés détectés dans les publications
            ["RESULTATS", "DIVIDENDE", "ACQUISITION", "ASSEMBLEE", "CONSEIL"]
    
    Returns:
        float: Poids sentiment entre 0.05 et 0.20
    """
    # DÉTECTION D'ÉVÉNEMENTS MAJEURS (prioritaire)
    evenements_majeurs = ["RESULTATS", "DIVIDENDE", "ACQUISITION", "FUSION", "CONSEIL"]
    
    if publication_keywords:
        for keyword in publication_keywords:
            if any(evt in keyword.upper() for evt in evenements_majeurs):
                return 0.20  # ÉVÉNEMENTIEL: sentiment devient moteur
    
    # SINON: pondération par volume de publications
    if nb_publications < 3:
        # Semaine calme: sentiment = bruit
        return 0.05
    elif nb_publications <= 8:
        # Semaine normale: sentiment = accélérateur
        return 0.10
    else:
        # > 8 publications: activité inhabituelle
        return 0.20
    

def normalize_weights(weights, sentiment_weight):
    """
    Ajuste les pondérations pour maintenir total = 1.0
    quand sentiment varie de 5% à 20%.
    
    RÈGLE TRADING HEBDOMADAIRE:
    - RS (force relative) reste dominant (30-40%)
    - Volume reste critique (20-30%)
    - On réduit proportionnellement les autres facteurs
    """
    # Calculer l'écart vs poids sentiment standard (10%)
    delta_sent = sentiment_weight - 0.10
    
    # Redistribuer l'écart sur les facteurs secondaires (breakout, voleff, accel)
    # JAMAIS toucher RS et Volume (moteurs principaux)
    
    if delta_sent > 0:
        # Sentiment augmente (15% ou 20%) → réduire breakout, voleff
        weights["breakout"] = max(0.03, weights["breakout"] - delta_sent * 0.5)
        weights["voleff"] = max(0.03, weights["voleff"] - delta_sent * 0.3)
        weights["accel"] = max(0.08, weights["accel"] - delta_sent * 0.2)
    elif delta_sent < 0:
        # Sentiment baisse (5%) → augmenter breakout, voleff
        weights["breakout"] = min(0.20, weights["breakout"] - delta_sent * 0.5)
        weights["voleff"] = min(0.10, weights["voleff"] - delta_sent * 0.3)
        weights["accel"] = min(0.25, weights["accel"] - delta_sent * 0.2)
    
    weights["sent"] = sentiment_weight
    
    # Vérifier total = 1.0 (avec tolérance ±0.01)
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        # Re-normaliser
        for k in weights:
            weights[k] = weights[k] / total
    
    return weights


def compute_alpha_score_institutional(action_data, regime_data):
    """
    COUCHE 3 INSTITUTIONNELLE: Score Alpha composite avec SENTIMENT DYNAMIQUE
    
    🔥 NOUVEAU: Pondération sentiment 5-20% selon activité publications
    
    Pénalise volatilité inefficace.
    Adapte pondérations selon régime ET volume publications.
    
    Args:
        action_data: dict avec rs_percentile, acceleration, volume_percentile, 
                     score_sem, nb_publications, publication_keywords, etc.
        regime_data: dict avec regime, brvm_vol, etc.
    
    Returns:
        tuple: (alpha_score, components, weights_used)
    """
    # Normaliser tous les facteurs 0-1
    
    # 1. RS Percentile (0-100 → 0-1)
    rs_norm = (action_data.get("rs_percentile", 0) / 100.0) if action_data.get("rs_percentile") is not None else 0
    
    # 2. Acceleration (normaliser -10% à +10% → 0-1)
    accel = action_data.get("acceleration", 0)
    if accel is not None:
        accel_norm = max(0, min(1, (accel + 10) / 20))  # -10% = 0, +10% = 1
    else:
        accel_norm = 0.5  # Neutre si absent
    
    # 3. Volume Percentile (0-100 → 0-1)
    vol_norm = (action_data.get("volume_percentile", 0) / 100.0) if action_data.get("volume_percentile") is not None else 0
    
    # 4. Breakout Strength (0 si pas breakout, 1 si breakout confirmé)
    prix = action_data.get("prix", 0)
    prix_max_3w = action_data.get("prix_max_3w", 0)
    
    if prix and prix_max_3w and prix > 0:
        breakout_margin = ((prix - prix_max_3w) / prix_max_3w) * 100
        if breakout_margin >= 0:
            # Breakout confirmé: 0% = 0.5, +5% = 1.0
            breakout_norm = min(1.0, 0.5 + (breakout_margin / 10))
        else:
            # Pas de breakout: -2% tolérance = 0.3, au-delà = 0
            if breakout_margin >= -2:
                breakout_norm = 0.3
            else:
                breakout_norm = 0
    else:
        breakout_norm = 0.5  # Neutre si données manquantes
    
    # 5. Sentiment Normalisé (score_sem -100 à +100 → 0-1)
    score_sem = action_data.get("score_sem", 0)
    sent_norm = max(0, min(1, (score_sem + 100) / 200))
    
    # 6. VOLATILITY EFFICIENCY (nouveau - clé institutionnelle)
    perf_4w = action_data.get("perf_action_4sem", 0)
    atr_pct = action_data.get("atr_pct", 15)
    
    if atr_pct and atr_pct > 0:
        vol_eff_raw = perf_4w / atr_pct  # Ratio rendement/volatilité
        # Normaliser: -1 = 0, 0 = 0.5, +2 = 1.0
        vol_eff_norm = max(0, min(1, (vol_eff_raw + 1) / 3))
    else:
        vol_eff_norm = 0.5
    
    # 🔥 CALCUL POIDS SENTIMENT DYNAMIQUE
    nb_publications = action_data.get("nb_publications", 0) or 0
    publication_keywords = action_data.get("publication_keywords", [])
    
    sentiment_weight = compute_dynamic_sentiment_weight(nb_publications, publication_keywords)
    
    # ADAPTATION PONDÉRATIONS SELON RÉGIME (base)
    regime = regime_data.get("regime", "RANGE")
    
    if regime == "BULL":
        # BULL: Favoriser momentum (accel, breakout)
        weights = {
            "rs": 0.30,
            "accel": 0.25,      # ↑ momentum
            "vol": 0.10,        # ↓ liquidité moins critique
            "breakout": 0.20,   # ↑ breakouts plus fiables
            "sent": 0.10,       # Sera ajusté après
            "voleff": 0.05
        }
    elif regime == "BEAR":
        # BEAR: Favoriser qualité (RS, liquidité, vol efficiency)
        weights = {
            "rs": 0.40,         # ↑ force relative critique
            "accel": 0.10,      # ↓ momentum moins fiable
            "vol": 0.25,        # ↑ liquidité essentielle  
            "breakout": 0.05,   # ↓ faux breakouts
            "sent": 0.10,       # Sera ajusté après
            "voleff": 0.10      # ↑ efficacité volatilité
        }
    else:  # RANGE
        # RANGE: Pondérations équilibrées (défaut institutionnel)
        weights = {
            "rs": 0.35,
            "accel": 0.20,
            "vol": 0.15,
            "breakout": 0.15,
            "sent": 0.10,       # Sera ajusté après
            "voleff": 0.05
        }
    
    # 🔥 AJUSTER PONDÉRATIONS AVEC SENTIMENT DYNAMIQUE
    weights = normalize_weights(weights, sentiment_weight)
    
    # Calcul score final
    alpha_score = (
        weights["rs"] * rs_norm +
        weights["accel"] * accel_norm +
        weights["vol"] * vol_norm +
        weights["breakout"] * breakout_norm +
        weights["sent"] * sent_norm +
        weights["voleff"] * vol_eff_norm
    ) * 100  # Ramener à 0-100
    
    # Logging détaillé (optionnel)
    components = {
        "rs": rs_norm * weights["rs"] * 100,
        "accel": accel_norm * weights["accel"] * 100,
        "vol": vol_norm * weights["vol"] * 100,
        "breakout": breakout_norm * weights["breakout"] * 100,
        "sent": sent_norm * weights["sent"] * 100,
        "voleff": vol_eff_norm * weights["voleff"] * 100
    }
    
    return round(alpha_score, 1), components, weights


def compute_portfolio_allocation(recommendations, regime_data, total_capital=100000):
    """
    COUCHE 4 INSTITUTIONNELLE: Allocation dynamique de capital
    
    Règles SGI:
    - Allocation par alpha_score (pas poids égal)
    - Max 30% par secteur
    - Max 25% par action
    - Ajuster selon régime (50% si BEAR, 70% si RANGE, 100% si BULL)
    
    Args:
        recommendations: list[dict] avec symbol, alpha_score, secteur, position_size_factor
        regime_data: dict avec regime, exposure_factor
        total_capital: capital total disponible
    
    Returns:
        list[dict]: Positions avec capital_alloue, pct_portfolio
    """
    if not recommendations:
        return []
    
    # 1. Facteur exposition global selon régime
    exposure_factor = regime_data.get("exposure_factor", 0.7)
    capital_disponible = total_capital * exposure_factor
    
    print(f"\n[ALLOCATION] Régime {regime_data.get('regime', 'N/A')} -> Exposition {exposure_factor*100:.0f}%")
    print(f"[ALLOCATION] Capital disponible: {capital_disponible:,.0f} FCFA")
    
    # 2. Somme alpha_scores pour allocation proportionnelle
    total_alpha = sum(r.get("alpha_score", 0) for r in recommendations)
    
    if total_alpha == 0:
        # Fallback: poids égal
        weight_base = 1.0 / len(recommendations)
        for r in recommendations:
            r["weight_raw"] = weight_base
    else:
        # Poids proportionnel à alpha_score
        for r in recommendations:
            r["weight_raw"] = r.get("alpha_score", 0) / total_alpha
    
    # 3. Appliquer contraintes institutionnelles
    
    # 3a. Position size factor (volume faible = réduction)
    for r in recommendations:
        size_factor = r.get("position_size_factor", 1.0)
        r["weight_adjusted"] = r["weight_raw"] * size_factor
    
    # Renormaliser après ajustement
    total_adjusted = sum(r["weight_adjusted"] for r in recommendations)
    if total_adjusted > 0:
        for r in recommendations:
            r["weight_normalized"] = r["weight_adjusted"] / total_adjusted
    else:
        # Fallback
        for r in recommendations:
            r["weight_normalized"] = 1.0 / len(recommendations)
    
    # 3b. Contrainte max 25% par action
    for r in recommendations:
        r["weight_final"] = min(r["weight_normalized"], 0.25)
    
    # 3c. Contrainte max 30% par secteur
    secteurs = {}
    for r in recommendations:
        secteur = r.get("secteur", "UNKNOWN")
        if secteur not in secteurs:
            secteurs[secteur] = []
        secteurs[secteur].append(r)
    
    # Vérifier et ajuster si secteur > 30%
    for secteur, actions in secteurs.items():
        total_secteur = sum(a["weight_final"] for a in actions)
        if total_secteur > 0.30:
            # Réduire proportionnellement
            factor = 0.30 / total_secteur
            for a in actions:
                a["weight_final"] *= factor
                a["secteur_limited"] = True
        else:
            for a in actions:
                a["secteur_limited"] = False
    
    # Renormaliser une dernière fois
    total_final = sum(r["weight_final"] for r in recommendations)
    if total_final > 0:
        for r in recommendations:
            r["pct_portfolio"] = (r["weight_final"] / total_final) * 100
            r["capital_alloue"] = (r["weight_final"] / total_final) * capital_disponible
    else:
        for r in recommendations:
            r["pct_portfolio"] = 0
            r["capital_alloue"] = 0
    
    # 4. Tri par allocation décroissante
    recommendations.sort(key=lambda x: x.get("capital_alloue", 0), reverse=True)
    
    # 5. Logging
    print(f"\n[ALLOCATION] Distribution finale (top {len(recommendations)}):")
    for i, r in enumerate(recommendations, 1):
        symbol = r.get("symbol", "N/A")
        pct = r.get("pct_portfolio", 0)
        capital = r.get("capital_alloue", 0)
        alpha = r.get("alpha_score", 0)
        secteur = r.get("secteur", "N/A")
        limited = "⚠️" if r.get("secteur_limited", False) else "  "
        
        print(f"  {i}. {symbol:6s} {limited} {pct:5.1f}% ({capital:>10,.0f} FCFA) | Alpha: {alpha:4.1f} | {secteur}")
    
    return recommendations


if __name__ == "__main__":
    # Test unitaire
    print("\n" + "="*70)
    print("TEST ALPHA SCORE INSTITUTIONNEL")
    print("="*70)
    
    # Données test
    action_test = {
        "symbol": "SGBC",
        "rs_percentile": 93,
        "acceleration": 5.2,
        "volume_percentile": 72,
        "prix": 31000,
        "prix_max_3w": 29500,
        "score_sem": 15,
        "perf_action_4sem": 50.0,
        "atr_pct": 25.0,
        "secteur": "FINANCE"
    }
    
    regime_test = {"regime": "BULL", "brvm_vol": 15.0, "exposure_factor": 1.0}
    
    alpha, components, weights = compute_alpha_score_institutional(action_test, regime_test)
    
    print(f"\nAction: {action_test['symbol']}")
    print(f"ALPHA_SCORE: {alpha:.1f}/100")
    print(f"\nComposants (régime {regime_test['regime']}):")
    for key, val in components.items():
        print(f"  - {key:10s}: {val:5.1f} (poids {weights[key]*100:.0f}%)")
    
    print("\n" + "="*70)

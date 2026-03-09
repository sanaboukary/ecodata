#!/usr/bin/env python3
"""
TRADABLE UNIVERSE BRVM — Source de vérité unique
=================================================
Consommé par : multi_factor_engine.py, decision_finale_brvm.py,
               top5_engine_final.py, backtest_daily_v2.py,
               ablation_study.py

Remplace la constante UNIVERSE={12 symboles} hardcodée dans decision_finale_brvm.py
et les définitions locales dispersées dans les autres fichiers.

Deux modes d'utilisation :
  1. Import statique  : from tradable_universe import UNIVERSE_BRVM_SET
  2. Filtre dynamique : get_tradable_universe(db) → filtre par liquidité réelle
"""

# ─── Univers officiel BRVM Equities (47 actions listées) ────────────────────
# Liste réglementaire complète. NE PAS MODIFIER sauf nouvelle cotation/radiation.
UNIVERSE_BRVM_47 = [
    "ABJC", "BICB", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS",
    "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC", "LNBB", "NEIC", "NSBC",
    "NTLC", "ONTBF", "ORAC", "ORGT", "PALC", "PRSC", "SAFC", "SCRC", "SDCC", "SDSC",
    "SEMC", "SGBC", "SHEC", "SIBC", "SICC", "SIVC", "SLBC", "SMBC", "SNTS", "SOGC",
    "SPHC", "STAC", "STBC", "TTLC", "TTLS", "UNLC", "UNXC",
]

# ─── Symboles exclus du moteur de recommandation ────────────────────────────
# Raison : historique insuffisant pour calculer des percentiles cross-sectionnels fiables.
# Condition de ré-inclusion : >= MIN_HISTORIQUE_JOURS jours de données réelles dans prices_daily.
# Ces actions restent dans UNIVERSE_BRVM_47 (liste réglementaire) mais sont exclues
# de UNIVERSE_BRVM_SET (univers de recommandation actif).
MIN_HISTORIQUE_JOURS = 500  # ~2 ans de séances BRVM (~250j/an)

SYMBOLS_HISTORIQUE_INSUFFISANT = {
    "BICB",  # ~132 jours disponibles (cotation récente — pas de données Sika Finance)
    "BNBC",  # ~132 jours disponibles (cotation récente — pas de données Sika Finance)
    "LNBB",  # ~132 jours disponibles (cotation récente — pas de données Sika Finance)
    # UNLC : ~563 jours — sous surveillance (proche du seuil MIN_HISTORIQUE_JOURS)
    # Ré-intégration automatique via get_tradable_universe(db) dès que volume réel confirmé.
}

# ─── Univers de recommandation actif (44 actions) ───────────────────────────
# Exclut les actions sans historique suffisant pour le modèle cross-sectionnel.
UNIVERSE_BRVM_SET = set(UNIVERSE_BRVM_47) - SYMBOLS_HISTORIQUE_INSUFFISANT

# Indices à exclure systématiquement (pas des actions tradables)
INDICES_BRVM = {"BRVM-PRESTIGE", "BRVM-COMPOSITE", "BRVM-10", "BRVM-30", "BRVMC", "BRVM10"}


def get_tradable_universe(
    db=None,
    min_val_fcfa: int = 1_000_000,
    min_jours_trades: int = 5,
    min_historique_jours: int = MIN_HISTORIQUE_JOURS,
) -> list:
    """
    Retourne la liste des symboles BRVM éligibles au trading.

    Sans db  : retourne l'univers de recommandation actif (UNIVERSE_BRVM_SET).
    Avec db  : filtre par liquidité réelle ET historique minimum sur prices_daily.

    Args:
        db                  : instance pymongo database (optionnel)
        min_val_fcfa        : valeur min échangée en FCFA/jour sur 20j (défaut 1 000 000)
        min_jours_trades    : nb jours minimum avec volume > 0 sur 20j (défaut 5)
        min_historique_jours: nb jours minimum de données dans prices_daily (défaut 500)

    Returns:
        list[str] : symboles tradables BRVM triés alphabétiquement
    """
    if db is None:
        return sorted(UNIVERSE_BRVM_SET)

    tradable = []
    for sym in UNIVERSE_BRVM_47:
        # Filtre 1 : exclusion explicite des symboles sans historique
        if sym in SYMBOLS_HISTORIQUE_INSUFFISANT:
            continue

        docs = list(db.prices_daily.find(
            {"symbol": sym, "close": {"$gt": 0}},
            {"volume": 1, "close": 1, "date": 1}
        ).sort("date", -1).limit(20))

        if not docs:
            continue

        # Filtre 2 : historique total minimum (percentile cross-sectionnel fiable)
        total_docs = db.prices_daily.count_documents({"symbol": sym, "close": {"$gt": 0}})
        if total_docs < min_historique_jours:
            continue

        # Filtre 3 : liquidité réelle sur les 20 derniers jours
        valeurs = [d.get("volume", 0) * d.get("close", 0) for d in docs]
        jours   = sum(1 for d in docs if (d.get("volume") or 0) > 0)
        val_moy = sum(valeurs) / len(valeurs) if valeurs else 0

        if val_moy >= min_val_fcfa and jours >= min_jours_trades:
            tradable.append(sym)

    return sorted(tradable)


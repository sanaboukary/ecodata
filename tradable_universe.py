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

# ─── Univers complet BRVM Equities (47 actions officielles) ─────────────────
UNIVERSE_BRVM_47 = [
    "ABJC", "BICB", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS",
    "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC", "LNBB", "NEIC", "NSBC",
    "NTLC", "ONTBF", "ORAC", "ORGT", "PALC", "PRSC", "SAFC", "SCRC", "SDCC", "SDSC",
    "SEMC", "SGBC", "SHEC", "SIBC", "SICC", "SIVC", "SLBC", "SMBC", "SNTS", "SOGC",
    "SPHC", "STAC", "STBC", "TTLC", "TTLS", "UNLC", "UNXC",
]

# Ensemble dédupliqué pour lookups O(1)
UNIVERSE_BRVM_SET = set(UNIVERSE_BRVM_47)

# Indices à exclure systématiquement (pas des actions tradables)
INDICES_BRVM = {"BRVM-PRESTIGE", "BRVM-COMPOSITE", "BRVM-10", "BRVM-30", "BRVMC", "BRVM10"}


def get_tradable_universe(
    db=None,
    min_val_fcfa: int = 1_000_000,
    min_jours_trades: int = 5,
) -> list:
    """
    Retourne la liste des symboles BRVM éligibles au trading.

    Sans db  : retourne l'univers statique complet (47 symboles).
    Avec db  : filtre par liquidité réelle sur les 20 derniers jours.

    Args:
        db              : instance pymongo database (optionnel)
        min_val_fcfa    : valeur minimale échangée en FCFA/jour (défaut 1 000 000)
        min_jours_trades: nb jours minimum avec volume > 0 sur 20j (défaut 5)

    Returns:
        list[str] : symboles tradables BRVM triés alphabétiquement
    """
    if db is None:
        return sorted(UNIVERSE_BRVM_47)

    tradable = []
    for sym in UNIVERSE_BRVM_47:
        docs = list(db.prices_daily.find(
            {"symbol": sym, "close": {"$gt": 0}},
            {"volume": 1, "close": 1}
        ).sort("date", -1).limit(20))

        if not docs:
            continue

        valeurs = [d.get("volume", 0) * d.get("close", 0) for d in docs]
        jours   = sum(1 for d in docs if (d.get("volume") or 0) > 0)
        val_moy = sum(valeurs) / len(valeurs) if valeurs else 0

        if val_moy >= min_val_fcfa and jours >= min_jours_trades:
            tradable.append(sym)

    return sorted(tradable)

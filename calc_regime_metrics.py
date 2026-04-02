#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGIME METRICS CALCULATOR
=========================
Détecte régime marché (BULL/NEUTRAL/ALERTE) base sur volatilité + breadth.
Populate collection volatility_regime_weekly (TTL 7j).

Usage:
  python calc_regime_metrics.py --current      # détection régime actuel
  python calc_regime_metrics.py --save         # sauvegarder dans MongoDB
  python calc_regime_metrics.py --history      # retrocalcul historique
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from plateforme_centralisation.mongo import get_mongo_db
except ImportError:
    print("[ERROR] Impossible d'importer get_mongo_db")
    sys.exit(1)


# ─── Mapping Régime → Paramètres ────────────────────────────────────────

REGIME_MAPPING = {
    "BULL": {
        "rsi_liq_max": 65,
        "atr_sweet_min": 0.08,
        "atr_sweet_max": 0.15,
        "vol_min_ratio": 1.5,
        "score_min": 75,
        "max_pos": 5,
        "exposure_factor": 1.0,
    },
    "NEUTRAL": {
        "rsi_liq_max": 60,
        "atr_sweet_min": 0.08,
        "atr_sweet_max": 0.12,
        "vol_min_ratio": 1.7,
        "score_min": 80,
        "max_pos": 3,
        "exposure_factor": 0.7,
    },
    "ALERTE": {
        "rsi_liq_max": 55,
        "atr_sweet_min": 0.08,
        "atr_sweet_max": 0.12,
        "vol_min_ratio": 2.0,
        "score_min": 85,
        "max_pos": 1,
        "exposure_factor": 0.5,
    },
}


# ─── Détection Régime ──────────────────────────────────────────────────

def calc_brvm_performance_4w(db, lookback_weeks: int = 4) -> float:
    """
    Calcule performance BRVM (composite) sur N semaines.
    Returns: performance en % (ex: +2.5 ou -1.3)
    """
    # Utiliser proxy SNTS (représente bien BRVM)
    docs = list(db.prices_daily.find(
        {"symbol": "SNTS"},
        sort=[("date", -1)],
        limit=lookback_weeks * 5  # ~5 jours trading par semaine
    ))

    if len(docs) < 2:
        return 0.0

    # Premier et dernier
    close_old = docs[-1].get("close", 0)
    close_new = docs[0].get("close", 0)

    if close_old <= 0:
        return 0.0

    return ((close_new - close_old) / close_old) * 100.0


def calc_brvm_volatility(db, lookback_weeks: int = 4) -> float:
    """
    Calcule volatilité BRVM médiane (ATR% moyen).
    Returns: ATR% (ex: 7.5)
    """
    from pipeline_hebdo.config import BRVMC_PROXY_SYMBOLS

    atrs = []

    for sym in BRVMC_PROXY_SYMBOLS[:3]:  # Top 3 proxies
        docs = list(db.prices_daily.find(
            {"symbol": sym},
            sort=[("date", -1)],
            limit=lookback_weeks * 5
        ))

        if len(docs) < 10:
            continue

        # Calculer ATR simple
        trs = []
        for i in range(1, len(docs)):
            high = docs[i].get("high", 0)
            low = docs[i].get("low", 0)
            close_prev = docs[i + 1].get("close", 0) if i + 1 < len(docs) else close_prev

            tr = max(
                high - low,
                abs(high - close_prev),
                abs(low - close_prev)
            )
            if tr > 0:
                trs.append(tr)

        if trs:
            atr = statistics.median(trs)
            close_median = statistics.median([d.get("close", 1) for d in docs])
            atr_pct = (atr / close_median) * 100.0
            atrs.append(atr_pct)

    if not atrs:
        return 7.5  # Default

    return statistics.median(atrs)


def calc_breadth(db, lookback_weeks: int = 4) -> Tuple[int, int, float]:
    """
    Calcule breadth (% actions en hausse vs baisse).
    Returns: (nb_up, nb_down, pct_up)
    """
    from pipeline_hebdo.config import UNIVERSE_BRVM

    nb_up = 0
    nb_down = 0

    for sym in UNIVERSE_BRVM[:30]:  # Top 30 pour vitesse
        docs = list(db.prices_daily.find(
            {"symbol": sym},
            sort=[("date", -1)],
            limit=20
        ))

        if len(docs) < 2:
            continue

        close_old = docs[-1].get("close", 0)
        close_new = docs[0].get("close", 0)

        if close_old <= 0:
            continue

        perf = (close_new - close_old) / close_old

        if perf > 0:
            nb_up += 1
        else:
            nb_down += 1

    total = nb_up + nb_down

    if total == 0:
        return 0, 0, 50.0

    pct_up = (nb_up / total) * 100.0

    return nb_up, nb_down, pct_up


def detect_market_regime(db) -> Dict:
    """
    Détecte régime actuel (BULL/NEUTRAL/ALERTE).

    Returns:
        {
            "regime": "BULL" | "NEUTRAL" | "ALERTE",
            "brvm_perf_4w": float,
            "brvm_vol": float,
            "breadth_up_pct": float,
            "breadth_nb_up": int,
            "breadth_nb_down": int,
            "stress_level": "FAIBLE" | "MODÉRÉ" | "ÉLEVÉ",
            "exposure_factor": float,
            "params": dict (mapping REGIME_MAPPING),
            "timestamp": str,
        }
    """
    perf = calc_brvm_performance_4w(db)
    vol = calc_brvm_volatility(db)
    nb_up, nb_down, pct_up = calc_breadth(db)

    # Logique détection (simplifié)
    stress = "FAIBLE"
    regime = "NEUTRAL"

    if vol > 12.0:
        stress = "ÉLEVÉ"
        regime = "ALERTE"
    elif vol > 8.0:
        stress = "MODÉRÉ"
        if perf > 0 and pct_up > 55:
            regime = "NEUTRAL"
        else:
            regime = "ALERTE"
    else:
        stress = "FAIBLE"
        if perf > 1.5 and pct_up > 60:
            regime = "BULL"
        elif perf < -1.5 and pct_up < 40:
            regime = "ALERTE"
        else:
            regime = "NEUTRAL"

    params = REGIME_MAPPING.get(regime, REGIME_MAPPING["NEUTRAL"])

    return {
        "regime": regime,
        "brvm_perf_4w": round(perf, 2),
        "brvm_vol": round(vol, 1),
        "breadth_up_pct": round(pct_up, 1),
        "breadth_nb_up": nb_up,
        "breadth_nb_down": nb_down,
        "stress_level": stress,
        "exposure_factor": params["exposure_factor"],
        "params": params,
        "timestamp": datetime.now().isoformat(),
    }


# ─── Sauvegarde ────────────────────────────────────────────────────────

def save_regime_snapshot(db) -> Dict:
    """
    Calcule + sauvegarde snapshot régime actuel.
    Returns: snapshot sauvegardé
    """
    regime_snapshot = detect_market_regime(db)

    # Ajouter metadata
    regime_snapshot["week"] = f"W{datetime.now().isocalendar()[1]}_{datetime.now().year}"
    regime_snapshot["date"] = datetime.now().date().isoformat()
    regime_snapshot["expires_at"] = datetime.now() + timedelta(weeks=1)

    # Sauvegarder
    db.volatility_regime_weekly.update_one(
        {"week": regime_snapshot["week"]},
        {"$set": regime_snapshot},
        upsert=True
    )

    # TTL index
    try:
        db.volatility_regime_weekly.create_index(
            "expires_at",
            expireAfterSeconds=0
        )
    except Exception:
        pass

    return regime_snapshot


def get_current_regime(db) -> Dict:
    """Récupère régime actuel (dernier enregistré)."""
    doc = db.volatility_regime_weekly.find_one(
        sort=[("timestamp", -1)]
    )

    if not doc:
        return detect_market_regime(db)

    return doc


def report_regime(db) -> str:
    """Génère rapport régime lisible."""
    regime = get_current_regime(db)

    lines = [
        f"\n📊 RÉGIME MARCHÉ BRVM — {regime.get('timestamp', 'N/A')[:10]}\n",
        f"  Régime actuel : {regime['regime']}",
        f"  Stress level  : {regime['stress_level']}",
        f"  Performance 4w: {regime['brvm_perf_4w']:+.1f}%",
        f"  Volatilité    : {regime['brvm_vol']:.1f}% ATR",
        f"  Breadth       : {regime['breadth_up_pct']:.0f}% up ({regime['breadth_nb_up']} up, {regime['breadth_nb_down']} down)",
        f"  Exposure      : {regime['exposure_factor']:.1%}",
        "",
        f"  Paramètres {regime['regime']}:",
        f"    - Score min   : {regime['params']['score_min']}",
        f"    - Max pos     : {regime['params']['max_pos']}",
        f"    - ATR sweet   : {regime['params']['atr_sweet_min']:.1%} - {regime['params']['atr_sweet_max']:.1%}",
    ]

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Regime Metrics Calculator")
    parser.add_argument("--current", action="store_true", help="Afficher régime actuel")
    parser.add_argument("--save", action="store_true", help="Sauvegarder snapshot")
    parser.add_argument("--history", action="store_true", help="Retrocalcul historique")

    args = parser.parse_args()

    try:
        _, db = get_mongo_db()
    except Exception as e:
        print(f"[ERROR] Connexion MongoDB: {e}")
        return

    if args.current:
        print(report_regime(db))

    elif args.save:
        snapshot = save_regime_snapshot(db)
        print(f"\n✅ Snapshot régime sauvegardé: {snapshot['regime']}")
        print(report_regime(db))

    elif args.history:
        print("\n[INFO] Retrocalcul historique lancé (future enhancement)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

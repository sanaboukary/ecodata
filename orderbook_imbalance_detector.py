#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORDERBOOK IMBALANCE DETECTOR — PHASE 1 ALTERNATIVE
===================================================
Alternative légère à boaksdirect Selenium.
Calcule bid/ask imbalance proxy depuis données BRVM existantes.

Phase 1 DÉCOUVERTE (non-bloquant):
  Estime l'imbalance carnet depuis prix/volume intra-jour
  Détecte manipulations potentielles (imbalance > 5x)
  Sauvegarde dans orderbook_imbalance collection (TTL 24h)

Usage:
  python orderbook_imbalance_detector.py --analyze SNTS
  python orderbook_imbalance_detector.py --report
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from plateforme_centralisation.mongo import get_mongo_db
except ImportError:
    print("[ERROR] Impossible d'importer get_mongo_db — vérifier plateforme_centralisation")
    sys.exit(1)


# ─── Constantes ────────────────────────────────────────────────────────────

# Seuils imbalance (bid_vol / ask_vol)
IMBALANCE_THRESHOLD_ALERT    = 3.0   # 3x = attention
IMBALANCE_THRESHOLD_MANIP    = 5.0   # 5x+ = suspicion manipulation
IMBALANCE_MIN_VOLUME         = 100   # volumes minimums pour calcul


# ─── Calcul Imbalance Proxy ────────────────────────────────────────────────

def calc_imbalance_proxy_from_intraday(
    docs_daily: List[Dict],
    symbol: str,
) -> Dict[str, float]:
    """
    Estime bid/ask imbalance depuis patterns intra-jour.

    Logique (simple mais robuste pour BRVM):
      - High = prix acheteurs agressifs (demand pressure)
      - Low  = prix vendeurs (supply pressure)
      - Close = dernier prix

    Imbalance proxy = (High - Close) / (Close - Low)
      Si > 5    → souvent acheteurs (bid pressure)
      Si < 0.2  → souvent vendeurs (ask pressure)

    Returns:
        {
            "imbalance_ratio": float,
            "bid_pressure": float (0-1),
            "ask_pressure": float (0-1),
            "signal": "NEUTRAL" | "BID_STRONG" | "ASK_STRONG" | "THIN_MARKET",
            "confidence": float (0-1),
        }
    """
    if not docs_daily or len(docs_daily) < 5:
        return {
            "imbalance_ratio": 1.0,
            "bid_pressure": 0.5,
            "ask_pressure": 0.5,
            "signal": "INSUFFICIENT_DATA",
            "confidence": 0.0,
        }

    # Derniers 5 jours
    recent = docs_daily[-5:]
    ratios = []

    for doc in recent:
        high = doc.get("high", 0)
        low = doc.get("low", 0)
        close = doc.get("close", 0)

        if not (high > 0 and low > 0 and close > 0):
            continue

        # Éviter division par zéro
        if close == low:
            ratio = 1.0
        else:
            numerator = max(0.01, high - close)
            denominator = max(0.01, close - low)
            ratio = numerator / denominator

        ratios.append(ratio)

    if not ratios:
        return {
            "imbalance_ratio": 1.0,
            "bid_pressure": 0.5,
            "ask_pressure": 0.5,
            "signal": "NO_VALID_DATA",
            "confidence": 0.0,
        }

    # Moyenne ratios
    avg_ratio = sum(ratios) / len(ratios)

    # Normaliser 0-1
    bid_pressure = max(0.0, min(1.0, avg_ratio / (1.0 + avg_ratio)))
    ask_pressure = 1.0 - bid_pressure

    # Signal
    if avg_ratio > IMBALANCE_THRESHOLD_MANIP:
        signal = "BID_STRONG"  # Carnet biaisé acheteurs
    elif avg_ratio < (1.0 / IMBALANCE_THRESHOLD_MANIP):
        signal = "ASK_STRONG"  # Carnet biaisé vendeurs
    elif high - low < 0.005 * close:  # Range < 0.5%
        signal = "THIN_MARKET"  # Marché illiquide
    else:
        signal = "NEUTRAL"

    return {
        "imbalance_ratio": round(avg_ratio, 3),
        "bid_pressure": round(bid_pressure, 2),
        "ask_pressure": round(ask_pressure, 2),
        "signal": signal,
        "confidence": round(len(ratios) / 5.0, 2),  # % jours valides
    }


def detect_manipulation_risk(imbalance: Dict) -> Tuple[bool, str]:
    """
    Détecte risque manipulation basé sur imbalance.

    Returns: (is_manipulation_suspected, reason)
    """
    if imbalance["confidence"] < 0.6:
        return False, "Données insuffisantes"

    ratio = imbalance["imbalance_ratio"]

    if ratio > IMBALANCE_THRESHOLD_MANIP:
        return True, f"Bid pressure extrême (ratio {ratio:.1f}x) — possible pump"

    if ratio < (1.0 / IMBALANCE_THRESHOLD_MANIP):
        return True, f"Ask pressure extrême (ratio 1/{ratio:.2f}) — possible dump"

    # Vérifier volatilité du ratio (instabilité = signe alerte)
    if imbalance["signal"] == "THIN_MARKET":
        return False, "Marché illiquide — pas trading"

    return False, "OK"


# ─── Collecte et Sauvegarde ────────────────────────────────────────────────

def collect_and_save_imbalances(db, symbol: str = None) -> Dict:
    """
    Collecte imbalances pour 1 symbole ou tous.
    Sauvegarde dans orderbook_imbalance collection (TTL 24h).

    Returns: rapport d'exécution
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "symbols_processed": 0,
        "alerts_generated": 0,
        "manipulations_suspected": [],
    }

    # Lire universe si pas de symbole spécifique
    if symbol:
        symbols = [symbol]
    else:
        from pipeline_hebdo.config import UNIVERSE_BRVM
        symbols = UNIVERSE_BRVM

    for sym in symbols:
        # Chercher derniers 20 jours de prices_daily
        docs = list(db.prices_daily.find(
            {"symbol": sym},
            sort=[("date", -1)],
            limit=20
        ))

        if not docs:
            continue

        # Calculer imbalance
        imbalance = calc_imbalance_proxy_from_intraday(list(reversed(docs)), sym)
        is_manip, reason = detect_manipulation_risk(imbalance)

        # Sauvegarder dans MongoDB
        record = {
            "symbol": sym,
            "timestamp": datetime.now(),
            "imbalance": imbalance,
            "is_manipulation_suspected": is_manip,
            "reason": reason,
            "expires_at": datetime.now() + timedelta(hours=24),
        }

        db.orderbook_imbalance.update_one(
            {"symbol": sym},
            {"$set": record},
            upsert=True
        )

        report["symbols_processed"] += 1

        if is_manip:
            report["manipulations_suspected"].append({
                "symbol": sym,
                "reason": reason,
                "ratio": imbalance["imbalance_ratio"],
            })
            report["alerts_generated"] += 1

        # Log
        signal = imbalance["signal"]
        confidence = imbalance["confidence"]
        print(f"  {sym:6s} | {signal:15s} | ratio={imbalance['imbalance_ratio']:6.2f} | conf={confidence:.1%}")

    return report


def get_imbalance_for_symbol(db, symbol: str) -> Optional[Dict]:
    """Récupère dernier imbalance calc pour un symbole."""
    return db.orderbook_imbalance.find_one(
        {"symbol": symbol},
        sort=[("timestamp", -1)]
    )


def report_imbalances(db) -> str:
    """Génère rapport des imbalances actuelles."""
    docs = list(db.orderbook_imbalance.find(
        {"is_manipulation_suspected": True},
        sort=[("timestamp", -1)]
    ))

    if not docs:
        return "✅ Aucune suspicion de manipulation actuellement."

    lines = [f"\n⚠️  ALERTES IMBALANCE — {len(docs)} symbole(s) suspects:\n"]
    for doc in docs:
        sym = doc["symbol"]
        reason = doc["reason"]
        ratio = doc["imbalance"]["imbalance_ratio"]
        lines.append(f"  [{sym}] ratio={ratio:.1f}x — {reason}")

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Orderbook Imbalance Detector")
    parser.add_argument("--analyze", help="Analyser 1 symbole", metavar="SYMBOL")
    parser.add_argument("--all", action="store_true", help="Analyser tous les symboles")
    parser.add_argument("--report", action="store_true", help="Afficher rapport alertes")

    args = parser.parse_args()

    try:
        _, db = get_mongo_db()
    except Exception as e:
        print(f"[ERROR] Connexion MongoDB: {e}")
        return

    # TTL index (crée automatiquement si absent)
    try:
        db.orderbook_imbalance.create_index(
            "expires_at",
            expireAfterSeconds=0
        )
    except Exception:
        pass

    if args.report:
        print(report_imbalances(db))

    elif args.analyze:
        print(f"\n[ANALYSE] Imbalance pour {args.analyze}:\n")
        report = collect_and_save_imbalances(db, symbol=args.analyze)
        print(f"\n  Traité: {report['symbols_processed']} | Alertes: {report['alerts_generated']}")

    elif args.all:
        print(f"\n[ANALYSE] Tous les symboles UNIVERSE:\n")
        report = collect_and_save_imbalances(db)
        print(f"\n  Traité: {report['symbols_processed']} | Alertes: {report['alerts_generated']}")
        if report["manipulations_suspected"]:
            print(f"\n  Symboles suspects: {[s['symbol'] for s in report['manipulations_suspected']]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

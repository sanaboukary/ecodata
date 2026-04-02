#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLIPPAGE OBSERVER
=================
Enregistre slippage réel observé lors d'exécutions.
Compare prédictions vs réalité pour calibration friction gate.

Collection: slippage_observed (TTL 30j).

Usage:
  python slippage_observer.py --log SNTS 1000000 23500 23400   # log trade réel
  python slippage_observer.py --report                         # rapport calibration
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import statistics

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from plateforme_centralisation.mongo import get_mongo_db
except ImportError:
    print("[ERROR] Impossible d'importer get_mongo_db")
    sys.exit(1)


# ─── Slippage Estimation ────────────────────────────────────────────────

def classify_liquidity_class(adv_fcfa: float) -> str:
    """Classe liquidité depuis ADV."""
    if adv_fcfa >= 10_000_000:
        return "A"
    elif adv_fcfa >= 5_000_000:
        return "B"
    elif adv_fcfa >= 2_000_000:
        return "C"
    else:
        return "D"


def estimate_slippage_pct(symbol: str, ticket_fcfa: float, classe: str) -> float:
    """
    Estime slippage théorique.
    Basé sur classe liquidité.
    """
    slippage_base = {
        "A": 0.50,   # 0.5%
        "B": 1.00,   # 1.0%
        "C": 2.00,   # 2.0%
        "D": 3.50,   # 3.5%
    }

    # Amplifier si ticket large (>25% ADV)
    amplifier = 1.0
    if ticket_fcfa > 5_000_000:
        amplifier = 1.3

    return slippage_base.get(classe, 1.0) * amplifier


def record_execution(
    db,
    symbol: str,
    ticket_fcfa: float,
    entry_planned: float,
    entry_actual: float,
    classe: str,
    trade_type: str = "ENTRY",  # ENTRY or EXIT
) -> Dict:
    """
    Enregistre execution donnée et calcule slippage réel.

    Args:
        db: MongoDB instance
        symbol: Code action
        ticket_fcfa: Montant transactionné
        entry_planned: Prix prédiction entrée
        entry_actual: Prix réel entrée
        classe: A/B/C/D
        trade_type: ENTRY ou EXIT

    Returns: Record sauvegardé
    """
    if entry_planned <= 0 or entry_actual <= 0:
        return None

    # Slippage réel en %
    slippage_real = abs((entry_actual - entry_planned) / entry_planned) * 100.0

    # Slippage estimé
    slippage_est = estimate_slippage_pct(symbol, ticket_fcfa, classe)

    # Écart avec estimation (diagnostic)
    var_vs_estimate = slippage_real - slippage_est

    record = {
        "symbol": symbol,
        "trade_type": trade_type,
        "date": datetime.now().date().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "ticket_fcfa": ticket_fcfa,
        "prix_planifie": entry_planned,
        "prix_reel": entry_actual,
        "slippage_reel_pct": round(slippage_real, 3),
        "slippage_estime_pct": round(slippage_est, 3),
        "variance_vs_estimate": round(var_vs_estimate, 3),
        "classe": classe,
        "expires_at": datetime.now() + timedelta(days=30),
    }

    # Sauvegarder
    db.slippage_observed.insert_one(record)

    # TTL index
    try:
        db.slippage_observed.create_index(
            "expires_at",
            expireAfterSeconds=0
        )
    except Exception:
        pass

    return record


def calibrate_slippage_gate(db) -> Dict:
    """
    Analyse slippage réels observés.
    Recommande calibrage friction gate.

    Returns: calibration report
    """
    docs = list(db.slippage_observed.find(
        {"trade_type": "ENTRY"},
        sort=[("timestamp", -1)],
        limit=50
    ))

    if not docs:
        return {
            "status": "INSUFFICIENT_DATA",
            "note": "< 10 executions réelles enregistrées",
            "recommendation": "Continuer tracking slippage réel",
        }

    # Par classe
    by_classe = {}

    for doc in docs:
        classe = doc["classe"]
        real_slip = doc["slippage_reel_pct"]
        est_slip = doc["slippage_estime_pct"]

        if classe not in by_classe:
            by_classe[classe] = {
                "real_slips": [],
                "est_slips": [],
                "variances": [],
            }

        by_classe[classe]["real_slips"].append(real_slip)
        by_classe[classe]["est_slips"].append(est_slip)
        by_classe[classe]["variances"].append(doc["variance_vs_estimate"])

    # Analyse
    import statistics

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_executions": len(docs),
        "by_classe": {},
        "recommendations": [],
    }

    for classe in ["A", "B", "C", "D"]:
        if classe not in by_classe:
            continue

        data = by_classe[classe]
        avg_real = statistics.mean(data["real_slips"])
        med_real = statistics.median(data["real_slips"])
        max_real = max(data["real_slips"])
        avg_var = statistics.mean(data["variances"])

        report["by_classe"][classe] = {
            "n_executions": len(data["real_slips"]),
            "slippage_real_mean": round(avg_real, 3),
            "slippage_real_median": round(med_real, 3),
            "slippage_real_max": round(max_real, 3),
            "variance_vs_estimate_mean": round(avg_var, 3),
        }

        # Recommandation
        if avg_var > 0.5:
            report["recommendations"].append(
                f"Classe {classe}: friction gate calibrée -2{int(avg_var)}% "
                f"(réel mean={avg_real:.2f}% vs estime)"
            )

    return report


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Slippage Observer")
    parser.add_argument(
        "--log",
        nargs=4,
        metavar=("SYMBOL", "TICKET", "PRIX_PLAN", "PRIX_REEL"),
        help="Enregistrer une execution"
    )
    parser.add_argument("--report", action="store_true", help="Rapport calibration")

    args = parser.parse_args()

    try:
        _, db = get_mongo_db()
    except Exception as e:
        print(f"[ERROR] Connexion MongoDB: {e}")
        return

    if args.log:
        try:
            symbol = args.log[0]
            ticket = float(args.log[1])
            prix_plan = float(args.log[2])
            prix_real = float(args.log[3])

            # Estimer classe depuis historique
            docs = list(db.prices_daily.find(
                {"symbol": symbol},
                sort=[("date", -1)],
                limit=20
            ))
            adv = 0
            if docs:
                adv = statistics.median([
                    d.get("close", 0) * d.get("volume", 0)
                    for d in docs if d.get("close", 0) > 0
                ])

            classe = classify_liquidity_class(adv)

            record = record_execution(
                db, symbol, ticket, prix_plan, prix_real, classe
            )

            if record:
                slip_real = record["slippage_reel_pct"]
                slip_est = record["slippage_estime_pct"]
                print(f"\n✅ Execution enregistrée:")
                print(f"   {symbol} | ticket={ticket} FCFA")
                print(f"   Slippage réel: {slip_real:.3f}%")
                print(f"   Slippage estimé: {slip_est:.3f}%")
                print(f"   Variance: {record['variance_vs_estimate']:+.3f}%\n")

        except ValueError as e:
            print(f"[ERROR] Format: --log SYMBOL TICKET PRIX_PLAN PRIX_REEL (numbers)")

    elif args.report:
        report = calibrate_slippage_gate(db)
        print(f"\n📊 RAPPORT SLIPPAGE — {report['timestamp'][:10]}")
        print(f"   Total executions: {report['total_executions']}\n")

        if report.get("by_classe"):
            for classe in ["A", "B", "C", "D"]:
                if classe in report["by_classe"]:
                    data = report["by_classe"][classe]
                    print(f"   Classe {classe}:")
                    print(f"     - n={data['n_executions']} | real_mean={data['slippage_real_mean']:.3f}% | real_max={data['slippage_real_max']:.3f}%")
                    print(f"     - vs_estimate: {data['variance_vs_estimate_mean']:+.3f}%")

        if report.get("recommendations"):
            print(f"\n   ⚠️  Recommandations:")
            for rec in report["recommendations"]:
                print(f"     • {rec}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

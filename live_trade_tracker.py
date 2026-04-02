#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVE TRADE TRACKER — PAPER TRADING MONITOR
===========================================
Enregistre chaque TOP5 launch et suite des trades (39 jours +).
Comparée automatiquement avec track_record_weekly pour validation simulation.

Collection: recommandations_live (TTL 60j).

Usage:
  python live_trade_tracker.py --launch       # lancer TOP5, enregistrer dans live
  python live_trade_tracker.py --update SNTS  # mettre à jour prix réel SNTS
  python live_trade_tracker.py --validate     # comparer live vs simulation
  python live_trade_tracker.py --report       # rapport complet
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from plateforme_centralisation.mongo import get_mongo_db
except ImportError:
    print("[ERROR] Impossible d'importer get_mongo_db")
    sys.exit(1)


# ─── Capture TOP5 Launch ────────────────────────────────────────────────

def capture_top5_launch(db) -> Optional[Dict]:
    """
    Capture TOP5 récent de top5_weekly_brvm.
    Crée un record live pour tracking.

    Returns: launch_record (ou None si pas de TOP5 actuel)
    """
    # Lire TOP5 actuel (dernier)
    top5 = list(db.top5_weekly_brvm.find(
        sort=[("timestamp", -1)],
        limit=5
    ))

    if not top5:
        return None

    record = {
        "launch_id": f"LIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "launch_date": datetime.now(),
        "launch_date_planned": datetime.now() + timedelta(days=25),  # J+25
        "simulation_top5": top5,
        "trades": [],  # À remplir lors des updates
        "status": "ACTIVE",
        "benchmark_vs_simulation": {},  # Rempli par validate()
        "expires_at": datetime.now() + timedelta(days=60),
    }

    # Initialiser trades depuis top5
    for i, top5_doc in enumerate(top5):
        trade = {
            "rank": i + 1,
            "symbol": top5_doc.get("symbol"),
            "entry_planned": top5_doc.get("entry_price", 0),
            "entry_actual": None,  # À remplir
            "entry_date": None,    # À remplir
            "tp1": top5_doc.get("tp1_price"),
            "tp2": top5_doc.get("tp2_price"),
            "stop": top5_doc.get("stop_price"),
            "wos_planned": top5_doc.get("wos", 0),
            "gain_planned_pct": top5_doc.get("gain", 0),
            "status": "PENDING",  # PENDING → EXECUTED → TP1/TP2/STOP/EXPIRE
            "exit_type": None,
            "exit_price": None,
            "exit_date": None,
            "gain_real_pct": None,
        }
        record["trades"].append(trade)

    # Sauvegarder
    db.recommandations_live.insert_one(record)

    # TTL index
    try:
        db.recommandations_live.create_index(
            "expires_at",
            expireAfterSeconds=0
        )
    except Exception:
        pass

    return record


def update_trade_execution(db, launch_id: str, symbol: str, entry_actual: float, entry_date: str = None) -> bool:
    """
    Met à jour track d'un trade avec prix actualité.

    Args:
        launch_id: ID de la launch (ex: LIVE_20260405_091500)
        symbol: Code action
        entry_actual: Prix actuel
        entry_date: Date exécution (défaut: aujourd'hui)

    Returns: OK ou False
    """
    if entry_date is None:
        entry_date = datetime.now().date().isoformat()

    # Trouver launch
    launch = db.recommandations_live.find_one({"launch_id": launch_id})

    if not launch:
        return False

    # Mettre à jour trade correspondant
    for trade in launch["trades"]:
        if trade["symbol"] == symbol:
            trade["entry_actual"] = entry_actual
            trade["entry_date"] = entry_date
            trade["status"] = "EXECUTED"

            # Calculer gain réel si TP/STOP atteint (simplifié)
            if entry_actual >= trade["tp1"]:
                trade["exit_type"] = "TP1"
                trade["exit_price"] = trade["tp1"]
                trade["gain_real_pct"] = ((trade["tp1"] - entry_actual) / entry_actual) * 100.0
            elif entry_actual <= trade["stop"]:
                trade["exit_type"] = "STOP"
                trade["exit_price"] = trade["stop"]
                trade["gain_real_pct"] = ((trade["stop"] - entry_actual) / entry_actual) * 100.0
            else:
                trade["exit_type"] = "PENDING"
                trade["gain_real_pct"] = None

            break

    # Sauvegarder
    db.recommandations_live.update_one(
        {"launch_id": launch_id},
        {"$set": {"trades": launch["trades"]}}
    )

    return True


def validate_against_simulation(db, launch_id: str) -> Dict:
    """
    Comparé live vs simulation (track_record_weekly).
    Calcule alignement WR/Gain/DD.

    Returns: validation report
    """
    # Récupérer live
    live = db.recommandations_live.find_one({"launch_id": launch_id})

    if not live:
        return {"status": "LAUNCH_NOT_FOUND"}

    # Compter trades
    trades_live = live["trades"]
    n_executed = len([t for t in trades_live if t["status"] == "EXECUTED"])
    n_tp = len([t for t in trades_live if t["exit_type"] in ("TP1", "TP2")])
    n_stop = len([t for t in trades_live if t["exit_type"] == "STOP"])

    wr_live = (n_tp / n_executed) * 100.0 if n_executed > 0 else 0

    gains = [t.get("gain_real_pct", 0) for t in trades_live if t.get("gain_real_pct")]
    avg_gain_live = statistics.mean(gains) if gains else 0

    # Comparé vs top5_weekly_brvm (simulation)
    top5_docs = live["simulation_top5"]

    gains_sim = [t.get("gain", 0) for t in top5_docs]
    avg_gain_sim = statistics.mean(gains_sim) if gains_sim else 0

    report = {
        "launch_id": launch_id,
        "timestamp": datetime.now().isoformat(),
        "execution_stats": {
            "n_executed": n_executed,
            "n_tp": n_tp,
            "n_stop": n_stop,
            "wr_pct": round(wr_live, 1),
            "avg_gain_pct": round(avg_gain_live, 2),
        },
        "simulation_stats": {
            "n_planned": len(top5_docs),
            "avg_gain_expected_pct": round(avg_gain_sim, 2),
        },
        "comparison": {
            "wr_delta": round(wr_live - 47, 1),  # Benchmark 47%
            "gain_delta": round(avg_gain_live - avg_gain_sim, 2),
            "status": "VALIDATING" if n_executed < len(top5_docs) else "COMPLETE",
        },
        "verdict": "✅ ON_TRACK" if abs(avg_gain_live - avg_gain_sim) < 2.0 else "⚠️ DIVERGING",
    }

    return report


# ─── Reporting ──────────────────────────────────────────────────────────

def report_active_launches(db) -> str:
    """Affiche tous les launches actifs."""
    launches = list(db.recommandations_live.find(
        {"status": "ACTIVE"},
        sort=[("launch_date", -1)]
    ))

    if not launches:
        return "✅ Aucune launch active."

    lines = [f"\n📊 LAUNCHES ACTIVES — {len(launches)} \n"]

    for launch in launches[:5]:  # Top 5
        lid = launch["launch_id"]
        date = launch["launch_date"].strftime("%Y-%m-%d %H:%M")
        trades = launch["trades"]

        n_executed = len([t for t in trades if t["status"] == "EXECUTED"])
        n_total = len(trades)

        lines.append(f"  [{lid}] {date}")
        lines.append(f"    Trades: {n_executed}/{n_total} executed")

        for trade in trades[:3]:
            symbol = trade["symbol"]
            status_txt = trade["status"]
            if trade["status"] == "EXECUTED":
                gain = trade.get("gain_real_pct", 0)
                exit_type = trade.get("exit_type", "?")
                status_txt = f"✅ {exit_type} ({gain:+.1f}%)"

            lines.append(f"      • {symbol:6s} {status_txt}")

        lines.append("")

    return "\n".join(lines)


def benchmark_report(db) -> str:
    """Génère rapport benchmark live vs simulation."""
    launches = list(db.recommandations_live.find(
        {"status": "ACTIVE"},
        sort=[("launch_date", -1)],
        limit=3
    ))

    if not launches:
        return "❌ Pas de launches pour benchmark."

    lines = ["\n🎯 BENCHMARK LIVE vs SIMULATION\n"]

    for launch in launches:
        report = validate_against_simulation(db, launch["launch_id"])

        exe = report["execution_stats"]
        sim = report["simulation_stats"]
        cmp = report["comparison"]

        lines.append(f"  {launch['launch_id']}")
        lines.append(f"    Live:        WR={exe['wr_pct']:.0f}% | Gain={exe['avg_gain_pct']:.2f}%")
        lines.append(f"    Simulation:  Gain expected={sim['avg_gain_expected_pct']:.2f}%")
        lines.append(f"    Delta:       WR{cmp['wr_delta']:+.0f}pts | Gain{cmp['gain_delta']:+.2f}pts")
        lines.append(f"    Verdict:     {report['verdict']}")
        lines.append("")

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Live Trade Tracker")
    parser.add_argument("--launch", action="store_true", help="Lancer capture TOP5 actuel")
    parser.add_argument("--update", nargs=3, metavar=("LAUNCH_ID", "SYMBOL", "PRIX"), help="Mettre à jour trade")
    parser.add_argument("--validate", metavar="LAUNCH_ID", help="Valider contre simulation")
    parser.add_argument("--report", action="store_true", help="Rapport launches actives")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark live vs sim")

    args = parser.parse_args()

    try:
        _, db = get_mongo_db()
    except Exception as e:
        print(f"[ERROR] Connexion MongoDB: {e}")
        return

    if args.launch:
        record = capture_top5_launch(db)
        if record:
            print(f"\n✅ TOP5 launch enregistré: {record['launch_id']}")
            print(f"   {len(record['trades'])} trades pour la validation")
            print(f"   À explorer jusqu'au {record['launch_date_planned'].strftime('%Y-%m-%d')}\n")
        else:
            print("❌ Pas de TOP5 actuel dans top5_weekly_brvm")

    elif args.update:
        launch_id, symbol, prix_str = args.update
        try:
            prix = float(prix_str)
            if update_trade_execution(db, launch_id, symbol, prix):
                print(f"\n✅ Trade {symbol} mis à jour: {prix}")
            else:
                print(f"❌ Launch {launch_id} non trouvée")
        except ValueError:
            print(f"❌ Prix invalide: {prix_str}")

    elif args.validate:
        report = validate_against_simulation(db, args.validate)
        if report.get("status") == "LAUNCH_NOT_FOUND":
            print(f"❌ Launch {args.validate} non trouvée")
        else:
            print(f"\n📊 VALIDATION {args.validate}")
            print(f"   Live WR: {report['execution_stats']['wr_pct']:.0f}% | Gain: {report['execution_stats']['avg_gain_pct']:.2f}%")
            print(f"   Sim Gain: {report['simulation_stats']['avg_gain_expected_pct']:.2f}%")
            print(f"   Delta: WR {report['comparison']['wr_delta']:+.0f}pts | Gain {report['comparison']['gain_delta']:+.2f}pts")
            print(f"   Verdict: {report['verdict']}\n")

    elif args.report:
        print(report_active_launches(db))

    elif args.benchmark:
        print(benchmark_report(db))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

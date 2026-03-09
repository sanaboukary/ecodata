#!/usr/bin/env python3
"""Afficher les raisons derrière le TOP ALPHA V2 (Shadow).

Objectif: rendre les recommandations interprétables.
- Source: MongoDB `centralisation_db.curated_observations`
- Dataset: `ALPHA_V2_SHADOW`
- Affiche: TOP N, facteurs (EM/VS/Ev/Sent), RS 2w/8w et une raison synthétique.

Usage:
  python afficher_raisons_top10_v2.py
  python afficher_raisons_top10_v2.py --limit 15
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Tuple

from pymongo import MongoClient


WEIGHTS = {
    "early_momentum": 0.35,
    "volume_spike": 0.25,
    "event": 0.20,
    "sentiment": 0.20,
}

LABELS = {
    "early_momentum": "Momentum (35%)",
    "volume_spike": "Volume spike (25%)",
    "event": "Event (20%)",
    "sentiment": "Sentiment (20%)",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _driver_contributions(details: Dict[str, Any]) -> List[Tuple[str, float, float]]:
    """Return list of (driver_key, score_0_100, contribution_points)."""
    out: List[Tuple[str, float, float]] = []
    for k, w in WEIGHTS.items():
        s = _safe_float(details.get(k, 0.0), 0.0)
        out.append((k, s, w * s))
    out.sort(key=lambda t: t[2], reverse=True)
    return out


def _reason_text(details: Dict[str, Any]) -> str:
    contrib = _driver_contributions(details)
    top2 = contrib[:2]
    parts = [f"{LABELS[k]}={s:.1f}" for (k, s, _c) in top2]

    rs_2w = _safe_float(details.get("rs_2w", 0.0), 0.0)
    rs_8w = _safe_float(details.get("rs_8w", 0.0), 0.0)

    risk = None
    if rs_2w < 0:
        risk = f"RS2w négatif ({rs_2w:+.1f}%)"
    elif rs_2w > 0:
        risk = f"RS2w positif ({rs_2w:+.1f}%)"

    if risk:
        return "; ".join(parts + [risk, f"RS8w={rs_8w:+.1f}%"])
    return "; ".join(parts + [f"RS8w={rs_8w:+.1f}%"])


def _connect() -> MongoClient:
    # Timeout court pour éviter les hangs si Mongo n'est pas démarré.
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    # Force un ping (fail fast)
    client.admin.command("ping")
    return client


def main() -> int:
    p = argparse.ArgumentParser(description="Afficher les raisons derrière le TOP ALPHA V2")
    p.add_argument("--limit", type=int, default=10, help="Nombre de lignes à afficher (défaut: 10)")
    args = p.parse_args()

    client = _connect()
    try:
        db = client["centralisation_db"]
        docs = list(
            db.curated_observations.find(
                {"dataset": "ALPHA_V2_SHADOW", "attrs.categorie": {"$ne": "REJECTED"}}
            )
            .sort("value", -1)
            .limit(args.limit)
        )

        if not docs:
            print("Aucun document ALPHA_V2_SHADOW trouvé.")
            return 0

        attrs0 = docs[0].get("attrs", {}) or {}
        week_source = attrs0.get("week_source")
        week_target = attrs0.get("week_target")
        week_target_start = attrs0.get("week_target_start")

        print("\n" + "=" * 90)
        print("TOP ALPHA V2 — Raisons (Shadow)")
        print("=" * 90)
        if week_source and week_target:
            print(f"Semaine source (données): {week_source}")
            print(f"Semaine cible (trading) : {week_target} (début {week_target_start})")
        print("-" * 90)
        print(f"{'#':>2}  {'Symbol':<6} {'Alpha':>6} {'Cat':<5}  EM   VS   Ev  Sent   RS2w    RS8w")
        print("-" * 90)

        for i, d in enumerate(docs, 1):
            key = d.get("key")
            value = _safe_float(d.get("value"), 0.0)
            attrs = d.get("attrs", {}) or {}
            cat = attrs.get("categorie")
            details = attrs.get("details", {}) or {}

            em = _safe_float(details.get("early_momentum"), 0.0)
            vs = _safe_float(details.get("volume_spike"), 0.0)
            ev = _safe_float(details.get("event"), 0.0)
            sent = _safe_float(details.get("sentiment"), 0.0)
            rs2 = _safe_float(details.get("rs_2w"), 0.0)
            rs8 = _safe_float(details.get("rs_8w"), 0.0)

            reason = _reason_text(details)

            print(
                f"{i:2d}  {str(key):<6} {value:6.1f} {str(cat):<5}  {em:4.0f} {vs:4.0f} {ev:4.0f} {sent:4.0f}  {rs2:+6.1f}%  {rs8:+6.1f}%"
            )
            print(f"    raison: {reason}")

        print("=" * 90 + "\n")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())

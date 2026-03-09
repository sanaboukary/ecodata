#!/usr/bin/env python3
"""Rattrapage automatique BRVM (daily + weekly).

Objectif:
- Construire les jours daily manquants (ou une plage de dates) à partir de prices_intraday_raw
- Puis construire le weekly à partir de prices_daily

Usage (exemples):
  ./.venv/Scripts/python.exe catchup_daily_weekly.py --daily --weekly --weekly-mode rebuild-all
  ./.venv/Scripts/python.exe catchup_daily_weekly.py --daily --start-date 2026-02-01 --end-date 2026-02-21
  ./.venv/Scripts/python.exe catchup_daily_weekly.py --daily --include-today --dry-run
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime


def _setup_django_and_get_db():
    base_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

    import django  # noqa: WPS433

    django.setup()

    from plateforme_centralisation.mongo import get_mongo_db  # noqa: WPS433

    _, db = get_mongo_db()
    return db


def _parse_args():
    parser = argparse.ArgumentParser(description="Rattrapage daily/weekly BRVM")

    parser.add_argument("--daily", action="store_true", help="Construire/MAJ prices_daily")
    parser.add_argument("--weekly", action="store_true", help="Construire/MAJ prices_weekly")

    parser.add_argument(
        "--start-date",
        help="Limiter le rattrapage à partir de cette date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="Limiter le rattrapage jusqu'à cette date incluse (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--include-today",
        action="store_true",
        help="Inclure la date d'aujourd'hui (sinon on évite un daily partiel)",
    )
    parser.add_argument(
        "--build-existing",
        action="store_true",
        help="Reconstruire aussi les jours déjà présents en daily (sinon: seulement manquants)",
    )

    parser.add_argument(
        "--weekly-mode",
        choices=["rebuild-all", "missing"],
        default="rebuild-all",
        help="Mode weekly: rebuild-all (recommandé) ou missing (plus rapide)",
    )

    parser.add_argument("--dry-run", action="store_true", help="Afficher ce qui serait fait sans écrire")

    args = parser.parse_args()

    # Par défaut: faire les deux si rien n'est précisé
    if not args.daily and not args.weekly:
        args.daily = True
        args.weekly = True

    return args


def _validate_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        raise ValueError(f"Date invalide: {date_str} (attendu YYYY-MM-DD)")


def main():
    args = _parse_args()
    db = _setup_django_and_get_db()

    today = datetime.now().strftime("%Y-%m-%d")

    start_date = _validate_date(args.start_date) if args.start_date else None
    end_date = _validate_date(args.end_date) if args.end_date else None

    if start_date and end_date and start_date > end_date:
        print("❌ Erreur: --start-date > --end-date")
        return 2

    # -----------------------
    # DAILY catch-up
    # -----------------------
    if args.daily:
        from build_daily import build_daily_for_date  # noqa: WPS433

        raw_dates = db.prices_intraday_raw.distinct("date")
        raw_dates = [d for d in raw_dates if isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
        raw_dates = sorted(set(raw_dates))

        if not args.include_today:
            raw_dates = [d for d in raw_dates if d < today]

        if start_date:
            raw_dates = [d for d in raw_dates if d >= start_date]
        if end_date:
            raw_dates = [d for d in raw_dates if d <= end_date]

        existing_daily = set(db.prices_daily.distinct("date"))

        if args.build_existing:
            dates_to_build = raw_dates
        else:
            dates_to_build = [d for d in raw_dates if d not in existing_daily]

        print("\n" + "=" * 80)
        print("RATTRAPAGE DAILY")
        print("=" * 80)
        print(f"Dates RAW intraday (candidates): {len(raw_dates)}")
        print(f"Dates daily existantes         : {len(existing_daily)}")
        print(f"Dates daily à construire       : {len(dates_to_build)}")

        if args.dry_run:
            if dates_to_build:
                print("\nDRY-RUN: premières dates à construire:")
                for d in dates_to_build[:20]:
                    print(f"  - {d}")
            else:
                print("\nDRY-RUN: rien à construire")
        else:
            for i, d in enumerate(dates_to_build, start=1):
                print(f"\n--- DAILY {i}/{len(dates_to_build)} : {d} ---")
                build_daily_for_date(db, d)

    # -----------------------
    # WEEKLY catch-up
    # -----------------------
    if args.weekly:
        from build_weekly import build_weekly_from_daily  # noqa: WPS433

        print("\n" + "=" * 80)
        print("RATTRAPAGE WEEKLY")
        print("=" * 80)

        if args.weekly_mode == "missing":
            daily_dates = db.prices_daily.distinct("date")
            daily_weeks = set()
            for d in daily_dates:
                if not isinstance(d, str):
                    continue
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                except Exception:
                    continue
                y, w, _ = dt.isocalendar()
                daily_weeks.add(f"{y}-W{w:02d}")

            existing_weeks = set(db.prices_weekly.distinct("week"))
            missing_weeks = sorted(daily_weeks - existing_weeks)
            weeks_to_save = set(missing_weeks)

            print(f"Semaines daily disponibles : {len(daily_weeks)}")
            print(f"Semaines weekly existantes : {len(existing_weeks)}")
            print(f"Semaines weekly manquantes : {len(weeks_to_save)}")

            if args.dry_run:
                if weeks_to_save:
                    print("\nDRY-RUN: premières semaines à construire:")
                    for w in sorted(weeks_to_save)[:20]:
                        print(f"  - {w}")
                else:
                    print("\nDRY-RUN: rien à construire")
            else:
                build_weekly_from_daily(db, weeks_to_save=weeks_to_save)
        else:
            print("Mode weekly: rebuild-all (recalcul complet depuis daily)")
            if args.dry_run:
                print("DRY-RUN: weekly rebuild-all non exécuté")
            else:
                build_weekly_from_daily(db, weeks_to_save=None)

    print("\n✅ Rattrapage terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

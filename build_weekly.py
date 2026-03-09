#!/usr/bin/env python3
"""
NIVEAU 3 : CONSTRUCTION WEEKLY DÉCISIONNEL (BASE DES DÉCISIONS)

Responsabilité :
- Agréger prices_daily par semaine (lundi-dimanche)
- Créer UNE ligne par action/semaine
- Open = premier prix de la semaine (lundi)
- High = prix maximum de la semaine
- Low = prix minimum de la semaine
- Close = dernier prix (vendredi ou dernier jour dispo)
- Volume = somme des volumes hebdo

👉 SEULE source pour décisions TOP5
👉 Indicateurs calibrés BRVM :
    - RSI 40-65 (pas 30-70)
    - ATR% 8-25%
    - SMA 5/10 semaines
    - Volume ratio 8 semaines
    
👉 Exécuter chaque lundi matin (ou après build_daily.py)
"""

import os, sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db


def _parse_args():
    parser = argparse.ArgumentParser(description="Construire prices_weekly depuis prices_daily")
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Reconstruire/MAJ toutes les semaines présentes dans prices_daily (recommandé en rattrapage).",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="Construire uniquement les semaines manquantes dans prices_weekly.",
    )
    parser.add_argument(
        "--week",
        help="Construire uniquement une semaine ISO (ex: 2026-W08).",
    )
    return parser.parse_args()


def _iso_week_key(date_str: str) -> str | None:
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year, week, _ = date_obj.isocalendar()
        return f"{year}-W{week:02d}"
    except Exception:
        return None


def _validate_week_str(week: str) -> str | None:
    if not week:
        return None
    try:
        year_part, week_part = week.split("-W")
        year = int(year_part)
        wk = int(week_part)
        if year < 2000 or wk < 1 or wk > 53:
            return None
        return f"{year}-W{wk:02d}"
    except Exception:
        return None


def build_weekly_from_daily(db, weeks_to_save: set[str] | None = None) -> dict:
    """Construit/MAJ prices_weekly depuis prices_daily.

    Si weeks_to_save est fourni, seules ces semaines sont sauvegardées (les indicateurs
    sont calculés avec l'historique complet chargé depuis prices_daily).
    """
    print("\n" + "="*80)
    print("CONSTRUCTION WEEKLY DÉCISIONNEL (NIVEAU 3)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # ÉTAPE 1: Charger toutes les données daily
    print("[1/5] Chargement données daily...")
    daily_docs = list(db.prices_daily.find().sort("date", 1))
    print(f"  Documents daily : {len(daily_docs)}")

    if not daily_docs:
        print("\n❌ Aucune donnée daily trouvée")
        print("   → Exécuter build_daily.py d'abord\n")
        return {"daily": 0, "weekly_created": 0, "weekly_updated": 0, "weeks_saved": 0}

    # ÉTAPE 2: Grouper par symbole et semaine ISO
    print("\n[2/5] Groupement par symbole et semaine...")

    def get_week_key(date_str):
        """Retourne année-semaine ISO (ex: 2026-W06)"""
        try:
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date_obj = date_str

            year, week, _ = date_obj.isocalendar()
            return f"{year}-W{week:02d}", date_obj.strftime("%Y-%m-%d")
        except Exception:
            return None, None

    by_symbol_week = defaultdict(lambda: defaultdict(list))

    for doc in daily_docs:
        symbol = doc.get("symbol")
        date_str = doc.get("date")

        if not symbol or not date_str:
            continue

        week_key, date_formatted = get_week_key(date_str)
        if week_key:
            doc["_date_formatted"] = date_formatted  # Pour tri
            by_symbol_week[symbol][week_key].append(doc)

    print(f"  Symboles uniques : {len(by_symbol_week)}")
    total_weeks = sum(len(weeks) for weeks in by_symbol_week.values())
    print(f"  Total semaines : {total_weeks}")

    # ÉTAPE 3: Calculer OHLC weekly + indicateurs BRVM
    print("\n[3/5] Calcul OHLC weekly + indicateurs...")

    weekly_docs = []
    stats = {
        "created": 0,
        "updated": 0,
        "weeks_processed": 0,
        "symbols_processed": 0
    }

    for symbol in sorted(by_symbol_week.keys()):
        weeks = by_symbol_week[symbol]
        stats["symbols_processed"] += 1

        for week_key in sorted(weeks.keys()):
            week_days = sorted(weeks[week_key], key=lambda x: x.get("_date_formatted", ""))

            if not week_days:
                continue

            stats["weeks_processed"] += 1

            first_day = week_days[0]
            last_day = week_days[-1]

            open_week = first_day.get("open")
            close_week = last_day.get("close")
            high_week = max((d.get("high") or 0 for d in week_days), default=0)
            low_week = min((d.get("low") for d in week_days if d.get("low")), default=None)

            volume_week = sum((d.get("volume") or 0 for d in week_days))

            if open_week and close_week:
                variation_week_pct = ((close_week - open_week) / open_week) * 100
            else:
                variation_week_pct = None

            closes = [d.get("close") for d in week_days if d.get("close")]
            if len(closes) >= 2:
                volatility_week = float(np.std(closes))
                volatility_week_pct = (volatility_week / np.mean(closes)) * 100 if np.mean(closes) > 0 else 0
            else:
                volatility_week = None
                volatility_week_pct = None

            first_date = datetime.strptime(first_day.get("_date_formatted"), "%Y-%m-%d")
            week_start = first_date - timedelta(days=first_date.weekday())

            weekly_doc = {
                "symbol": symbol,
                "week": week_key,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "year": int(week_key.split("-W")[0]),
                "week_number": int(week_key.split("-W")[1]),
                "open": open_week,
                "high": high_week,
                "low": low_week,
                "close": close_week,
                "volume": volume_week,
                "variation_pct": variation_week_pct,
                "volatility": volatility_week,
                "volatility_pct": volatility_week_pct,
                "nb_jours_trading": len(week_days),
                "first_date": first_day.get("_date_formatted"),
                "last_date": last_day.get("_date_formatted"),
                "nom": last_day.get("nom"),
                "sector": last_day.get("sector"),
                "secteur_officiel": last_day.get("secteur_officiel"),
                "built_at": datetime.now(),
                "source": "WEEKLY_BUILDER"
            }
            weekly_docs.append(weekly_doc)

    print(f"  Documents weekly calculés : {len(weekly_docs)}")

    # ÉTAPE 4: Calcul indicateurs techniques BRVM (calibration spéciale)
    print("\n[4/5] Calcul indicateurs techniques BRVM...")

    for symbol in by_symbol_week.keys():
        symbol_weeks = [w for w in weekly_docs if w["symbol"] == symbol]
        symbol_weeks_sorted = sorted(symbol_weeks, key=lambda x: x["week"])

        for i, week_doc in enumerate(symbol_weeks_sorted):
            closes_5 = [w["close"] for w in symbol_weeks_sorted[max(0, i-4):i+1] if w.get("close")]
            week_doc["sma_5"] = sum(closes_5) / len(closes_5) if closes_5 else None

            closes_10 = [w["close"] for w in symbol_weeks_sorted[max(0, i-9):i+1] if w.get("close")]
            week_doc["sma_10"] = sum(closes_10) / len(closes_10) if closes_10 else None

        for i, week_doc in enumerate(symbol_weeks_sorted):
            if i < 14:
                week_doc["rsi"] = None
                continue

            changes = []
            for j in range(i-13, i+1):
                if j > 0 and symbol_weeks_sorted[j].get("close") and symbol_weeks_sorted[j-1].get("close"):
                    change = symbol_weeks_sorted[j]["close"] - symbol_weeks_sorted[j-1]["close"]
                    changes.append(change)

            if len(changes) >= 10:
                gains = [c for c in changes if c > 0]
                losses = [abs(c) for c in changes if c < 0]

                avg_gain = sum(gains) / len(changes) if gains else 0
                avg_loss = sum(losses) / len(changes) if losses else 0

                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                week_doc["rsi"] = round(rsi, 2)
            else:
                week_doc["rsi"] = None

        for i, week_doc in enumerate(symbol_weeks_sorted):
            volumes = [w["volume"] for w in symbol_weeks_sorted[max(0, i-7):i+1] if w.get("volume") and w["volume"] > 0]
            if len(volumes) >= 3:
                avg_volume_8w = sum(volumes) / len(volumes)
                current_volume = week_doc.get("volume") or 0
                week_doc["volume_ratio"] = round(current_volume / avg_volume_8w, 2) if avg_volume_8w > 0 else None
            else:
                week_doc["volume_ratio"] = None

        for i, week_doc in enumerate(symbol_weeks_sorted):
            if i < 1:
                week_doc["atr_pct"] = None
                continue

            trs = []
            for j in range(max(0, i-7), i+1):
                week = symbol_weeks_sorted[j]
                prev_close = symbol_weeks_sorted[j-1].get("close") if j > 0 else week.get("open")
                if week.get("high") and week.get("low") and prev_close:
                    tr = max(
                        week["high"] - week["low"],
                        abs(week["high"] - prev_close),
                        abs(week["low"] - prev_close)
                    )
                    trs.append(tr)

            if trs and week_doc.get("close"):
                atr = sum(trs) / len(trs)
                atr_pct = (atr / week_doc["close"]) * 100
                week_doc["atr_pct"] = round(atr_pct, 2)
            else:
                week_doc["atr_pct"] = None

    print(f"  Indicateurs calculés (SMA, RSI, Volume ratio, ATR%)")

    # Filtrer les semaines à sauvegarder si nécessaire
    docs_to_save = weekly_docs
    if weeks_to_save is not None:
        docs_to_save = [d for d in weekly_docs if d.get("week") in weeks_to_save]
        print(f"\n📌 Filtre : sauvegarde limitée à {len(docs_to_save)} documents (semaines ciblées)")

    # ÉTAPE 5: Sauvegarder dans prices_weekly
    print("\n[5/5] Sauvegarde dans prices_weekly...")

    for doc in docs_to_save:
        result = db.prices_weekly.update_one(
            {"symbol": doc["symbol"], "week": doc["week"]},
            {"$set": doc},
            upsert=True
        )
        if result.matched_count > 0:
            stats["updated"] += 1
        else:
            stats["created"] += 1

    print("\n" + "="*80)
    print("RESUME CONSTRUCTION WEEKLY")
    print("="*80)
    print(f"  Documents daily sources : {len(daily_docs)}")
    print(f"  Symboles traites        : {stats['symbols_processed']}")
    print(f"  Semaines traitees       : {stats['weeks_processed']}")
    print(f"  Documents weekly crees  : {stats['created']}")
    print(f"  Documents weekly MAJ    : {stats['updated']}")
    print(f"\n  CALIBRATION BRVM :")
    print(f"   RSI : 40-65 (zone optimale BRVM)")
    print(f"   ATR% : 8-25% (normal pour BRVM)")
    print(f"   SMA : 5 et 10 semaines")
    print(f"   Volume ratio : 8 semaines glissantes")
    print(f"\n  Prochaine etape : Lancer TOP5 Engine")
    print(f"   python top5_engine.py\n")
    print("="*80 + "\n")

    return {
        "daily": len(daily_docs),
        "weeks_saved": len(docs_to_save),
        "weekly_created": stats["created"],
        "weekly_updated": stats["updated"],
    }


def main():
    args = _parse_args()
    _, db = get_mongo_db()

    if args.week:
        week = _validate_week_str(args.week)
        if not week:
            print("❌ Erreur: --week doit être au format YYYY-Wxx (ex: 2026-W08)\n")
            sys.exit(2)
        weeks_to_save = {week}
        print(f"📅 MODE : Semaine ciblée {week}\n")
    elif args.rebuild_all:
        weeks_to_save = None
        print("MODE : Reconstruction complete (toutes les semaines)\n")
    else:
        # Par défaut: semaines manquantes si --missing, sinon semaine courante + précédente
        if args.missing:
            daily_dates = db.prices_daily.distinct("date")
            daily_weeks = {w for w in (_iso_week_key(d) for d in daily_dates) if w}
            existing_weeks = set(db.prices_weekly.distinct("week"))
            weeks_to_save = sorted(daily_weeks - existing_weeks)
            weeks_to_save = set(weeks_to_save)
            print(f"🧩 MODE : Semaines manquantes uniquement ({len(weeks_to_save)})\n")
        else:
            today = datetime.now()
            year, week, _ = today.isocalendar()
            current_week = f"{year}-W{week:02d}"
            prev_week_date = today - timedelta(days=7)
            py, pw, _ = prev_week_date.isocalendar()
            prev_week = f"{py}-W{pw:02d}"
            weeks_to_save = {current_week, prev_week}
            print(f"📅 MODE : Semaines courante+précédente ({prev_week}, {current_week})\n")

    result = build_weekly_from_daily(db, weeks_to_save=weeks_to_save)
    if result.get("daily", 0) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()


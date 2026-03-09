#!/usr/bin/env python3
"""
NIVEAU 2 : CONSTRUCTION DAILY OFFICIEL (SOURCE DE VÉRITÉ)

Responsabilité :
- Agréger toutes les collectes intraday du jour
- Créer UNE ligne par action/jour
- Open = premier prix du jour
- High = prix maximum
- Low = prix minimum  
- Close = dernier prix (clôture)
- Volume = somme des volumes

👉 Cette collection alimente RSI, SMA, ATR, volatilité
👉 Exécuter en fin de journée (après dernière collecte)
"""

import os, sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

def _parse_args():
    parser = argparse.ArgumentParser(description="Construire prices_daily depuis prices_intraday_raw")
    parser.add_argument(
        "--date",
        dest="build_date",
        help="Date à construire au format YYYY-MM-DD (ex: 2026-02-21). Par défaut: aujourd'hui.",
    )
    parser.add_argument(
        "--yesterday",
        action="store_true",
        help="Construire pour hier (utile si tu as oublié de lancer le soir).",
    )
    return parser.parse_args()


def build_daily_for_date(db, build_date: str) -> dict:
    """Construit/MAJ prices_daily pour une date YYYY-MM-DD depuis prices_intraday_raw."""
    print(f"📅 Construction pour : {build_date}\n")

    # ÉTAPE 1: Charger toutes les collectes intraday du jour
    print("[1/4] Chargement collectes intraday...")
    intraday_docs = list(db.prices_intraday_raw.find({
        "date": build_date
    }).sort("datetime", 1))

    print(f"  Collectes intraday trouvées : {len(intraday_docs)}")

    if not intraday_docs:
        print("\n❌ Aucune donnée intraday pour ce jour")
        print("   → Vérifier que collecter_brvm_complet_maintenant.py a été exécuté\n")
        return {"date": build_date, "created": 0, "updated": 0, "symbols": 0, "intraday": 0}

    # ÉTAPE 2: Grouper par symbole
    print("\n[2/4] Groupement par symbole...")
    by_symbol = defaultdict(list)

    for doc in intraday_docs:
        symbol = doc.get("symbol")
        if symbol:
            by_symbol[symbol].append(doc)

    print(f"  Symboles uniques : {len(by_symbol)}")

    # ÉTAPE 3: Calculer OHLC daily pour chaque action
    print("\n[3/4] Calcul OHLC daily...")
    daily_docs = []
    stats = {"created": 0, "updated": 0, "skipped": 0}

    for symbol in sorted(by_symbol.keys()):
        collectes = sorted(by_symbol[symbol], key=lambda x: x.get("datetime", ""))
        if not collectes:
            continue

        first = collectes[0]
        last = collectes[-1]

        open_price = first.get("open") or first.get("close")
        high_price = max((c.get("high") or c.get("close") or 0 for c in collectes), default=0)
        low_price = min(
            (c.get("low") or c.get("close") or 999999 for c in collectes if c.get("low") or c.get("close")),
            default=999999,
        )
        close_price = last.get("close")

        # Volume, valeur et nb_transactions sont des cumulatifs journaliers publiés
        # par la BRVM (total depuis l'ouverture). On prend la dernière collecte
        # (= valeur finale de la journée), pas la somme qui gonflerait par le
        # nombre de collectes (biais ×4–6 constaté sur analyse intraday).
        volume_total = last.get("volume") or 0
        valeur_totale = last.get("valeur") or 0
        nb_tx_total = last.get("nb_transactions") or 0

        precedent = first.get("precedent")
        if precedent and close_price:
            variation_pct = ((close_price - precedent) / precedent) * 100
        else:
            variation_pct = last.get("variation_pct")

        daily_doc = {
            "symbol": symbol,
            "date": build_date,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "precedent": precedent,
            "variation_pct": variation_pct,
            "volume": volume_total,
            "valeur": valeur_totale,
            "nb_transactions": nb_tx_total,
            "nb_collectes_intraday": len(collectes),
            "nom": last.get("nom"),
            "sector": last.get("sector"),
            "secteur_officiel": last.get("secteur_officiel"),
            "capitalisation": last.get("capitalisation"),
            "market_cap": last.get("market_cap"),
            "pe_ratio": last.get("pe_ratio"),
            "dividend_yield": last.get("dividend_yield"),
            "nombre_titres": last.get("nombre_titres"),
            "flottant_pct": last.get("flottant_pct"),
            "data_quality": last.get("data_quality"),
            "first_collect_time": first.get("datetime"),
            "last_collect_time": last.get("datetime"),
            "built_at": datetime.now(),
            "source": "DAILY_BUILDER"
        }
        daily_docs.append(daily_doc)

    print(f"  Documents daily créés : {len(daily_docs)}")

    # ÉTAPE 4: Sauvegarder dans prices_daily
    print("\n[4/4] Sauvegarde dans prices_daily...")

    for doc in daily_docs:
        result = db.prices_daily.update_one(
            {"symbol": doc["symbol"], "date": doc["date"]},
            {"$set": doc},
            upsert=True
        )
        if result.matched_count > 0:
            stats["updated"] += 1
        else:
            stats["created"] += 1

    print(f"  ✅ Créés  : {stats['created']}")
    print(f"  ♻️  Mis à jour : {stats['updated']}")

    print("\n" + "="*80)
    print("RÉSUMÉ CONSTRUCTION DAILY")
    print("="*80)
    print(f"📅 Date             : {build_date}")
    print(f"📊 Collectes intraday : {len(intraday_docs)}")
    print(f"🏢 Actions traitées  : {len(daily_docs)}")
    print(f"✅ Documents daily   : {stats['created'] + stats['updated']}")
    print("\n💡 Ces données alimentent maintenant RSI, SMA, ATR")
    print("💡 Prochaine étape : build_weekly.py (chaque lundi)\n")
    print("="*80 + "\n")

    return {
        "date": build_date,
        "created": stats["created"],
        "updated": stats["updated"],
        "symbols": len(daily_docs),
        "intraday": len(intraday_docs),
    }


def main():
    _, db = get_mongo_db()

    print("\n" + "="*80)
    print("CONSTRUCTION DAILY OFFICIEL (NIVEAU 2)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    args = _parse_args()

    if args.yesterday and args.build_date:
        print("❌ Erreur: utiliser soit --date, soit --yesterday (pas les deux).\n")
        sys.exit(2)

    if args.yesterday:
        build_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif args.build_date:
        try:
            build_date = datetime.strptime(args.build_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Erreur: --date doit être au format YYYY-MM-DD (ex: 2026-02-21).\n")
            sys.exit(2)
    else:
        build_date = datetime.now().strftime("%Y-%m-%d")

    result = build_daily_for_date(db, build_date)
    if result.get("intraday", 0) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()


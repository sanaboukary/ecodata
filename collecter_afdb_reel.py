#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
Collecte AFDB reelle 2010-2026 via World Bank REST API.
- Purge les docs mock (attrs.mock: True)
- Collecte 6 indicateurs x 8 pays UEMOA = 48 series
- Periode: 2010 -> aujourd'hui
- Tolerance zero: aucun fallback mock
"""
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db
from scripts.connectors.afdb import (
    fetch_afdb_all_countries,
    INDICATEUR_WB,
    PAYS_UEMOA,
)

_, db = get_mongo_db()
INDICATEURS = list(INDICATEUR_WB.keys())


def _upsert_observations(observations):
    if not observations:
        return 0
    from pymongo import UpdateOne
    ops = []
    for o in observations:
        filtre = {"source": o["source"], "dataset": o["dataset"],
                  "key": o["key"], "ts": o["ts"]}
        ops.append(UpdateOne(filtre, {"$set": o}, upsert=True))
    result = db.curated_observations.bulk_write(ops, ordered=False)
    return result.upserted_count + result.modified_count


def purger_mock():
    print("=" * 60)
    print("ETAPE 1 - PURGE DONNEES MOCK AFDB")
    print("=" * 60)
    result = db.curated_observations.delete_many({
        "source": "AfDB",
        "attrs.mock": True,
    })
    print(f"  Docs supprimes  : {result.deleted_count}")
    remaining = db.curated_observations.count_documents({"source": "AfDB"})
    print(f"  Docs AfDB restants : {remaining}")
    print()


def collecter_afdb_reel():
    print("=" * 60)
    print("ETAPE 2 - COLLECTE AFDB REELLE (World Bank API)")
    print(f"  Indicateurs : {', '.join(INDICATEURS)}")
    print(f"  Pays        : {', '.join(PAYS_UEMOA)}")
    print("  Periode     : 2010 -> 2026")
    print("=" * 60)

    total_obs = 0
    succes = 0
    echecs = 0

    for ind in INDICATEURS:
        wb_code = INDICATEUR_WB[ind]
        print(f"\n  [{ind}] ({wb_code})")
        try:
            obs = fetch_afdb_all_countries(ind, PAYS_UEMOA, "2010:2026")
            if obs:
                _upsert_observations(obs)
                total_obs += len(obs)
                succes += 1
                pays_counts = {}
                for o in obs:
                    pays = o["attrs"].get("country", "??")
                    pays_counts[pays] = pays_counts.get(pays, 0) + 1
                details = " | ".join(
                    f"{p}={c}" for p, c in sorted(pays_counts.items())
                )
                print(f"    OK - {len(obs)} obs ({details})")
            else:
                echecs += 1
                print("    ECHEC - 0 observations retournees")
        except Exception as e:
            echecs += 1
            print(f"    ERREUR - {str(e)[:60]}")

        time.sleep(0.8)

    return total_obs, succes, echecs


def rapport_final(total_obs, succes, echecs, duree):
    print()
    print("=" * 60)
    print("RAPPORT FINAL")
    print("=" * 60)
    print(f"  Indicateurs collectes : {succes}/{succes+echecs}")
    print(f"  Echecs                : {echecs}")
    print(f"  Observations totales  : {total_obs:,}")
    print(f"  Duree                 : {int(duree//60)}m {int(duree%60)}s")

    print()
    print("  Verification en base :")
    total_afdb = db.curated_observations.count_documents({"source": "AfDB"})
    mock_restants = db.curated_observations.count_documents(
        {"source": "AfDB", "attrs.mock": True}
    )
    print(f"    Docs AfDB total : {total_afdb:,}")
    print(f"    Docs mock       : {mock_restants}  {'<-- OK ZERO MOCK' if mock_restants == 0 else '*** ATTENTION ***'}")

    res = list(db.curated_observations.aggregate([
        {"$match": {"source": "AfDB"}},
        {"$group": {"_id": None, "min_ts": {"$min": "$ts"}, "max_ts": {"$max": "$ts"}}},
    ]))
    if res:
        print(f"    Periode         : {res[0]['min_ts'][:4]} -> {res[0]['max_ts'][:4]}")

    print()
    print("  Detail par indicateur :")
    for ind in INDICATEURS:
        n = db.curated_observations.count_documents(
            {"source": "AfDB", "attrs.indicator_name": ind}
        )
        print(f"    {ind:<18} : {n:>4} obs")

    print()
    if mock_restants == 0 and total_afdb > 0:
        print("  STATUT : DONNEES 100% REELLES")
    elif total_afdb == 0:
        print("  STATUT : ERREUR - aucune donnee collectee")
    else:
        print("  STATUT : ATTENTION - verifier les donnees mock restantes")
    print("=" * 60)


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("COLLECTE AFDB REELLE 2010-2026 - TOLERANCE ZERO MOCK")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    debut = time.time()

    purger_mock()
    total_obs, succes, echecs = collecter_afdb_reel()
    duree = time.time() - debut

    rapport_final(total_obs, succes, echecs, duree)

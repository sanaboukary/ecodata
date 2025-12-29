import os
import sys
from pathlib import Path
import time
import datetime as dt
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    import wbdata
except Exception as e:
    raise SystemExit("wbdata non disponible. Installe: pip install wbdata>=1.0") from e

from packaging import version

if version.parse(getattr(wbdata, "__version__", "0.0")) < version.parse("1.0.0"):
    raise SystemExit(f"wbdata {wbdata.__version__} détecté. Utilise wbdata>=1.0.0 (API date=(start,end)).")

# Assure que le dossier parent (scripts/) est dans le path pour importer _common
PARENT = Path(__file__).resolve().parent.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _common import get_db_from_env


# Paramètres par défaut (surchageables par env)
START_YEAR = int(os.getenv("WB_START_YEAR", "2015"))
END_YEAR = int(os.getenv("WB_END_YEAR", "2024"))
SCOPE = os.getenv("WB_SCOPE", "UEMOA")  # UEMOA ou ALL

START_DATE = dt.datetime(START_YEAR, 1, 1)
END_DATE = dt.datetime(END_YEAR, 12, 31)

UEMOA_CODES = ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"]
COUNTRY_FILTER = UEMOA_CODES if SCOPE.upper() == "UEMOA" else None


INDICATORS: Dict[str, str] = {
    "NY.GDP.MKTP.CD": "PIB_total_USD_courant",
    "NY.GDP.MKTP.KD.ZG": "PIB_croissance_pct",
    "FP.CPI.TOTL.ZG": "Inflation_CPI_annuelle_pct",
    "BN.CAB.XOKA.CD": "Compte_courant_USD",
    "GC.REV.XGRT.GD.ZS": "Recettes_publiques_hors_dons_pctPIB",
    "GC.XPN.TOTL.GD.ZS": "Depenses_totales_pctPIB",
    "GC.NLD.TOTL.GD.ZS": "Solde_budgetaire_net_pctPIB",
    "GC.DOD.TOTL.GD.ZS": "Dette_publique_pctPIB",
    "CM.MKT.LCAP.GD.ZS": "Capitalisation_boursiere_pctPIB",
    "CM.MKT.TRAD.GD.ZS": "Valeur_echanges_actions_pctPIB",
    "FD.AST.PRVT.GD.ZS": "Credit_secteur_prive_pctPIB",
    "GC.TAX.TOTL.GD.ZS": "Recettes_fiscales_pctPIB",
    "GC.NFN.TOTL.GD.ZS": "Investissement_public_net_ANF_pctPIB",
    "GC.XPN.INTP.ZS": "Interets_dette_pct_depenses",
    "GC.XPN.INTP.RV.ZS": "Interets_dette_pct_recettes",
    "GC.XPN.INTP.CN": "Interets_dette_valeur_LCU",
    "NY.GDP.MKTP.CN": "PIB_total_LCU",
    "SP.POP.TOTL": "Population_totale",
}


def _retry(call, max_tries=5, base_sleep=1.2):
    for i in range(1, max_tries + 1):
        try:
            return call()
        except Exception:
            if i == max_tries:
                raise
            time.sleep(base_sleep * (2 ** (i - 1)))


def fetch_dataframe(indicators: Dict[str, str]) -> pd.DataFrame:
    def _call():
        return wbdata.get_dataframe(indicators, country=COUNTRY_FILTER, date=(START_DATE, END_DATE))

    df = _retry(_call)
    df = df.reset_index().rename(columns={"country": "Pays", "date": "Annee"})
    dtcol = pd.to_datetime(df["Annee"], errors="coerce")
    df["Annee"] = dtcol.dt.year.astype("Int64")
    for _, alias in indicators.items():
        if alias in df.columns:
            df[alias] = pd.to_numeric(df[alias], errors="coerce")
    return df


def upsert_worldbank_documents(df_master: pd.DataFrame) -> None:
    client, db = get_db_from_env()
    try:
        # Collection: ext_worldbank_indicators (pays, indicateur, année)
        bulk = []
        value_cols = [c for c in df_master.columns if c not in ("Pays", "Annee")]
        # Optionnel: récupérer mapping code -> nom
        countries = wbdata.get_countries(COUNTRY_FILTER) if COUNTRY_FILTER else wbdata.get_countries()
        code_to_name = {c["id"]: c["name"] for c in countries}

        # Heuristique sur code pays: utiliser code à 3 lettres si présent sinon nom
        # wbdata renvoie le nom dans "Pays"; on tente d'inférer le code si présent dans mapping inverse
        name_to_code = {v: k for k, v in code_to_name.items()}

        for _, row in df_master.iterrows():
            country_name = row["Pays"]
            country_code = name_to_code.get(country_name, country_name)
            year = int(row["Annee"]) if pd.notna(row["Annee"]) else None
            for col in value_cols:
                value = row[col]
                if pd.isna(value):
                    continue
                indicator_alias = col
                # retrouver le code indicateur à partir de l'alias
                indicator_code = None
                for k, alias in INDICATORS.items():
                    if alias == indicator_alias:
                        indicator_code = k
                        break

                doc_id = f"{country_code}:{indicator_code}:{year}"
                bulk.append(
                    {
                        "update_one": {
                            "filter": {"_id": doc_id},
                            "update": {
                                "$set": {
                                    "_id": doc_id,
                                    "country_code": country_code,
                                    "country_name": country_name,
                                    "indicator_code": indicator_code,
                                    "indicator_alias": indicator_alias,
                                    "year": year,
                                    "value": float(value),
                                    "scope": SCOPE,
                                    "period": {"granularity": "year", "start": f"{year}-01-01", "end": f"{year}-12-31"},
                                    "source": "WorldBank/WDI",
                                    "ingested_at": dt.datetime.utcnow(),
                                }
                            },
                            "upsert": True,
                        }
                    }
                )

        if bulk:
            db.ext_worldbank_indicators.bulk_write(bulk, ordered=False)

        # Métadonnées indicateurs
        ind_meta = wbdata.get_indicators(list(INDICATORS.keys()))
        for i in ind_meta:
            db.ext_worldbank_meta.update_one(
                {"type": "indicator", "code": i["id"]},
                {
                    "$set": {
                        "type": "indicator",
                        "code": i["id"],
                        "alias": INDICATORS.get(i["id"]),
                        "name": i.get("name"),
                        "source": i.get("source", {}).get("value"),
                        "topics": [t.get("value") for t in i.get("topics", [])],
                        "updated_at": dt.datetime.utcnow(),
                    }
                },
                upsert=True,
            )
        # Métadonnées pays
        for code, name in code_to_name.items():
            db.ext_worldbank_meta.update_one(
                {"type": "country", "code": code},
                {"$set": {"type": "country", "code": code, "name": name, "updated_at": dt.datetime.utcnow()}},
                upsert=True,
            )
    finally:
        client.close()


if __name__ == "__main__":
    df = fetch_dataframe(INDICATORS)
    base_cols = ["Pays", "Annee"]
    val_cols = [v for v in INDICATORS.values() if v in df.columns]
    df_master = df[base_cols + val_cols].sort_values(["Pays", "Annee"]).reset_index(drop=True)

    upsert_worldbank_documents(df_master)
    print("worldbank: ingestion Mongo OK")



"""
Connecteur AfDB — données réelles via World Bank REST API.
Les indicateurs AfDB (GDP_GROWTH, DEBT_GDP, etc.) sont disponibles via l'API
World Bank qui publie les mêmes séries statistiques pour les pays africains.
Plus de mock : si l'API ne répond pas, on retourne [] et on log l'erreur.
"""
from typing import List, Dict, Any
import requests
import logging
import time

logger = logging.getLogger(__name__)

WB_BASE = "https://api.worldbank.org/v2"
HTTP_TIMEOUT = 30
MAX_RETRIES = 3

# Mapping: indicateur AfDB → indicateur World Bank
INDICATEUR_WB = {
    "GDP_GROWTH":     "NY.GDP.MKTP.KD.ZG",   # Croissance PIB réel (%)
    "DEBT_GDP":       "DT.DOD.DECT.GN.ZS",   # Dette exterieure totale / RNB (%) — meilleure couverture UEMOA
    "FDI_GDP":        "BX.KLT.DINV.WD.GD.ZS",# IDE nets / PIB (%)
    "TRADE_BALANCE":  "NE.RSB.GNFS.ZS",       # Balance commerciale / PIB (%)
    "INFLATION":      "FP.CPI.TOTL.ZG",       # Inflation IPC (%)
    "UNEMPLOYMENT":   "SL.UEM.TOTL.ZS",       # Chômage (% pop active)
}

# Pays UEMOA + Ghana (codes ISO2 BCEAO/AfDB)
PAYS_UEMOA = ["BJ", "BF", "CI", "ML", "NE", "SN", "TG", "GH"]


def _wb_fetch(country: str, wb_indicator: str,
              date_range: str = "2010:2026") -> List[Dict]:
    """Appel direct à l'API World Bank REST avec retry."""
    url = (
        f"{WB_BASE}/country/{country}/indicator/{wb_indicator}"
        f"?format=json&date={date_range}&per_page=500"
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, list) or len(payload) < 2:
                return []
            return payload[1] or []
        except requests.exceptions.RequestException as e:
            logger.warning(f"WB API attempt {attempt}/{MAX_RETRIES} failed for "
                           f"{country}/{wb_indicator}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
    logger.error(f"WB API unreachable for {country}/{wb_indicator} after {MAX_RETRIES} attempts")
    return []


def fetch_afdb_sdmx(dataset: str, key: str, **_kwargs) -> List[Dict[str, Any]]:
    """
    Interface de compatibilité : dataset='AFDB', key='GDP_GROWTH.BJ'
    Retourne des observations au format curated_observations (100% réelles).
    """
    try:
        parts = key.split(".")
        if len(parts) != 2:
            logger.error(f"Format de clé invalide: '{key}' (attendu: INDICATEUR.PAYS)")
            return []
        indicator_name, country = parts[0].upper(), parts[1].upper()
    except Exception as e:
        logger.error(f"Impossible de parser la clé '{key}': {e}")
        return []

    wb_indicator = INDICATEUR_WB.get(indicator_name)
    if not wb_indicator:
        logger.warning(f"Indicateur inconnu '{indicator_name}'. "
                       f"Indicateurs disponibles: {list(INDICATEUR_WB.keys())}")
        return []

    raw = _wb_fetch(country, wb_indicator)
    out: List[Dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        val = entry.get("value")
        date_str = entry.get("date")
        if val is None or date_str is None:
            continue
        try:
            ts = f"{date_str}-01-01T00:00:00Z"
            out.append({
                "source":  "AfDB",
                "dataset": dataset or "AFDB",
                "key":     f"{country}.{indicator_name}",
                "ts":      ts,
                "value":   round(float(val), 6),
                "attrs": {
                    "country":        country,
                    "indicator_name": indicator_name,
                    "indicator_wb":   wb_indicator,
                    "mock":           False,
                },
            })
        except (ValueError, TypeError):
            continue

    logger.info(f"AfDB/{indicator_name}/{country}: {len(out)} observations collectées (source: WB API)")
    return out


def fetch_afdb_all_countries(indicator_name: str,
                              pays: List[str] = None,
                              date_range: str = "2010:2026") -> List[Dict[str, Any]]:
    """
    Collecte un indicateur pour tous les pays UEMOA en un seul appel groupé.
    Utilisation : fetch_afdb_all_countries('GDP_GROWTH')
    """
    pays = pays or PAYS_UEMOA
    wb_indicator = INDICATEUR_WB.get(indicator_name.upper())
    if not wb_indicator:
        logger.error(f"Indicateur inconnu: {indicator_name}")
        return []

    country_param = ";".join(pays)
    raw = _wb_fetch(country_param, wb_indicator, date_range)
    out: List[Dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        val = entry.get("value")
        date_str = entry.get("date")
        country_id = entry.get("countryiso3code") or (
            entry.get("country", {}) or {}
        ).get("id", "??")
        if val is None or date_str is None:
            continue
        try:
            out.append({
                "source":  "AfDB",
                "dataset": "AFDB",
                "key":     f"{country_id}.{indicator_name.upper()}",
                "ts":      f"{date_str}-01-01T00:00:00Z",
                "value":   round(float(val), 6),
                "attrs": {
                    "country":        country_id,
                    "indicator_name": indicator_name.upper(),
                    "indicator_wb":   wb_indicator,
                    "mock":           False,
                },
            })
        except (ValueError, TypeError):
            continue

    logger.info(f"AfDB/{indicator_name} (groupé): {len(out)} observations")
    return out

from typing import List, Dict, Any
import requests, os
from math import ceil
from .._http import get_json
import logging

logger = logging.getLogger(__name__)

IMF_BASE_URL = os.getenv("IMF_BASE_URL","https://dataservices.imf.org/REST/SDMX_JSON.svc").rstrip("/")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT","30"))
USE_MOCK_DATA = os.getenv("USE_MOCK_IMF", "false").lower() == "true"

def fetch_imf_compact(dataset: str, key: str, use_mock: bool = None, retries: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch data from IMF SDMX API
    Args:
        dataset: IMF dataset code (e.g., IFS)
        key: SDMX key (e.g., M.BEN.PCPI_IX for monthly CPI Benin)
        use_mock: Force use of mock data (overrides env var)
    Returns:
        List of observations
    """
    if use_mock is None:
        use_mock = USE_MOCK_DATA
    
    if use_mock:
        logger.info(f"Using mock data for IMF {dataset}/{key}")
        return _get_mock_imf_data(dataset, key)
    
    try:
        url = f"{IMF_BASE_URL}/CompactData/{dataset}/{key}"
        logger.info(f"Fetching IMF data from {url} (retries={retries})")
        data = get_json(url, timeout=HTTP_TIMEOUT, retries=retries)
        series = data.get("CompactData", {}).get("DataSet", {}).get("Series")
        if not series: 
            logger.warning(f"No series found for {dataset}/{key}")
            return []
        if isinstance(series, dict): series = [series]
        out=[]
        for s in series:
            obs = s.get("Obs") or []
            if isinstance(obs, dict): obs=[obs]
            key_full = ".".join([str(v) for v in s.values() if isinstance(v,str)])
            for o in obs:
                t = o.get("@TIME_PERIOD"); v = o.get("@OBS_VALUE")
                if not (t and v): continue
                ts = f"{t}-01-01T00:00:00Z" if len(t)==4 else f"{t}T00:00:00Z"
                out.append({"source":"IMF","dataset":dataset,"key":key_full or key,"ts":ts,"value":float(v),"attrs":{}})
        logger.info(f"Fetched {len(out)} observations from IMF")
        return out
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to IMF API after retries: {e}")
        logger.info("Falling back to mock data")
        return _get_mock_imf_data(dataset, key)
    except Exception as e:
        logger.error(f"Unexpected error fetching IMF data: {e}")
        return []

def _get_mock_imf_data(dataset: str, key: str) -> List[Dict[str, Any]]:
    """Generate mock IMF data for testing"""
    import random
    from datetime import datetime, timedelta
    
    # Parse country from key (e.g., M.BEN.PCPI_IX -> BEN)
    parts = key.split('.')
    country = parts[1] if len(parts) > 1 else "BEN"
    indicator = parts[2] if len(parts) > 2 else "PCPI_IX"
    
    # Generate mock data for last 5 years
    out = []
    base_value = 100.0 if "PCPI" in indicator else 1000.0  # CPI base 100, GDP in millions
    
    for year in range(2020, 2025):
        for month in range(1, 13):
            # Add some random variation
            value = base_value * (1 + random.uniform(-0.05, 0.15))  # -5% to +15% variation
            base_value = value  # Carry forward for next period
            
            ts = f"{year}-{month:02d}-01T00:00:00Z"
            out.append({
                "source": "IMF",
                "dataset": dataset,
                "key": f"{country}.{indicator}",
                "ts": ts,
                "value": round(value, 2),
                "attrs": {"mock": True}
            })
    
    logger.info(f"Generated {len(out)} mock IMF observations for {dataset}/{key}")
    return out

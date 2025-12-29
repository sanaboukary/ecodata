from typing import List, Dict, Any
import requests, os
from .._http import get_json
import logging

logger = logging.getLogger(__name__)

AFDB_BASE_URL = os.getenv("AFDB_BASE_URL","").rstrip("/")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT","30"))
USE_MOCK_DATA = os.getenv("USE_MOCK_AFDB", "false").lower() == "true"

def fetch_afdb_sdmx(dataset: str, key: str, use_mock: bool = None, retries: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch AfDB data (with fallback to mock data)
    Args:
        dataset: Dataset code
        key: Data key
        use_mock: Force use of mock data
    Returns:
        List of observations
    """
    if use_mock is None:
        use_mock = USE_MOCK_DATA
    
    if not AFDB_BASE_URL or use_mock:
        logger.info(f"Using mock data for AfDB {dataset}/{key}")
        return _get_mock_afdb_data(dataset, key)
    
    try:
        url = f"{AFDB_BASE_URL}/CompactData/{dataset}/{key}"
        logger.info(f"Fetching AfDB data from {url} (retries={retries})")
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
                out.append({"source":"AfDB","dataset":dataset,"key":key_full or key,"ts":ts,"value":float(v),"attrs":{}})
        logger.info(f"Fetched {len(out)} observations from AfDB")
        return out
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to AfDB API after retries: {e}")
        logger.info("Falling back to mock data")
        return _get_mock_afdb_data(dataset, key)
    except Exception as e:
        logger.error(f"Unexpected error fetching AfDB data: {e}")
        return []

def _get_mock_afdb_data(dataset: str, key: str) -> List[Dict[str, Any]]:
    """Generate mock AfDB data for testing"""
    import random
    
    # West African countries
    countries = ["BEN", "BFA", "CIV", "GIN", "MLI", "NER", "SEN", "TGO"]
    
    out = []
    for country in countries:
        # Base values depending on indicator
        if "DEBT" in key.upper():
            base_value = random.uniform(2000, 8000)  # Millions USD
        elif "GDP" in key.upper():
            base_value = random.uniform(10000, 50000)  # Millions USD
        elif "INFLATION" in key.upper():
            base_value = random.uniform(1.5, 6.0)  # Percentage
        else:
            base_value = random.uniform(100, 1000)
        
        for year in range(2020, 2025):
            value = base_value * (1 + random.uniform(-0.05, 0.10))  # -5% to +10% variation
            base_value = value  # Carry forward
            
            ts = f"{year}-01-01T00:00:00Z"
            out.append({
                "source": "AfDB",
                "dataset": dataset,
                "key": f"{country}.{key}",
                "ts": ts,
                "value": round(value, 2),
                "attrs": {"country": country, "mock": True}
            })
    
    logger.info(f"Generated {len(out)} mock AfDB observations for {dataset}/{key}")
    return out

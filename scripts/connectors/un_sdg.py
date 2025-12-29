from typing import List, Dict, Any, Optional
import requests, os
from .._http import get_json
import logging

logger = logging.getLogger(__name__)

UN_SDG_BASE_URL = os.getenv("UN_SDG_BASE_URL","https://unstats.un.org/SDGAPI/v1/sdg").rstrip("/")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT","30"))
USE_MOCK_DATA = os.getenv("USE_MOCK_UN", "false").lower() == "true"

def fetch_un_sdg(series: str, area: Optional[str] = None, time: Optional[str] = None, page_size: int = 10000, use_mock: bool = None, retries: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch UN SDG data
    Args:
        series: Series code (e.g., SL_TLF_UEM for unemployment)
        area: Area code (e.g., 204 for Benin)
        time: Time period filter
        page_size: Max results per page
        use_mock: Force use of mock data
    Returns:
        List of observations
    """
    if use_mock is None:
        use_mock = USE_MOCK_DATA
    
    if use_mock:
        logger.info(f"Using mock data for UN SDG {series}")
        return _get_mock_un_data(series, area, time)
    
    try:
        # UN SDG API paginates; if multiple areas provided as comma-separated, fetch per area
        areas = [a.strip() for a in area.split(',')] if area else [None]
        url = f"{UN_SDG_BASE_URL}/Series/Data"
        out: List[Dict[str, Any]] = []
        for area_item in areas:
            page = 1
            while True:
                params = {"seriesCode": series, "pageSize": page_size, "page": page}
                if area_item: params["areaCode"] = area_item
                if time: params["timePeriod"] = time
                logger.info(f"Fetching UN SDG data: {url} page={page} params={params}")
                # Désactiver vérif SSL pour Windows (CRYPT_E_NO_REVOCATION_CHECK)
                data = get_json(url, params=params, timeout=HTTP_TIMEOUT, retries=retries, verify_ssl=False)
                rows = data.get("data", [])
                for row in rows:
                    try:
                        # API retourne 'timePeriodStart' (year as float), pas 'timePeriod'
                        time_period = row.get("timePeriodStart")
                        if time_period is not None:
                            time_period = str(int(time_period))  # 2002.0 -> "2002"
                        val = row.get("value");
                        geo = row.get("geoAreaCode") or row.get("geoAreaName") or area_item or "UNKNOWN"
                        if val is None or time_period is None:
                            continue
                        ts = f"{time_period}-01-01T00:00:00Z" if len(time_period)==4 else f"{time_period}T00:00:00Z"
                        out.append({
                            "source": "UN_SDG",
                            "dataset": series,
                            "key": f"{geo}.{series}",
                            "ts": ts,
                            "value": float(val),
                            "attrs": {"geo": geo}
                        })
                    except Exception:
                        continue
                # pagination info
                page_info = data.get("page") or {}
                current = page_info.get("currentPage") or page
                total_pages = page_info.get("totalPages") or 1
                if current >= total_pages or not rows:
                    break
                page += 1
        logger.info(f"Fetched {len(out)} observations from UN SDG")
        return out
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to UN API after retries: {e}")
        logger.info("Falling back to mock data")
        return _get_mock_un_data(series, area, time)
    except Exception as e:
        logger.error(f"Unexpected error fetching UN SDG data: {e}")
        return []

def _get_mock_un_data(series: str, area: Optional[str] = None, time: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate mock UN SDG data for testing"""
    import random
    
    # Country codes for West Africa
    countries = {
        "204": "BEN",  # Benin
        "854": "BFA",  # Burkina Faso
        "384": "CIV",  # Côte d'Ivoire
        "624": "GIN",  # Guinea
        "466": "MLI",  # Mali
        "562": "NER",  # Niger
        "686": "SEN",  # Senegal
        "768": "TGO"   # Togo
    }
    
    # Parse area codes
    if area:
        area_codes = [a.strip() for a in area.split(',')]
    else:
        area_codes = list(countries.keys())
    
    out = []
    # Generate data for each country and year
    for area_code in area_codes:
        country = countries.get(area_code, area_code)
        base_value = random.uniform(5.0, 15.0)  # Base unemployment rate 5-15%
        
        for year in range(2020, 2025):
            value = base_value * (1 + random.uniform(-0.1, 0.1))  # ±10% variation
            ts = f"{year}-01-01T00:00:00Z"
            out.append({
                "source": "UN_SDG",
                "dataset": series,
                "key": f"{country}.{series}",
                "ts": ts,
                "value": round(value, 2),
                "attrs": {"geo": area_code, "mock": True}
            })
    
    logger.info(f"Generated {len(out)} mock UN SDG observations for {series}")
    return out

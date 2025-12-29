from typing import List, Dict, Any, Optional
import requests, os

WB_BASE_URL = os.getenv("WB_BASE_URL","https://api.worldbank.org/v2").rstrip("/")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT","30"))

def _wb_get(path: str, params: Dict[str, Any]) -> Any:
    url = f"{WB_BASE_URL}/{path.lstrip('/')}"
    r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_worldbank_indicator(indicator: str, date: Optional[str] = None, country: str = "all", per_page: int = 20000) -> List[Dict[str, Any]]:
    params = {"format": "json", "per_page": per_page}
    if date:
        params["date"] = date
    data = _wb_get(f"country/{country}/indicator/{indicator}", params=params)
    if not isinstance(data, list) or len(data) < 2:
        return []
    rows = data[1] or []
    out=[]
    for row in rows:
        try:
            country_id = row["countryiso3code"] or row["country"]["id"]
            year = row["date"]; val = row["value"]
            if val is None: continue
            out.append({
                "source":"WorldBank","dataset":indicator,"key":f"{country_id}.{indicator}",
                "ts": f"{year}-01-01T00:00:00Z",
                "value": float(val),
                "attrs": {"country": country_id, "indicator": indicator}
            })
        except Exception:
            continue
    return out

import time
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def get_json(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    retries: int = 2,
    backoff: float = 0.75,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    HTTP GET with small, exponential backoff retry returning JSON.

    Args:
        url: Full URL to request.
        params: Optional query params.
        timeout: Per-request timeout in seconds.
        retries: Number of retry attempts on transient failures.
        backoff: Base backoff seconds multiplied exponentially per attempt.
        verify_ssl: Verify SSL certificates (set False for Windows cert issues).

    Raises:
        requests.RequestException if all attempts fail.
        ValueError if response is not JSON parseable.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout, verify=verify_ssl)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_exc = e
            # Retry on network/server errors; break early on 4xx except 429
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            should_retry = status in (None, 500, 502, 503, 504, 429)
            if attempt < retries and should_retry:
                sleep_s = backoff * (2 ** attempt)
                logger.warning(f"GET {url} failed (attempt {attempt+1}/{retries+1}): {e}. Retrying in {sleep_s:.2f}s...")
                time.sleep(sleep_s)
                continue
            break
        except ValueError as e:
            # JSON decode error
            last_exc = e
            break
    assert last_exc is not None
    raise last_exc

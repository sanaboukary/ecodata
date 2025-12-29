# Bridge between Django and scripts package
from scripts.pipeline import run_ingestion

def run(source: str, params: dict) -> int:
    kw = dict(params)
    kw.pop("source", None)
    return run_ingestion(source, **kw)

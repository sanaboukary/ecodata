from . import adapters

def run_ingestion_adapter(source: str, params: dict) -> int:
    return adapters.run(source, params)

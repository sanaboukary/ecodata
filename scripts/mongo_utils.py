from pymongo import MongoClient, ASCENDING
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_db(uri, name):
    client = MongoClient(uri)
    return client[name]

def write_raw(db, source, payload):
    col = db.raw_events
    col.create_index([("source", ASCENDING), ("fetched_at", ASCENDING)])
    col.insert_one({"source": source, "fetched_at": datetime.utcnow(), "payload": payload})

def upsert_observations(db, obs):
    col = db.curated_observations
    col.create_index([("source", ASCENDING), ("dataset", ASCENDING), ("key", ASCENDING), ("ts", ASCENDING)], unique=True)
    for r in obs:
        q = {"source": r["source"], "dataset": r["dataset"], "key": r["key"], "ts": r["ts"]}
        col.update_one(q, {"$set": r}, upsert=True)

def log_ingestion_run(db, source: str, status: str, obs_count: int = 0, duration_sec: float = 0.0, error_msg: str = None, params: dict = None):
    """
    Enregistre un run d'ingestion dans la collection ingestion_runs.
    
    Args:
        db: Instance MongoDB database
        source: Nom de la source (BRVM, IMF, etc.)
        status: 'success' ou 'error'
        obs_count: Nombre d'observations ingérées
        duration_sec: Durée en secondes
        error_msg: Message d'erreur si status='error'
        params: Paramètres utilisés (dataset, key, etc.)
    """
    col = db.ingestion_runs
    col.create_index([("source", ASCENDING), ("started_at", ASCENDING)])
    
    doc = {
        "source": source,
        "status": status,
        "obs_count": obs_count,
        "duration_sec": round(duration_sec, 2),
        "started_at": datetime.utcnow(),
        "params": params or {},
    }
    if error_msg:
        doc["error_msg"] = error_msg
    
    col.insert_one(doc)
    logger.info(f"Logged ingestion run: {source} - {status} - {obs_count} obs - {duration_sec:.2f}s")

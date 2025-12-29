from typing import List, Dict
import time
import logging
from .settings import MONGO_URI, MONGO_DB
from .mongo_utils import get_db, write_raw, upsert_observations, log_ingestion_run
from .connectors.brvm import fetch_brvm
from .connectors.worldbank import fetch_worldbank_indicator
from .connectors.imf import fetch_imf_compact
from .connectors.un_sdg import fetch_un_sdg
from .connectors.afdb import fetch_afdb_sdmx

logger = logging.getLogger(__name__)

def normalize_brvm(records: List[Dict]) -> List[Dict]:
    """Normalise les enregistrements BRVM vers le schéma curated avec métriques d'investissement"""
    out = []
    for r in records:
        # Extraire toutes les métriques d'investissement
        attrs = {
            # Prix de base
            "open": r["open"], 
            "high": r["high"], 
            "low": r["low"], 
            "volume": r["volume"],
            "name": r.get("name", r["symbol"]),
            "sector": r.get("sector", "Unknown"),
            "country": r.get("country", "Unknown"),
            
            # Performance & Tendances
            "day_change": r.get("day_change", 0),
            "day_change_pct": r.get("day_change_pct", 0),
            "week_change_pct": r.get("week_change_pct", 0),
            "month_change_pct": r.get("month_change_pct", 0),
            "ytd_change_pct": r.get("ytd_change_pct", 0),
            
            # Valorisation
            "market_cap": r.get("market_cap", 0),
            "shares_outstanding": r.get("shares_outstanding", 0),
            "pe_ratio": r.get("pe_ratio", 0),
            "pb_ratio": r.get("pb_ratio", 0),
            "eps": r.get("eps", 0),
            
            # Dividendes
            "dividend_yield": r.get("dividend_yield", 0),
            "dividend_per_share": r.get("dividend_per_share", 0),
            "payout_ratio": r.get("payout_ratio", 0),
            
            # Liquidité & Volume
            "avg_volume_30d": r.get("avg_volume_30d", 0),
            "turnover_rate": r.get("turnover_rate", 0),
            
            # Analyse Technique
            "sma_20": r.get("sma_20", 0),
            "sma_50": r.get("sma_50", 0),
            "rsi": r.get("rsi", 50),
            "beta": r.get("beta", 1.0),
            "support_level": r.get("support_level", 0),
            "resistance_level": r.get("resistance_level", 0),
            
            # Santé Financière
            "roe": r.get("roe", 0),
            "roa": r.get("roa", 0),
            "debt_to_equity": r.get("debt_to_equity", 0),
            "current_ratio": r.get("current_ratio", 0),
            
            # Recommandations
            "recommendation": r.get("recommendation", "Hold"),
            "consensus_score": r.get("consensus_score", 3),
            "target_price": r.get("target_price", 0),
            "price_to_target_pct": r.get("price_to_target_pct", 0),
            
            # Scores de Qualité
            "liquidity_score": r.get("liquidity_score", 5),
            "growth_score": r.get("growth_score", 5),
            "dividend_score": r.get("dividend_score", 5),
            
            # Comparaisons Sectorielles
            "sector_avg_pe": r.get("sector_avg_pe", 0),
            "sector_performance": r.get("sector_performance", 0)
        }
        
        out.append({
            "source": "BRVM", 
            "dataset": "QUOTES", 
            "key": r["symbol"],
            "ts": r["ts"], 
            "value": r["close"],  # Prix de clôture comme valeur principale
            "attrs": attrs
        })
    return out

def run_ingestion(source: str, **kwargs) -> int:
    db = get_db(MONGO_URI, MONGO_DB)
    start = time.time()
    obs_count = 0
    status = "success"
    error_msg = None
    
    try:
        if source == "brvm":
            recs = fetch_brvm()
            write_raw(db, "BRVM", recs)
            obs = normalize_brvm(recs)
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "brvm_publications":
            from .connectors.brvm_publications import fetch_brvm_publications
            obs = fetch_brvm_publications()
            write_raw(db, "BRVM_PUBLICATION", {"rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "brvm_fundamentals":
            from .connectors.brvm_fundamentals import collect_brvm_fundamentals
            obs = collect_brvm_fundamentals()
            write_raw(db, "BRVM_FUNDAMENTALS", {"rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "worldbank":
            obs = fetch_worldbank_indicator(kwargs.get("indicator"), kwargs.get("date"), kwargs.get("country","all"))
            write_raw(db, "WorldBank", {"params": kwargs, "rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "imf":
            obs = fetch_imf_compact(kwargs.get("dataset"), kwargs.get("key"))
            write_raw(db, "IMF", {"params": kwargs, "rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "un":
            obs = fetch_un_sdg(kwargs.get("series"), kwargs.get("area"), kwargs.get("time"))
            write_raw(db, "UN_SDG", {"params": kwargs, "rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        elif source == "afdb":
            obs = fetch_afdb_sdmx(kwargs.get("dataset"), kwargs.get("key"))
            write_raw(db, "AfDB", {"params": kwargs, "rows": len(obs)})
            upsert_observations(db, obs)
            obs_count = len(obs)
        else:
            raise ValueError(f"Unknown source: {source}")
    except Exception as e:
        status = "error"
        error_msg = str(e)
        logger.error(f"Ingestion failed for {source}: {e}", exc_info=True)
        raise
    finally:
        duration = time.time() - start
        log_ingestion_run(db, source, status, obs_count, duration, error_msg, kwargs)
    
    return obs_count

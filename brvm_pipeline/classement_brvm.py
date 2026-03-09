import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from plateforme_centralisation.mongo import get_mongo_db
from brvm_pipeline.scoring_objectif import score_par_objectif
from brvm_pipeline.config_objectifs import OBJECTIFS

db = get_mongo_db()
decisions = db.decisions_brvm
classements = db.classements_brvm

classements.delete_many({})

for objectif in OBJECTIFS:
    rows = []
    for d in decisions.find({"signal": {"$ne": "SELL"}}):
        score = score_par_objectif(d.get("features", {}), objectif)
        rows.append({
            "symbol": d["symbol"],
            "objectif": objectif,
            "score": score,
            "signal": d["signal"],
            "horizon": d["horizon"]
        })
    rows = sorted(rows, key=lambda x: x["score"], reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        classements.insert_one(row)

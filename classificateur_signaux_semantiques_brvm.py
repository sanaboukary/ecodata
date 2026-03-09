#!/usr/bin/env python3
"""
🎯 CLASSIFICATEUR DE SIGNAUX – BRVM
==================================
Transformation des scores sémantiques en signaux BUY / HOLD / SELL
par horizon :
- Court terme (CT)
- Moyen terme (MT)
- Long terme (LT)

Méthode : règles expertes BRVM (prudentes et auditables)
"""

import os
import sys
from datetime import datetime
from collections import defaultdict

# -------------------------------
# Django & MongoDB
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# ===============================
# 🔢 SEUILS DE DÉCISION BRVM
# ===============================
THRESHOLDS = {
    "CT": {"BUY": 20, "SELL": -10},
    "MT": {"BUY": 30, "SELL": -15},
    "LT": {"BUY": 40, "SELL": -20},
}

def classify(score: float, horizon: str) -> str:
    """Retourne BUY / HOLD / SELL selon score et horizon"""
    if score >= THRESHOLDS[horizon]["BUY"]:
        return "BUY"
    if score <= THRESHOLDS[horizon]["SELL"]:
        return "SELL"
    return "HOLD"

# ===============================
# 🚦 CLASSIFICATION GLOBALE
# ===============================
def classify_all_actions():
    _, db = get_mongo_db()

    print("\n=== CLASSIFICATION DES SIGNAUX SÉMANTIQUES BRVM ===\n")

    docs = list(db.curated_observations.find({
        "source": "BRVM_PUBLICATION",
        "attrs.semantic_score_short": {"$exists": True},
        "attrs.emetteur": {"$exists": True}
    }))

    if not docs:
        print("❌ Aucune donnée sémantique disponible")
        return

    # Agrégation par action
    agg = defaultdict(lambda: {
        "CT": 0.0,
        "MT": 0.0,
        "LT": 0.0,
        "publications": 0
    })

    for d in docs:
        em = d["attrs"]["emetteur"]
        agg[em]["CT"] += d["attrs"].get("semantic_score_short", 0)
        agg[em]["MT"] += d["attrs"].get("semantic_score_medium", 0)
        agg[em]["LT"] += d["attrs"].get("semantic_score_long", 0)
        agg[em]["publications"] += 1

    # Classification finale
    results = []

    for emetteur, scores in agg.items():
        ct = scores["CT"]
        mt = scores["MT"]
        lt = scores["LT"]

        signal_ct = classify(ct, "CT")
        signal_mt = classify(mt, "MT")
        signal_lt = classify(lt, "LT")

        results.append({
            "emetteur": emetteur,
            "CT": ct,
            "MT": mt,
            "LT": lt,
            "signal_CT": signal_ct,
            "signal_MT": signal_mt,
            "signal_LT": signal_lt,
            "publications": scores["publications"]
        })

        # Sauvegarde en base
        db.curated_observations.update_one(
            {
                "source": "BRVM_SIGNAL_SEMANTIQUE",
                "key": emetteur
            },
            {
                "$set": {
                    "source": "BRVM_SIGNAL_SEMANTIQUE",
                    "key": emetteur,
                    "ts": datetime.now().strftime("%Y-%m-%d"),
                    "value": 1,
                    "attrs": {
                        "score_CT": ct,
                        "score_MT": mt,
                        "score_LT": lt,
                        "signal_CT": signal_ct,
                        "signal_MT": signal_mt,
                        "signal_LT": signal_lt,
                        "publications": scores["publications"],
                        "method": "RULE_BASED_BRVM",
                        "generated_at": datetime.now().isoformat()
                    }
                }
            },
            upsert=True
        )

    # ===============================
    # 📊 AFFICHAGE
    # ===============================
    for r in sorted(results, key=lambda x: x["LT"], reverse=True):
        print(f"▶ {r['emetteur']}")
        print(f"   Publications : {r['publications']}")
        print(f"   CT : {r['CT']:.1f} → {r['signal_CT']}")
        print(f"   MT : {r['MT']:.1f} → {r['signal_MT']}")
        print(f"   LT : {r['LT']:.1f} → {r['signal_LT']}")
        print("-" * 55)

    print("\n✅ Classification terminée\n")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    classify_all_actions()

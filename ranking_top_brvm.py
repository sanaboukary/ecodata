#!/usr/bin/env python3
"""
🏆 RANKING TOP OPPORTUNITÉS BRVM
================================
Classement des meilleures actions BRVM
par horizon :
- Court terme (CT)
- Moyen terme (MT)
- Long terme (LT)

Source : BRVM_SIGNAL_FINAL
"""

import os
import sys
from datetime import datetime

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
# ⚖️ PONDÉRATIONS HORIZONS
# ===============================
WEIGHTS = {
    "CT": 1.2,
    "MT": 1.0,
    "LT": 0.9
}

def rank_top_actions(top_n=10):
    _, db = get_mongo_db()

    print("\n🏆 TOP OPPORTUNITÉS BRVM")
    print("=" * 70)
    print(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    docs = list(db.curated_observations.find({
        "source": "BRVM_SIGNAL_FINAL",
        "attrs.score_final": {"$gt": 0}
    }))

    if not docs:
        print("❌ Aucun signal final disponible")
        return

    rankings = {
        "CT": [],
        "MT": [],
        "LT": []
    }

    for d in docs:
        action = d["key"]
        score = d["attrs"]["score_final"]
        signal = d["attrs"]["signal_final"]

        if signal == "SELL":
            continue

        rankings["CT"].append((action, score * WEIGHTS["CT"], signal))
        rankings["MT"].append((action, score * WEIGHTS["MT"], signal))
        rankings["LT"].append((action, score * WEIGHTS["LT"], signal))

    # ===============================
    # 📊 AFFICHAGE
    # ===============================
    for horizon in ["CT", "MT", "LT"]:
        print(f"\n=== TOP {top_n} – {horizon} ===\n")
        ranked = sorted(rankings[horizon], key=lambda x: x[1], reverse=True)[:top_n]

        if not ranked:
            print("Aucune opportunité détectée")
            continue

        for i, (action, score, signal) in enumerate(ranked, 1):
            print(
                f"{i:>2}. {action:<8} | "
                f"Score: {score:>6.1f} | "
                f"Signal: {signal}"
            )

    print("\n✅ Classement terminé\n")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    rank_top_actions(top_n=10)

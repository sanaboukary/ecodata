#!/usr/bin/env python3
"""
🧠 FUSION DES SIGNAUX – BRVM
============================
Fusion experte :
- Sémantique (fondamental)
- Technique (timing)
- Corrélation (risque)

Sortie : BUY / HOLD / SELL final
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
# 🧮 UTILITAIRES
# ===============================
def normalize(score, min_val=0, max_val=100):
    return max(min(score, max_val), min_val)


def signal_to_score(signal):
    return {"BUY": 100, "HOLD": 50, "SELL": 0}.get(signal, 50)

# ===============================
# 🚦 FUSION MÉTIER
# ===============================
def fusion_brvm():
    _, db = get_mongo_db()

    print("\n=== FUSION SÉMANTIQUE + TECHNIQUE + CORRÉLATION (BRVM) ===\n")

    actions = db.curated_observations.distinct(
        "key", {"source": "BRVM_SIGNAL_SEMANTIQUE"}
    )

    if not actions:
        print("❌ Aucun signal sémantique trouvé")
        return

    for action in actions:

        # ===============================
        # 1️⃣ SIGNAL SÉMANTIQUE
        # ===============================
        sem = db.curated_observations.find_one({
            "source": "BRVM_SIGNAL_SEMANTIQUE",
            "key": action
        })

        if not sem:
            continue

        score_sem = max(
            sem["attrs"].get("score_CT", 0),
            sem["attrs"].get("score_MT", 0),
            sem["attrs"].get("score_LT", 0),
        )

        score_sem = normalize(score_sem)

        # ===============================
        # 2️⃣ SIGNAL TECHNIQUE
        # ===============================
        tech = db.curated_observations.find_one({
            "source": "BRVM_TECH_SIGNAL",
            "key": action
        })

        if not tech:
            signal_tech = "HOLD"
        else:
            signal_tech = tech["attrs"].get("signal", "HOLD")

        # 🔴 Blocage technique
        if signal_tech == "SELL":
            final_signal = "SELL"
            final_score = 0
        else:
            score_tech = signal_to_score(signal_tech)

            # ===============================
            # 3️⃣ CORRÉLATION (PÉNALITÉ)
            # ===============================
            corr = db.curated_observations.find_one({
                "source": "BRVM_CORRELATION",
                "key": action
            })

            avg_corr = corr["attrs"].get("avg_correlation", 0) if corr else 0

            penalty = 0
            if avg_corr > 0.75:
                penalty = 20
            elif avg_corr > 0.60:
                penalty = 10

            # ===============================
            # 4️⃣ SCORE FINAL
            # ===============================
            final_score = (
                0.50 * score_sem +
                0.35 * score_tech -
                penalty
            )

            final_score = round(normalize(final_score), 1)

            if final_score >= 70:
                final_signal = "BUY"
            elif final_score >= 45:
                final_signal = "HOLD"
            else:
                final_signal = "SELL"

        # ===============================
        # 💾 SAUVEGARDE
        # ===============================
        db.curated_observations.update_one(
            {
                "source": "BRVM_SIGNAL_FINAL",
                "key": action
            },
            {
                "$set": {
                    "source": "BRVM_SIGNAL_FINAL",
                    "key": action,
                    "ts": datetime.now().strftime("%Y-%m-%d"),
                    "value": final_score,
                    "attrs": {
                        "score_final": final_score,
                        "signal_final": final_signal,
                        "semantic_score": score_sem,
                        "technical_signal": signal_tech,
                        "avg_correlation": avg_corr,
                        "method": "SEM+TECH+CORR_BRVM",
                        "generated_at": datetime.now().isoformat()
                    }
                }
            },
            upsert=True
        )

        # ===============================
        # 📊 AFFICHAGE
        # ===============================
        print(f"▶ {action}")
        print(f"   Sémantique : {score_sem}")
        print(f"   Technique  : {signal_tech}")
        print(f"   Corrélation: {avg_corr}")
        print(f"   ➜ SCORE FINAL : {final_score}")
        print(f"   ➜ SIGNAL FINAL: {final_signal}")
        print("-" * 60)

    print("\n✅ Fusion terminée\n")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    fusion_brvm()

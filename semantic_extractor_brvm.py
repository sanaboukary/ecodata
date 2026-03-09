#!/usr/bin/env python3
"""
🧠 EXTRACTION SÉMANTIQUE FINANCIÈRE – BRVM
========================================
Analyse experte + écriture en base MongoDB
"""

import os
import sys
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# ===============================
# RÈGLES SÉMANTIQUES
# ===============================
SEMANTIC_RULES = {
    "RESULTATS_HAUSSE": {
        "patterns": [
            r"bénéfice.*hausse", r"résultat.*progresse",
            r"chiffre d.?affaires.*hausse", r"croissance",
            r"performance record"
        ],
        "score": {"short": 25, "medium": 30, "long": 20},
        "risk": "LOW"
    },
    "RESULTATS_BAISSE": {
        "patterns": [
            r"bénéfice.*baisse", r"résultat.*recul",
            r"perte", r"dégradation"
        ],
        "score": {"short": -30, "medium": -25, "long": -15},
        "risk": "HIGH"
    },
    "DIVIDENDE": {
        "patterns": [r"dividende", r"distribution", r"coupon"],
        "score": {"short": 20, "medium": 25, "long": 30},
        "risk": "LOW"
    },
    "RISQUE": {
        "patterns": [r"risque", r"incertitude", r"difficultés", r"endettement"],
        "score": {"short": -20, "medium": -30, "long": -20},
        "risk": "HIGH"
    }
}

def analyze_text(text: str):
    scores = {"short": 0, "medium": 0, "long": 0}
    tags = []
    risks = []

    text = text.lower()

    for tag, rule in SEMANTIC_RULES.items():
        for pattern in rule["patterns"]:
            if re.search(pattern, text):
                tags.append(tag)
                scores["short"] += rule["score"]["short"]
                scores["medium"] += rule["score"]["medium"]
                scores["long"] += rule["score"]["long"]
                risks.append(rule["risk"])
                break

    return scores, tags, ("HIGH" if "HIGH" in risks else "LOW")

def main():
    _, db = get_mongo_db()

    print("\n=== EXTRACTION SÉMANTIQUE BRVM ===\n")

    docs = list(db.curated_observations.find({
        "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}
    }))

    if not docs:
        print("❌ Aucune publication trouvée")
        return

    updated = 0

    for doc in docs:
        attrs = doc.get("attrs", {})
        text = " ".join([
            attrs.get("titre", ""),
            attrs.get("description", "")
        ])

        if not text.strip():
            continue

        scores, tags, risk = analyze_text(text)

        db.curated_observations.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "attrs.semantic_score_short": scores["short"],
                "attrs.semantic_score_medium": scores["medium"],
                "attrs.semantic_score_long": scores["long"],
                "attrs.semantic_tags": tags,
                "attrs.semantic_risk": risk,
                "attrs.semantic_analyzed_at": datetime.now().isoformat()
            }}
        )

        updated += 1

    print(f"✅ {updated} publications enrichies sémantiquement\n")


if __name__ == "__main__":
    main()

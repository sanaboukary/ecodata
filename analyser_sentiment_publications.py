#!/usr/bin/env python3
"""
🧠 EXTRACTION SÉMANTIQUE EXPERTE – BRVM (V2)
===========================================

Objectif :
- Lire publications longues (BRVM, RichBourse, rapports, AG)
- Extraire le signal financier exploitable
- Produire des scores par horizon :
  SEMAINE / MOIS / TRIMESTRE / ANNUEL
- Préparer directement la décision d’investissement
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# =====================================================
# DJANGO / MONGODB
# =====================================================
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


# =====================================================
# 🔎 RÈGLES SÉMANTIQUES EXPERTES
# =====================================================

SEMANTIC_RULES = {

    # ---------- PERFORMANCE FINANCIÈRE ----------
    "RESULTATS_HAUSSE": {
        "patterns": [
            r"résultat.*hausse", r"bénéfice.*hausse",
            r"croissance du chiffre d.?affaires",
            r"performance record", r"résultat positif"
        ],
        "scores": {"SEMAINE": 5, "MOIS": 10, "TRIMESTRE": 20, "ANNUEL": 15},
        "risk": "LOW"
    },

    "RESULTATS_BAISSE": {
        "patterns": [
            r"résultat.*baisse", r"perte nette",
            r"dégradation des résultats", r"résultat négatif"
        ],
        "scores": {"SEMAINE": -20, "MOIS": -15, "TRIMESTRE": -10, "ANNUEL": -5},
        "risk": "HIGH"
    },

    # ---------- DIVIDENDES ----------
    "DIVIDENDE": {
        "patterns": [
            r"dividende", r"distribution de dividende",
            r"détachement du dividende", r"coupon"
        ],
        "scores": {"SEMAINE": 0, "MOIS": 10, "TRIMESTRE": 20, "ANNUEL": 40},
        "risk": "LOW"
    },

    # ---------- RISQUES ----------
    "SUSPENSION": {
        "patterns": [r"suspension", r"reprise de cotation"],
        "scores": {"SEMAINE": -80, "MOIS": -60, "TRIMESTRE": -40, "ANNUEL": -20},
        "risk": "EXTREME"
    },

    "RISQUE_FINANCIER": {
        "patterns": [
            r"endettement élevé", r"tension financière",
            r"incertitude", r"difficultés financières"
        ],
        "scores": {"SEMAINE": -20, "MOIS": -20, "TRIMESTRE": -15, "ANNUEL": -10},
        "risk": "HIGH"
    },

    # ---------- GOUVERNANCE ----------
    "GOUVERNANCE": {
        "patterns": [
            r"nomination", r"démission",
            r"changement de direction", r"nouveau directeur"
        ],
        "scores": {"SEMAINE": 0, "MOIS": 5, "TRIMESTRE": 10, "ANNUEL": 10},
        "risk": "MEDIUM"
    }
}


# =====================================================
# 🧠 ANALYSEUR
# =====================================================
class SemanticAnalyzerBRVMV2:

    def __init__(self):
        _, self.db = get_mongo_db()

    # -------------------------------------------------
    # Pondération temporelle
    # -------------------------------------------------
    def time_weight(self, ts: str) -> float:
        days = (datetime.now() - datetime.fromisoformat(ts)).days
        if days <= 7:
            return 1.2
        elif days <= 30:
            return 1.0
        elif days <= 90:
            return 0.7
        else:
            return 0.4

    # -------------------------------------------------
    # Analyse d'un texte
    # -------------------------------------------------
    def analyze_text(self, text: str, ts: str) -> Dict:
        t = text.lower()

        scores = {
            "SEMAINE": 0,
            "MOIS": 0,
            "TRIMESTRE": 0,
            "ANNUEL": 0
        }

        reasons = {
            "SEMAINE": [],
            "MOIS": [],
            "TRIMESTRE": [],
            "ANNUEL": []
        }

        risks_detected = set()

        # --- Application des règles ---
        for rule_name, rule in SEMANTIC_RULES.items():
            for pattern in rule["patterns"]:
                if re.search(pattern, t):
                    for horizon, val in rule["scores"].items():
                        scores[horizon] += val
                        if val != 0:
                            reasons[horizon].append(rule_name)
                    risks_detected.add(rule["risk"])
                    break

        # --- Lecture experte : silence financier ---
        if "états financiers" in t and not any(
            k in t for k in ["chiffre d'affaires", "résultat", "bénéfice", "perte"]
        ):
            for h in scores:
                scores[h] -= 10
                reasons[h].append("Silence sur chiffres clés")

        # --- Pondération temporelle ---
        weight = self.time_weight(ts)
        for h in scores:
            scores[h] = round(scores[h] * weight, 2)
            scores[h] = max(-100, min(100, scores[h]))

        return {
            "scores": scores,
            "reasons": reasons,
            "risks": list(risks_detected)
        }

    # -------------------------------------------------
    # Analyse globale des publications
    # -------------------------------------------------
    def analyze_publications(self, days_back: int = 90):
        print("=" * 90)
        print("🧠 EXTRACTION SÉMANTIQUE BRVM – V2 (MULTI-HORIZON)")
        print("=" * 90)

        date_limit = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        pubs = list(self.db.curated_observations.find({
            "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]},
            "ts": {"$gte": date_limit}
        }))

        print(f"{len(pubs)} publications analysées (depuis {date_limit})\n")

        for pub in pubs:
            # Utiliser le texte intégral si disponible, sinon fallback sur description
            attrs = pub.get('attrs', {})
            text = attrs.get('full_text') or attrs.get('description', '') or pub.get('key', '')
            ts = pub.get("ts")

            result = self.analyze_text(text, ts)

            self.db.curated_observations.update_one(
                {"_id": pub["_id"]},
                {"$set": {
                    "attrs.semantic_v2": {
                        "scores": result["scores"],
                        "reasons": result["reasons"],
                        "risks": result["risks"],
                        "analyzed_at": datetime.now().isoformat()
                    }
                }}
            )

        print("✅ Extraction sémantique V2 terminée.")
        print("➡️ Données prêtes pour agrégation par action.")


# =====================================================
# MAIN
# =====================================================
def main():
    analyzer = SemanticAnalyzerBRVMV2()
    analyzer.analyze_publications(days_back=120)

if __name__ == "__main__":
    main()

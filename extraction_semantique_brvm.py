#!/usr/bin/env python3
"""
🧠 EXTRACTION SÉMANTIQUE FINANCIÈRE – BRVM
========================================

Analyse financière experte des publications officielles et médiatiques :
- Résultats, bénéfices, CA
- Dividendes
- Risques & avertissements
- Gouvernance & opérations stratégiques
- Pondération temporelle (7j / 1m / 3m / 1a)

🎯 SORTIE : scores exploitables pour BUY / HOLD / SELL
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List
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
# 🔎 DICTIONNAIRES SÉMANTIQUES
# ===============================

SEMANTIC_RULES = {

    # --- PERFORMANCE FINANCIÈRE ---
    "RESULTATS_HAUSSE": {
        "patterns": [
            r"bénéfice.*(hausse|croissance|progression|amélioration)",
            r"résultat.*(progresse|hausse|croissance|amélioration)",
            r"chiffre d.?affaires.*(hausse|croissance|record)",
            r"croissance", r"performance record", r"excédent", r"profit en hausse",
            r"résultat net positif", r"résultat bénéficiaire", r"résultat excédentaire",
            r"amélioration de la rentabilité", r"augmentation du dividende"
        ],
        "score": {"short": 25, "medium": 30, "long": 20},
        "risk": "LOW"
    },

    "RESULTATS_BAISSE": {
        "patterns": [
            r"bénéfice.*baisse", r"résultat.*recul", r"perte", r"dégradation",
            r"résultat net négatif", r"résultat déficitaire", r"détérioration",
            r"chiffre d.?affaires.*baisse", r"diminution du dividende",
            r"baisse de la rentabilité", r"perte nette", r"déficit"
        ],
        "score": {"short": -30, "medium": -25, "long": -15},
        "risk": "HIGH"
    },
    # --- BULLETINS & INDICATEURS MARCHÉ ---
    "BULLETIN_OFFICIEL": {
        "patterns": [
            r"bulletin officiel", r"rapport de la cote", r"cours de clôture", r"variation", r"volume échangé", r"capitalisation", r"marché actif", r"top 5"
        ],
        "score": {"short": 5, "medium": 5, "long": 5},
        "risk": "LOW"
    },
    # --- EVENEMENTS & GENERAL ---
    "EVENEMENT_GENERAL": {
        "patterns": [
            r"dividende", r"distribution", r"bénéfice", r"croissance", r"progression", r"recul", r"alerte", r"convocation", r"assemblée générale", r"communiqué", r"publication", r"résolution", r"coupon", r"paiement", r"investissement", r"acquisition", r"fusion", r"nomination", r"démission", r"gouvernance", r"stratégie", r"plan", r"prévision", r"prévisionnel", r"prévisions", r"perspectives", r"projet", r"financement", r"emprunt", r"obligation", r"augmentation de capital", r"baisse de capital", r"distribution de dividende"
        ],
        "score": {"short": 10, "medium": 10, "long": 10},
        "risk": "MEDIUM"
    },

    # --- DIVIDENDES ---
    "DIVIDENDE_ANNONCE": {
        "patterns": [
            r"dividende", r"distribution.*dividende",
            r"détachement du dividende", r"coupon"
        ],
        "score": {"short": 20, "medium": 25, "long": 30},
        "risk": "LOW"
    },
    "DIVIDENDE": {
        "patterns": [
            r"dividende", r"distribution", r"coupon", r"versement", r"paiement du dividende",
            r"dividende exceptionnel", r"dividende en hausse", r"dividende stable"
        ],
        "score": {"short": 20, "medium": 25, "long": 30},
        "risk": "LOW"
    },
    "SPLIT_ACTION": {
        "patterns": [r"split", r"fractionnement d'action", r"augmentation du nombre d'actions"],
        "score": {"short": 15, "medium": 20, "long": 25},
        "risk": "LOW"
    },
    "BONUS": {
        "patterns": [r"attribution gratuite", r"bonus", r"augmentation de capital gratuite"],
        "score": {"short": 15, "medium": 20, "long": 25},
        "risk": "LOW"
    },
    "PERSPECTIVES_POSITIVES": {
        "patterns": [r"perspectives favorables", r"prévisions positives", r"croissance attendue", r"plan de développement", r"investissement majeur", r"nouveau contrat", r"extension d'activité", r"lancement de produit"],
        "score": {"short": 18, "medium": 22, "long": 28},
        "risk": "LOW"
    },
    # --- RISQUES & AVERTISSEMENTS ---
    "RISQUE_ELEVE": {
        "patterns": [
            r"tension", r"incertitude", r"risque",
            r"endettement élevé", r"restructuration",
            r"difficultés financières", r"alerte"
        ],
        "score": {"short": -20, "medium": -30, "long": -20},
        "risk": "HIGH"
    },

    # --- GOUVERNANCE & STRATÉGIE ---
    "CHANGEMENT_GOUVERNANCE": {
        "patterns": [
            r"nomination", r"démission",
            r"nouveau directeur", r"nouveau dg", r"pdg"
        ],
        "score": {"short": 5, "medium": 10, "long": 15},
        "risk": "MEDIUM"
    },

    "FUSION_ACQUISITION": {
        "patterns": [
            r"fusion", r"acquisition",
            r"prise de participation", r"opa"
        ],
        "score": {"short": 15, "medium": 25, "long": 30},
        "risk": "MEDIUM"
    }
}
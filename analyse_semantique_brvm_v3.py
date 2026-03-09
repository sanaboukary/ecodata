#!/usr/bin/env python3
"""
ANALYSE SÉMANTIQUE BRVM — V4 (CATALYSEURS FONDAMENTAUX)
==========================================================
Modèle quant desk adapté BRVM :

    score_contenu = score_lexique + 3 × score_catalyseur

- score_lexique    : comptage mots positifs/négatifs (signal faible)
- score_catalyseur : phrases qui font bouger le prix  (signal fort, ×3)
- confiance        : pénalité si texte court / vide
- Stocke les composantes séparément pour debug et Top-k downstream
"""
import sys
import os
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

# ─── Lexique financier (signal faible) ─────────────────────────────────────
LEXIQUE_POSITIF = [
    "hausse", "croissance", "progression", "augmentation",
    "bénéfice", "dividende", "amélioration", "rentable",
    "résultat positif", "distribution", "expansion",
    "investissement", "partenariat", "performance", "profit",
    "acquisition", "consolidation", "rebond", "relance",
    "excédent", "solide", "dynamique",
]
LEXIQUE_NEGATIF = [
    "baisse", "recul", "perte", "tension", "incertitude",
    "retard", "risque", "déficit", "suspension",
    "difficultés", "endettement", "dégradation",
    "litige", "sanction", "réduction", "chute",
    "contraction", "ralentissement", "annulation",
]

# ─── Catalyseurs fondamentaux (signal fort, poids ×3) ──────────────────────
# Ce sont les phrases qui ATTIRENT L'ARGENT sur 1-2 semaines
CATALYSEURS_POSITIFS = [
    # Résultats
    "résultat net en hausse",
    "bénéfice net en hausse",
    "résultat net progresse",
    "résultat supérieur aux attentes",
    "croissance à deux chiffres",
    "résultat record",
    "chiffre d'affaires en hausse",
    "ca en progression",
    "bénéfice en progression",
    "marge en amélioration",
    "résultat semestriel en hausse",
    "résultat annuel en hausse",
    # Dividende
    "dividende en hausse",
    "hausse du dividende",
    "dividende exceptionnel",
    "dividende augmente",
    "dividende proposé",
    "dividende de",         # suivi d'un montant
    "distribution de dividende",
    "coupon de",
    "programme de rachat",
    # Contrats / expansion
    "signature de contrat",
    "nouveau contrat",
    "contrat majeur",
    "accord stratégique",
    "partenariat stratégique",
    "acquisition stratégique",
    "extension de capacité",
    "ouverture de",
    "lancement de",
    # Perspectives
    "guidance relevée",
    "perspectives positives",
    "objectifs dépassés",
    "plus haut historique",
    "record de production",
]
CATALYSEURS_NEGATIFS = [
    # Avertissements
    "avertissement sur résultat",
    "profit warning",
    "révision à la baisse",
    "objectifs revus à la baisse",
    "résultat inférieur aux attentes",
    # Pertes
    "perte nette",
    "perte importante",
    "déficit aggravé",
    "baisse du résultat",
    "résultat net en baisse",
    "chiffre d'affaires en baisse",
    # Dividende
    "baisse du dividende",
    "suspension du dividende",
    "dividende supprimé",
    "pas de dividende",
    # Problèmes juridiques / réglementaires
    "litige",
    "sanction",
    "mise en redressement",
    "suspension de cotation",
    "non-conformité",
    "difficultés financières",
    "endettement excessif",
    # Notation
    "dégradation de note",
    "notation dégradée",
    "perspective négative",
    # Opérationnel
    "incident opérationnel",
    "arrêt de production",
    "rappel de produit",
]


def nettoyer_texte(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Zà-ÿ0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def confiance_texte(text: str) -> float:
    """Pénalise les textes courts (souvent du bruit, pas des catalyseurs)."""
    ln = len(text)
    if ln < 100:
        return 0.0
    if ln < 500:
        return 0.4
    if ln < 2000:
        return 0.7
    return 1.0


def score_text(text: str) -> dict:
    """
    Retourne :
        score_catalyseur  : nb catalyseurs détectés (phrases ×3)
        score_lexique     : comptage mot-clés simples
        score_contenu     : score_lexique + 3 × score_catalyseur
        reasons           : liste des signaux detectes
        has_catalyseur    : bool
    """
    t = nettoyer_texte(text)

    score_cat_pos = 0
    score_cat_neg = 0
    reasons = []

    # ── Catalyseurs positifs (poids fort)
    for phrase in CATALYSEURS_POSITIFS:
        if phrase in t:
            score_cat_pos += 1
            reasons.append(f"[CAT+] {phrase}")

    # ── Catalyseurs négatifs (poids fort)
    for phrase in CATALYSEURS_NEGATIFS:
        if phrase in t:
            score_cat_neg += 1
            reasons.append(f"[CAT-] {phrase}")

    score_catalyseur = score_cat_pos - score_cat_neg

    # ── Lexique simple (poids faible)
    score_lex_pos = sum(1 for w in LEXIQUE_POSITIF if w in t)
    score_lex_neg = sum(1 for w in LEXIQUE_NEGATIF if w in t)
    score_lexique  = score_lex_pos - score_lex_neg

    # ── Score contenu final
    score_contenu = score_lexique + 3 * score_catalyseur

    return {
        "score_catalyseur": score_catalyseur,
        "score_catalyseur_pos": score_cat_pos,
        "score_catalyseur_neg": score_cat_neg,
        "score_lexique": score_lexique,
        "score_contenu": score_contenu,
        "reasons": reasons,
        "has_catalyseur": score_catalyseur != 0,
    }


class SemanticAnalyzerBRVMV4:
    def __init__(self):
        _, self.db = get_mongo_db()

    def run(self, sources=("RICHBOURSE", "BRVM_PUBLICATION")):
        print("=" * 70)
        print(" ANALYSE SÉMANTIQUE BRVM — V4 (CATALYSEURS FONDAMENTAUX) ".center(70))
        print("=" * 70)

        pubs = list(self.db.curated_observations.find({
            "source": {"$in": list(sources)},
            "$or": [
                {"attrs.full_text":   {"$exists": True}},
                {"attrs.description": {"$exists": True}},
                {"attrs.contenu":     {"$exists": True}},
            ]
        }))
        print(f"{len(pubs)} documents a analyser\n")

        n_ok = n_skip = n_cat = 0

        for pub in pubs:
            attrs = pub.get("attrs", {})
            text  = (attrs.get("full_text")
                     or attrs.get("description")
                     or attrs.get("contenu", ""))

            confiance = confiance_texte(text)
            if confiance == 0.0:
                n_skip += 1
                # Store zero scores so aggregator ignores this doc
                self.db.curated_observations.update_one(
                    {"_id": pub["_id"]},
                    {"$set": {
                        "attrs.semantic_score_base":      0,
                        "attrs.semantic_score_catalyseur": 0,
                        "attrs.semantic_score_lexique":    0,
                        "attrs.semantic_confiance":        0.0,
                        "attrs.has_catalyseur":            False,
                        "attrs.semantic_scores": {"SEMAINE": 0, "MOIS": 0,
                                                  "TRIMESTRE": 0, "ANNUEL": 0},
                        "attrs.semantic_reasons":          [],
                        "attrs.semantic_analyzed_at":      datetime.now().isoformat(),
                        "attrs.semantic_version":          "v4",
                    }}
                )
                continue

            result = score_text(text)
            s      = result["score_contenu"]

            # Horizon weights kept for backward compat (aggregator uses score_contenu directly)
            horizon_scores = {
                "SEMAINE":   round(s * 2.0, 2),
                "MOIS":      round(s * 1.5, 2),
                "TRIMESTRE": round(s * 1.2, 2),
                "ANNUEL":    round(float(s), 2),
            }

            self.db.curated_observations.update_one(
                {"_id": pub["_id"]},
                {"$set": {
                    "attrs.semantic_score_base":       s,
                    "attrs.semantic_score_catalyseur":  result["score_catalyseur"],
                    "attrs.semantic_score_catalyseur_pos": result["score_catalyseur_pos"],
                    "attrs.semantic_score_catalyseur_neg": result["score_catalyseur_neg"],
                    "attrs.semantic_score_lexique":     result["score_lexique"],
                    "attrs.semantic_confiance":         confiance,
                    "attrs.has_catalyseur":             result["has_catalyseur"],
                    "attrs.semantic_scores":            horizon_scores,
                    "attrs.semantic_reasons":           result["reasons"],
                    "attrs.semantic_analyzed_at":       datetime.now().isoformat(),
                    "attrs.semantic_version":           "v4",
                }}
            )

            n_ok += 1
            if result["has_catalyseur"]:
                n_cat += 1
                titre = attrs.get("titre", attrs.get("title", "?"))[:60]
                print(f"  [CAT] {titre}")
                for r in result["reasons"][:4]:
                    print(f"        {r}")
                print(f"        score_contenu={s}  (cat={result['score_catalyseur']}×3"
                      f" + lex={result['score_lexique']})  confiance={confiance}")

        print(f"\n{'='*70}")
        print(f"  Analyses     : {n_ok} ok  /  {n_skip} ignores (texte vide/court)")
        print(f"  Avec cataly. : {n_cat}  ← seuls ces docs activent le signal explosion")
        print(f"{'='*70}")
        print("  Prochaine etape : agregateur_semantique_actions.py")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    SemanticAnalyzerBRVMV4().run()

#!/usr/bin/env python3
"""
Enrichissement sectoriel BRVM – VERSION ADAPTÉE BASE RÉELLE
==========================================================

- Extraction du ticker depuis le champ `key`
- Fallback par mots-clés sectoriels
- Compatible RichBourse / BRVM
"""

from plateforme_centralisation.mongo import get_mongo_db
import re

# ======================
# PONDÉRATION DES SOURCES (logique pro)
# ======================
SOURCE_WEIGHTS = {
    "BRVM_PUBLICATION": 1.0,
    "COMMUNIQUE_EMETTEUR": 1.0,
    "RICHBOURSE": 0.8,
    "ANALYSE_FINANCIERE": 0.7,
    "WorldBank": 0.6,
    "IMF": 0.6,
    "AfDB": 0.6,
    "UN_SDG": 0.5,
    "PRESSE_REGIONALE": 0.4,
    "BLOG": 0.25
}

# ======================
# SECTEURS BRVM
# ======================
BRVM_SECTORS = {
    "BANQUE": {
        "tickers": ["BICC", "SGBC", "SIBC", "BOAB", "BOAC", "NSBC", "ECOC", "ETIT"],
        "keywords": ["banque", "crédit", "prêt", "fonds propres", "résultat bancaire"]
    },
    "ASSURANCE": {
        "tickers": ["NSIA", "SAFC", "SCRC"],
        "keywords": ["assurance", "prime", "sinistre", "réassurance"]
    },
    "ENERGIE": {
        "tickers": ["TOTAL", "PETROCI", "CIPREL", "ECOB"],
        "keywords": ["énergie", "électricité", "gaz", "pétrole", "centrale"]
    },
    "AGROINDUSTRIE": {
        "tickers": ["SIFCA", "SUCAF", "PALMCI", "SOGC", "SPHC"],
        "keywords": ["cacao", "sucre", "palme", "hévéa", "agricole"]
    },
    "DISTRIBUTION": {
        "tickers": ["SDSC", "CDC", "CFAO"],
        "keywords": ["distribution", "commerce", "vente", "magasin"]
    },
    "INDUSTRIE": {
        "tickers": ["SMBC", "SICABLE", "FILTISAC"],
        "keywords": ["industrie", "usine", "production", "fabrication"]
    },
    "SERVICES": {
        "tickers": ["ONATEL", "SONATEL"],
        "keywords": ["télécom", "réseau", "abonnés", "data"]
    }
}

ALL_TICKERS = {t for s in BRVM_SECTORS.values() for t in s["tickers"]}

# ======================
# EXTRACTION TICKER
# ======================
def extract_ticker(pub):
    key = pub.get("key", "")
    if not key:
        return None

    # Exemple : "[RICHBOURSE] SDSC CI : Rapport d'activités ..."
    m = re.search(r"\b([A-Z]{3,6})\b", key)
    if m:
        t = m.group(1)
        if t in ALL_TICKERS:
            return t
    return None

# ======================
# DÉTECTION SECTEUR
# ======================
def detect_sector(text, ticker=None):
    text = text.lower()
    scores = {}

    for sector, data in BRVM_SECTORS.items():
        score = 0

        if ticker and ticker in data["tickers"]:
            score += 100  # priorité absolue

        for kw in data["keywords"]:
            if kw in text:
                score += 10

        scores[sector] = score

    best = max(scores, key=scores.get)
    return best if scores[best] >= 20 else "AUTRE"

# ======================
# PIPELINE
# ======================
if __name__ == "__main__":

    from datetime import datetime, timedelta
    _, db = get_mongo_db()
    pubs = list(db.curated_observations.find({"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}}))
    count = 0

    # 1. Enrichissement publication par publication (secteur, ticker, pondération)
    for pub in pubs:
        attrs = pub.get("attrs", {})
        full_text = attrs.get("full_text", "")
        description = attrs.get("description", "")
        text = f"{full_text} {description}"
        ticker = extract_ticker(pub)
        sector = detect_sector(text, ticker)
        source = pub.get("source", "")
        source_weight = SOURCE_WEIGHTS.get(source, 0.5)
        sentiment_score = attrs.get("sentiment_score")
        weighted_sentiment_score = None
        if sentiment_score is not None:
            try:
                weighted_sentiment_score = float(sentiment_score) * source_weight
            except Exception:
                weighted_sentiment_score = None
        db.curated_observations.update_one(
            {"_id": pub["_id"]},
            {"$set": {
                "sector": sector,
                "ticker": ticker,
                "source_weight": source_weight,
                "weighted_sentiment_score": weighted_sentiment_score
            }}
        )
        count += 1

    print(f"\n✅ {count} publications enrichies avec un secteur et une pondération source.")

    # 2. Calcul du score hebdomadaire (semantic_score_short) pour chaque ticker
    print("\nCalcul du score hebdomadaire (semantic_score_short) pour chaque ticker...")
    tickers = list(ALL_TICKERS)
    now = datetime.now()
    for ticker in tickers:
        # Récupère toutes les publications du ticker sur les 7 derniers jours
        pubs_7j = list(db.curated_observations.find({
            "ticker": ticker,
            "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]},
            "ts": {"$gte": (now - timedelta(days=7)).isoformat()}
        }))
        scores = []
        for pub in pubs_7j:
            ws = pub.get("weighted_sentiment_score")
            if ws is not None:
                scores.append(ws)
        if scores:
            score_ct = round(sum(scores) / len(scores), 2)
        else:
            score_ct = 0.0
        # Stocke ce score dans la base pour le ticker (dans un doc dédié ou dans une collection d'agrégats)
        db.curated_observations.update_many(
            {"ticker": ticker},
            {"$set": {"semantic_score_short": score_ct}}
        )
        print(f"[HEBDO] {ticker} | semantic_score_short = {score_ct}")

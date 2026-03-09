#!/usr/bin/env python3
"""
PROPAGATION SCORE SECTORIEL → ACTION – BRVM
===========================================

- Pour chaque action, applique le bonus sectoriel selon l'horizon
- Calcule le score final et le signal cohérent
- Stocke dans la collection MongoDB 'decisions_finales_brvm'
"""

import os
import sys
from datetime import datetime, timedelta

# --- Django & MongoDB ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

# --- TABLE BONUS SECTORIEL ---
BONUS_COURT_TERME = [
    (30, 20),
    (10, 10),
    (-10, 0),
    (-30, -10),
    (-1000, -20)
]
BONUS_LONG_TERME = [
    (30, 10),
    (10, 5),
    (-10, 0),
    (-30, -5),
    (-1000, -10)
]

# --- SIGNAL FINAL ---
def interpret_signal(score):
    if score >= 50:
        return "BUY"
    elif score >= 40:
        return "HOLD"
    else:
        return "SELL"

# --- GÉNÉRATION DES JUSTIFICATIONS ---
def generate_justifications(signal, sector, horizon, score_ia, sector_score, sector_bonus, pubs, scores_ia):
    justifications = []
    horizon_label = horizon.capitalize()
    # Semaine/mois : accent sur le récent, technique, secteur court terme
    # Trimestre/annuel : accent sur secteur, fondamentaux, stabilité
    if signal == "BUY":
        justifications.append(f"Signal BUY confirmé pour l’horizon {horizon_label}")
        if sector_score >= 10:
            justifications.append(f"Secteur {sector} en dynamique favorable sur {horizon_label}")
        elif sector_score <= -10:
            justifications.append(f"BUY tactique malgré un secteur défavorable sur {horizon_label}")
        else:
            justifications.append(f"Opportunité spécifique à l’action, secteur {sector} neutre sur {horizon_label}")
        if pubs:
            pos_pubs = [p for p in pubs if p.get("weighted_sentiment_score", 0) > 0]
            if pos_pubs:
                justifications.append("Publications récentes à sentiment positif")
        if scores_ia and max(scores_ia) > 0:
            justifications.append("Configuration technique cohérente avec une poursuite de la tendance")
    elif signal == "HOLD":
        justifications.append(f"Signal HOLD : absence de catalyseur clair à {horizon_label.lower()}")
        if -10 < sector_score < 10:
            justifications.append(f"Contexte sectoriel {sector} neutre ou incertain sur {horizon_label}")
        else:
            justifications.append(f"Secteur {sector} mitigé sur {horizon_label}")
        justifications.append("Signaux techniques et sémantiques mitigés")
        justifications.append("Attente d’une confirmation du marché")
    else:  # SELL
        justifications.append(f"Signal SELL pour l’horizon {horizon_label}")
        if sector_score <= -10:
            justifications.append(f"Secteur {sector} sous pression informationnelle sur {horizon_label}")
        else:
            justifications.append(f"Secteur {sector} peu porteur sur {horizon_label}")
        if pubs:
            neg_pubs = [p for p in pubs if p.get("weighted_sentiment_score", 0) < 0]
            if neg_pubs:
                justifications.append("Publications récentes à sentiment négatif")
        justifications.append("Risque de poursuite de la baisse à court/moyen terme")
    # Ajustement horizon long terme
    if horizon in ["TRIMESTRE", "ANNUEL"] and signal == "BUY":
        justifications.append("Recommandation orientée long terme")
        justifications.append("Secteur structurellement porteur")
        justifications.append("Visibilité sur les dividendes")
        justifications.append("Profil risque/rendement attractif")
    return justifications

def get_sector_bonus(score, horizon):
    if horizon in ["SEMAINE", "MOIS"]:
        table = BONUS_COURT_TERME
    else:
        table = BONUS_LONG_TERME
    for threshold, bonus in table:
        if score >= threshold:
            return bonus
    return 0

if __name__ == "__main__":
    _, db = get_mongo_db()
    now = datetime.now().isoformat()
    # Charger tous les scores sectoriels par horizon
    sector_scores = {}
    for doc in db.sector_sentiment_aggregates.find({}):
        sector_scores[(doc["sector"], doc["horizon"])] = doc["score"]
    # Pour chaque action, chaque horizon
    actions = list(db.curated_observations.distinct("ticker", {"ticker": {"$ne": None}}))
    horizons = ["SEMAINE", "MOIS", "TRIMESTRE", "ANNUEL"]
    for action in actions:
        # Trouver le secteur de l'action
        pub = db.curated_observations.find_one({"ticker": action, "sector": {"$ne": None}})
        if not pub:
            continue
        sector = pub["sector"]
        for horizon in horizons:
            # Score IA action (exemple: moyenne des scores sémantiques sur l'horizon)
            pubs = list(db.curated_observations.find({
                "ticker": action,
                "ts": {"$gte": (datetime.now() - {
                    "SEMAINE": timedelta(days=7),
                    "MOIS": timedelta(days=30),
                    "TRIMESTRE": timedelta(days=90),
                    "ANNUEL": timedelta(days=365)
                }[horizon]).isoformat()}
            }))
            scores_ia = [pub.get("weighted_sentiment_score") for pub in pubs if pub.get("weighted_sentiment_score") is not None]
            score_ia = round(sum(scores_ia) / len(scores_ia), 2) if scores_ia else 0.0
            # Score sectoriel et bonus
            sector_score = sector_scores.get((sector, horizon), 0.0)
            sector_bonus = get_sector_bonus(sector_score, horizon)
            score_final = score_ia + sector_bonus
            signal = interpret_signal(score_final)
            justifications = generate_justifications(signal, sector, horizon, score_ia, sector_score, sector_bonus, pubs, scores_ia)

            # Enrichissement premium : prix actuel, prix cible, gain attendu, nom société
            # On prend la dernière publication pour les prix
            last_pub = db.curated_observations.find_one({"ticker": action}, sort=[("ts", -1)])
            prix_actuel = last_pub.get("prix", None) if last_pub else None
            prix_cible = None
            gain_attendu = None
            if prix_actuel is not None:
                # Exemple : prix cible = prix actuel * (1 + score_final/100)
                prix_cible = round(prix_actuel * (1 + score_final/100), 2)
                gain_attendu = round((prix_cible - prix_actuel) / prix_actuel * 100, 1)
            company_name = last_pub.get("company_name") if last_pub and last_pub.get("company_name") else None

            doc = {
                "symbol": action,
                "sector": sector,
                "horizon": horizon,
                "score_ia": score_ia,
                "sector_score": sector_score,
                "sector_bonus": sector_bonus,
                "score_final": score_final,
                "signal": signal,
                "justifications": justifications,
                "generated_at": now,
                "prix_actuel": prix_actuel,
                "prix_cible": prix_cible,
                "gain_attendu": gain_attendu,
                "company_name": company_name
            }
            db.decisions_finales_brvm.replace_one(
                {"symbol": action, "horizon": horizon},
                doc,
                upsert=True
            )
            print(f"✅ {action} [{horizon}] | Score final: {score_final} | Signal: {signal} | Prix: {prix_actuel} | Cible: {prix_cible} | Gain: {gain_attendu}%")
    print("\n✅ Propagation sectorielle → action terminée et sauvegardée dans decisions_finales_brvm.")

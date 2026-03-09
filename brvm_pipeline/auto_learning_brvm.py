#!/usr/bin/env python3
"""
🧠 AUTO-LEARNING BRVM
=====================
Recalibrage automatique des poids IA
basé sur les décisions passées (GAGNÉ / PERDU)
"""

from collections import defaultdict
from plateforme_centralisation.mongo import get_mongo_db

# -----------------------------
# Connexion MongoDB
# -----------------------------
db = get_mongo_db()
decisions = db["decisions_brvm"]
config = db["ia_config_brvm"]

# -----------------------------
# Paramètres initiaux
# -----------------------------
BASE_WEIGHTS = {
    "rsi": 1.0,
    "volatilite": 1.0,
    "volume_ratio": 1.0,
    "sentiment": 1.0,
    "macro": 1.0,
    "correlation": 1.0,
    "dividende": 1.0
}

stats = {
    "GAGNE": defaultdict(list),
    "PERDU": defaultdict(list)
}

# -----------------------------
# Collecte des décisions passées
# -----------------------------
for d in decisions.find({"statut": {"$in": ["GAGNE", "PERDU"]}}):
    statut = d["statut"]
    features = d.get("features", {})

    for k, v in features.items():
        if isinstance(v, (int, float)):
            stats[statut][k].append(v)

# -----------------------------
# Calcul des nouveaux poids
# -----------------------------
new_weights = {}

for feature in BASE_WEIGHTS:
    gains = stats["GAGNE"].get(feature, [])
    pertes = stats["PERDU"].get(feature, [])

    if not gains or not pertes:
        new_weights[feature] = BASE_WEIGHTS[feature]
        continue

    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(pertes) / len(pertes)

    # Coefficient d’apprentissage
    delta = (avg_gain - avg_loss) / (abs(avg_loss) + 1e-6)

    # Limitation pour éviter les dérives
    delta = max(min(delta, 0.3), -0.3)

    new_weights[feature] = round(
        BASE_WEIGHTS[feature] * (1 + delta), 3
    )

# -----------------------------
# Sauvegarde en base
# -----------------------------
config.update_one(
    {"type": "poids_ia"},
    {"$set": {"weights": new_weights}},
    upsert=True
)

# -----------------------------
# Affichage
# -----------------------------
print("\n=== 🔄 RECALIBRATION IA TERMINÉE ===\n")
for k, v in new_weights.items():
    print(f"{k.upper():15s} -> poids = {v}")

print("\n✅ Poids IA mis à jour et prêts pour les prochaines décisions")

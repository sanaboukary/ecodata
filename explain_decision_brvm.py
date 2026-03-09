def determine_horizon(data: dict) -> dict:
    """
    Détermine l’horizon d’investissement dominant
    """
    rsi = data.get("rsi", 0)
    volatility = data.get("volatility", 0)
    score_semantic = data.get("score_semantic", 0)
    decision = data.get("decision", "")

    # Sécurisation des types
    if rsi is None:
        rsi = 0
    try:
        rsi = float(rsi)
    except Exception:
        rsi = 0
    if volatility is None:
        volatility = 0
    try:
        volatility = float(volatility)
    except Exception:
        volatility = 0
    if score_semantic is None:
        score_semantic = 0
    try:
        score_semantic = float(score_semantic)
    except Exception:
        score_semantic = 0

    # Par défaut
    horizon = "Court terme (7 jours)"
    rationale = "Le contexte actuel privilégie une approche tactique de court terme."

    # Long terme
    if score_semantic >= 30 and volatility < 30:
        horizon = "Long terme (1 an)"
        rationale = (
            "Les fondamentaux informationnels sont solides et la volatilité est maîtrisée, "
            "ce qui favorise une stratégie de détention longue."
        )
    # Trimestriel
    elif score_semantic >= 20 and volatility < 40:
        horizon = "Moyen / long terme (3 mois)"
        rationale = (
            "Les signaux fondamentaux sont positifs et compatibles avec un horizon trimestriel."
        )
    # Mensuel
    elif 45 <= rsi <= 65 and volatility < 50:
        horizon = "Moyen terme (1 mois)"
        rationale = (
            "La dynamique technique est équilibrée, adaptée à une stratégie mensuelle."
        )
    # Court terme renforcé
    elif volatility >= 60:
        horizon = "Très court terme (7 jours)"
        rationale = (
            "La volatilité élevée impose des opérations rapides avec contrôle strict du risque."
        )

    return {
        "horizon": horizon,
        "horizon_rationale": rationale
    }
#!/usr/bin/env python3
"""
📝 GÉNÉRATION D’EXPLICATIONS – DÉCISIONS BRVM
===========================================

Transforme une décision IA en justification claire et professionnelle
"""

def explain_decision(data: dict) -> str:
    """
    data contient :
    - decision
    - confidence
    - score_tech
    - score_semantic
    - trend
    - rsi
    - volatility
    - correlation_penalty
    """
    decision = data["decision"]
    confidence = data["confidence"]
    explanations = []
    # 1️⃣ TECHNIQUE
    if data.get("trend") == "UP":
        explanations.append("La tendance technique est haussière.")
    else:
        explanations.append("La tendance technique reste baissière ou neutre.")
    rsi = data.get("rsi", 0)
    if rsi is None:
        rsi = 0
    try:
        rsi = float(rsi)
    except Exception:
        rsi = 0
    if 45 <= rsi <= 65:
        explanations.append(f"Le RSI est équilibré ({rsi:.1f}), indiquant une dynamique saine.")
    elif rsi > 70:
        explanations.append(f"Le RSI est élevé ({rsi:.1f}), signalant un risque de surachat.")
    else:
        explanations.append(f"Le RSI est faible ({rsi:.1f}), traduisant un manque de momentum.")
    # 2️⃣ VOLATILITÉ
    volatility = data.get("volatility", 0)
    if volatility is None:
        volatility = 0
    try:
        volatility = float(volatility)
    except Exception:
        volatility = 0
    if volatility > 60:
        explanations.append("La volatilité est élevée, ce qui accroît le risque à court terme.")
    else:
        explanations.append("La volatilité reste contenue, favorable à une stratégie progressive.")
    # 3️⃣ SÉMANTIQUE
    if data.get("score_semantic", 0) >= 20:
        explanations.append("Les publications récentes dégagent un signal fondamental positif.")
    elif data.get("score_semantic", 0) > 0:
        explanations.append("Les informations disponibles sont modérément favorables.")
    else:
        explanations.append("Aucun catalyseur informationnel fort n’a été identifié récemment.")
    # 4️⃣ CORRÉLATION
    if data.get("correlation_penalty", 0) > 0:
        explanations.append("Une forte corrélation avec d’autres titres limite la diversification.")
    # 5️⃣ CONCLUSION MÉTIER
    if decision.startswith("BUY"):
        conclusion = "Les conditions sont réunies pour une prise de position progressive."
    elif "SURVEILLANCE" in decision:
        conclusion = "Une surveillance active est recommandée en attente d’un signal de confirmation."
    elif "RISQUE" in decision:
        conclusion = "Le contexte actuel impose une grande prudence."
    else:
        conclusion = "Aucune action immédiate n’est recommandée dans le contexte actuel."

    # Ajout de l'horizon dominant
    horizon_info = determine_horizon(data)

    # TEXTE FINAL
    return (
        f"Décision : {decision} (confiance {confidence}%)\n"
        f"Horizon recommandé : {horizon_info['horizon']}\n"
        f"{horizon_info['horizon_rationale']}\n\n"
        + " ".join(explanations)
        + " "
        + conclusion
    )

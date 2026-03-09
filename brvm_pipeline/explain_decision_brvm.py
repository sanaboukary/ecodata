def explain_decision(action, horizon, signal, score, raisons):
    horizon_map = {
        "SEMAINE": "Court terme (7 jours)",
        "MOIS": "Moyen terme (1 mois)",
        "TRIMESTRE": "Trimestriel (3 mois)",
        "ANNUEL": "Long terme (1 an)"
    }
    texte = (
        f"Décision finale : {signal} (score {score:.1f})\n"
        f"Horizon recommandé : {horizon_map.get(horizon, horizon)}\n"
        f"Justifications : {'; '.join(raisons)}\n"
    )
    return texte

# Exemple d'utilisation
if __name__ == "__main__":
    action = {
        'tech_score': 80,
        'volume_score': 1.7,
        'sentiment_7j': 60,
        'sentiment_30j': 55,
        'correlation_score': 40,
        'macro_score': 30,
        'sentiment_90j': 50,
        'fundamental_score': 70,
        'tech_long_score': 65,
        'dividend_score': 80,
        'sentiment_1y': 60,
        'volatility_penalty': 20
    }
    from decision_finale_brvm import decision_finale
    for horizon in ["SEMAINE", "MOIS", "TRIMESTRE", "ANNUEL"]:
        signal, score, raisons = decision_finale(action, horizon)
        texte = explain_decision(action, horizon, signal, score, raisons)
        print(texte)
        print()

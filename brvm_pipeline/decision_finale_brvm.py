

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
from brvm_pipeline.config_horizons import HORIZONS

def calcul_score_horizon(features, horizon):
    w = HORIZONS[horizon]["weights"]
    score = 0
    for facteur, poids in w.items():
        score += features.get(facteur, 0) * poids
    return round(score, 2)

def get_features(action):
    # Mapping générique pour extraire les features attendues par horizon
    return {
        "technique": action.get("tech_score", 0),
        "volume": action.get("volume_score", 0),
        "sentiment": action.get("sentiment_7j", 0),
        "volatilite": action.get("volatilite", 0),
        "macro": action.get("macro_score", 0),
        "correlation": action.get("correlation_score", 0),
        "fondamentaux": action.get("fundamental_score", 0),
        "dividendes": action.get("dividend_score", 0)
    }


# Pipeline principal
if __name__ == "__main__":
    from plateforme_centralisation.mongo import get_mongo_db
    _, db = get_mongo_db()


    def save_decision(symbol, horizon, signal, score, confidence, features, action, justifications=None):
        from datetime import datetime
        prix_entree = action.get("prix_dernier", None)
        prix_sortie = action.get("prix_sortie", None)
        stop_loss = action.get("stop_loss", None)
        take_profit = action.get("take_profit", None)
        reliability_score = action.get("reliability_score", confidence)
        if justifications is None:
            justifications = [f"Score calculé: {score}"]
        db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "horizon": horizon},
            {"$set": {
                "symbol": symbol,
                "horizon": horizon,
                "signal": signal,
                "score": score,
                "confidence": confidence,
                "justifications": justifications,
                "prix_entree": prix_entree,
                "prix_sortie": prix_sortie,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "reliability_score": reliability_score,
                "features": features,
                "date_generation": datetime.now(datetime.UTC)
            }},
            upsert=True
        )

    analyses = list(db.brvm_ai_analysis.find({}))
    for doc in analyses:
        action = doc.get("attrs", {})
        symbol = action.get("symbol", "N/A")
        features = get_features(action)
        for horizon in HORIZONS:
            score = calcul_score_horizon(features, horizon)
            if score >= 70:
                signal = "BUY"
                justifications = ["Signal d'achat fort sur cet horizon"]
            elif score >= 55:
                signal = "HOLD"
                justifications = ["Signal neutre, surveillance recommandée"]
            else:
                signal = "SELL"
                justifications = ["Signal de vente ou absence d'opportunité"]
            confidence = min(95, int(score))
            print(f"{symbol} | {horizon} | {signal} | score={score}")
            save_decision(
                symbol=symbol,
                horizon=horizon,
                signal=signal,
                score=score,
                confidence=confidence,
                features=features,
                action=action,
                justifications=justifications
            )

HORIZONS = {
    "SEMAINE": {
        "days": 7,
        "weights": {
            "technique": 0.35,
            "volume": 0.25,
            "sentiment": 0.25,
            "volatilite": -0.15,
            "macro": 0.05
        }
    },
    "MOIS": {
        "days": 30,
        "weights": {
            "technique": 0.30,
            "sentiment": 0.20,
            "correlation": 0.20,
            "macro": 0.20,
            "volatilite": -0.10
        }
    },
    "TRIMESTRE": {
        "days": 90,
        "weights": {
            "fondamentaux": 0.35,
            "sentiment": 0.25,
            "technique": 0.20,
            "macro": 0.20
        }
    },
    "ANNUEL": {
        "days": 365,
        "weights": {
            "dividendes": 0.40,
            "fondamentaux": 0.35,
            "sentiment": 0.15,
            "volatilite": -0.10
        }
    }
}

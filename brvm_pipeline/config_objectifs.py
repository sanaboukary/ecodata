OBJECTIFS = {
    "TRADING": {
        "horizons": ["SEMAINE", "MOIS"],
        "weights": {
            "momentum": 0.30,
            "volume": 0.25,
            "sentiment": 0.25,
            "volatilite": -0.20
        }
    },
    "DIVIDENDE": {
        "horizons": ["ANNUEL"],
        "weights": {
            "dividende": 0.45,
            "stabilite": 0.25,
            "fondamentaux": 0.20,
            "volatilite": -0.10
        }
    },
    "CROISSANCE": {
        "horizons": ["MOIS", "TRIMESTRE", "ANNUEL"],
        "weights": {
            "fondamentaux": 0.35,
            "macro": 0.25,
            "sentiment": 0.20,
            "correlation": 0.20
        }
    },
    "DEFENSIF": {
        "horizons": ["MOIS", "TRIMESTRE"],
        "weights": {
            "stabilite": 0.40,
            "drawdown": -0.30,
            "volatilite": -0.20,
            "sentiment": 0.10
        }
    }
}

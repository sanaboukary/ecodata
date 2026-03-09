"""
Module : granularite_temporelle.py
Ajoute la gestion multi-horizon (court, moyen, long terme) pour l'analyse et la recommandation BRVM.
"""

from enum import Enum
from datetime import datetime, timedelta

class Horizon(Enum):
    COURT_TERME = 'court_terme'      # Semaine
    MOYEN_TERME = 'moyen_terme'      # Mois/Trimestre
    LONG_TERME = 'long_terme'        # Année

def filtrer_par_horizon(data, horizon: Horizon):
    """
    Filtre les données selon l'horizon choisi.
    - COURT_TERME : 7 derniers jours
    - MOYEN_TERME : 90 derniers jours
    - LONG_TERME  : 365 derniers jours
    """
    now = datetime.now()
    if horizon == Horizon.COURT_TERME:
        date_limite = now - timedelta(days=7)
    elif horizon == Horizon.MOYEN_TERME:
        date_limite = now - timedelta(days=90)
    else:
        date_limite = now - timedelta(days=365)
    
    return [d for d in data if 'ts' in d and d['ts'] >= date_limite.strftime('%Y-%m-%d')]

def recommander_selon_horizon(data, horizon: Horizon):
    """
    Applique une logique de recommandation différente selon l'horizon.
    (Exemple simplifié, à spécialiser selon les signaux pertinents)
    """
    if horizon == Horizon.COURT_TERME:
        # Privilégier volatilité, volume, signaux techniques
        return recommander_court_terme(data)
    elif horizon == Horizon.MOYEN_TERME:
        # Prendre en compte tendances sectorielles, résultats trimestriels
        return recommander_moyen_terme(data)
    else:
        # Privilégier fondamentaux, stabilité, dividendes
        return recommander_long_terme(data)

def recommander_court_terme(data):
    # Exemple : signaux techniques, breakout, volume anormal
    # ... à compléter selon ta logique
    return []

def recommander_moyen_terme(data):
    # Exemple : tendance sur 3 mois, news sectorielles, sentiment
    # ... à compléter selon ta logique
    return []

def recommander_long_terme(data):
    # Exemple : fondamentaux solides, dividendes, croissance
    # ... à compléter selon ta logique
    return []

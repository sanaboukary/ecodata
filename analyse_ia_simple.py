# =====================
# SAUVEGARDE ANALYSE IA (MongoDB)
# =====================
import sys
# Forcer UTF-8 sur Windows (évite UnicodeEncodeError cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime, timezone
import statistics
from scipy import stats
from scipy.stats import percentileofscore, linregress
import numpy as np

# MODE DUAL : --mode daily (court terme) ou défaut weekly (moyen terme)
MODE_DAILY = "--mode" in sys.argv and "daily" in sys.argv
if MODE_DAILY:
    print("[MODE] COURT TERME — données journalières (prices_daily) | Horizon 2-3 semaines")
else:
    print("[MODE] MOYEN TERME  — données hebdomadaires (prices_weekly) | Horizon 4-8 semaines")

def sauvegarder_analyse_ia(db, symbol, result):
    """
    Sauvegarde standardisée de l'analyse IA dans brvm_ai_analysis ET curated_observations (pipeline compatible)
    """
    # 1. brvm_ai_analysis (historique IA)
    db.brvm_ai_analysis.update_one(
        {"symbol": symbol},
        {
            "$set": {
                "symbol": symbol,
                "signal": result["signal"],
                "score": result["score"],
                "details": result.get("details", []),
                "trend": result.get("trend"),
                "rsi": result.get("rsi"),
                "volatility": result.get("volatility"),
                "volume_ratio": result.get("volume_ratio"),
                "vsr": result.get("vsr"),
                "momentum_5j": result.get("momentum_5j"),
                "correlation_penalty": result.get("correlation_penalty", 0),
                "generated_at": datetime.now(timezone.utc),
                "source": "ANALYSE_IA_SIMPLE",
                "breakout_score": result.get("breakout_score"),
                "atr_expansion": result.get("atr_expansion"),
                "vol_shock_label": result.get("vol_shock_label"),
                "score_alpha": result.get("score_alpha"),
                "alpha_label": result.get("alpha_label"),
                "alpha_breakout": result.get("alpha_breakout"),
                "alpha_vol_shock": result.get("alpha_vol_shock"),
                "alpha_rs": result.get("alpha_rs"),
                "alpha_vol_exp": result.get("alpha_vol_exp"),
                "alpha_vcp": result.get("alpha_vcp"),
                "wos_today": result.get("wos_today"),
                "wos_3": result.get("wos_3"),
                "vcp_score": result.get("vcp_score"),
                "vcp_label": result.get("vcp_label"),
                "vcp_atr_ratio": result.get("vcp_atr_ratio"),
            }
        },
        upsert=True
    )
    # 2. curated_observations (pour décision finale) - FUSION avec données existantes
    existing = db.curated_observations.find_one({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if existing:
        # Fusionner les attrs (garder les données sémantiques existantes)
        attrs_merged = existing.get("attrs", {})
        attrs_merged.update({
            "signal": result.get("signal"),
            "score": result.get("score"),
            "confiance": result.get("confiance"),
            "details": result.get("details", []),
            "trend": result.get("trend"),
            "rsi": result.get("rsi"),
            "volatility": result.get("volatility"),
            "volume_ratio": result.get("volume_ratio"),
            "vsr": result.get("vsr"),
            "momentum_5j": result.get("momentum_5j"),
            "correlation_penalty": result.get("correlation_penalty", 0),
            "sentiment": result.get("sentiment"),
            "last_technical_update": datetime.now(timezone.utc),
            "breakout_score": result.get("breakout_score"),
            "atr_expansion": result.get("atr_expansion"),
            "vol_shock_label": result.get("vol_shock_label"),
            "score_alpha": result.get("score_alpha"),
            "alpha_label": result.get("alpha_label"),
        })
        
        db.curated_observations.update_one(
            {"dataset": "AGREGATION_SEMANTIQUE_ACTION", "key": symbol},
            {"$set": {"attrs": attrs_merged}}
        )
    else:
        # Créer nouveau document (pas de données sémantiques disponibles)
        doc = {
            "source": "AI_ANALYSIS",
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key": symbol,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "value": result.get("score", 0),
            "attrs": {
                "symbol": symbol,
                "signal": result.get("signal"),
                "score": result.get("score"),
                "confiance": result.get("confiance"),
                "details": result.get("details", []),
                "trend": result.get("trend"),
                "rsi": result.get("rsi"),
                "volatility": result.get("volatility"),
                "volume_ratio": result.get("volume_ratio"),
                "vsr": result.get("vsr"),
                "momentum_5j": result.get("momentum_5j"),
                "correlation_penalty": result.get("correlation_penalty", 0),
                "sentiment": result.get("sentiment"),
                "last_technical_update": datetime.now(timezone.utc),
            }
        }
        
        db.curated_observations.insert_one(doc)

from correlation_engine_brvm import ajuster_score_avec_correlation
# =====================
# AGRÉGATION DU SENTIMENT PAR ACTION
# =====================
def get_sentiment_for_symbol(db, symbol: str):
    """
    Agrège le sentiment des publications récentes d’un émetteur
    """
    pubs = list(db.curated_observations.find({
        "source": "BRVM_PUBLICATION",
        "attrs.emetteur": symbol,
        "attrs.sentiment_score": {"$exists": True}
    }))

    if not pubs:
        return None

    # Moyenne pondérée (récent = plus fort)
    total, poids = 0, 0
    for p in pubs:
        score = p["attrs"].get("sentiment_score", 0)
        impact = p["attrs"].get("sentiment_impact", "LOW")

        w = 2 if impact == "HIGH" else 1
        total += score * w
        poids += w

    avg_score = total / poids if poids else 0

    if avg_score >= 20:
        sentiment = "positive"
    elif avg_score <= -20:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "impact": "HIGH" if abs(avg_score) >= 40 else "MEDIUM"
    }
# =====================
# FUSION SCORE TECHNIQUE + SENTIMENT
# =====================
def appliquer_sentiment_au_score(score_technique: float, sentiment_data: dict):
    """
    Fusion score technique + sentiment expert BRVM
    """
    if not sentiment_data:
        return max(0, min(100, round(score_technique, 1))), False  # pas de blocage, borné

    sentiment = sentiment_data.get("sentiment", "neutral")
    impact = sentiment_data.get("impact", "LOW")

    blocage_buy = False
    score_final = score_technique

    if sentiment == "positive":
        if impact == "HIGH":
            score_final += 20
        elif impact == "MEDIUM":
            score_final += 10

    elif sentiment == "negative":
        if impact == "HIGH":
            score_final -= 40
            blocage_buy = True
        elif impact == "MEDIUM":
            score_final -= 15

    # Bornage final
    score_final = max(0, min(100, round(score_final, 1)))

    return score_final, blocage_buy
# =====================
# ANALYSE DE CORRÉLATION INTER-ACTIONS
# =====================
import numpy as np
import pandas as pd

def analyser_correlation_actions(db, min_history=10, top_n=10):
    """
    Calcule la matrice de corrélation des rendements hebdomadaires entre toutes les actions BRVM.
    Affiche les top paires les plus corrélées (positif et négatif).
    CORRECTION: Utilise prices_weekly au lieu de curated_observations
    """
    print("\n=== MATRICE DE CORRÉLATION DES ACTIONS BRVM ===")
    
    # Récupérer les symboles selon le mode
    if MODE_DAILY:
        actions = db.prices_daily.distinct("symbol")
    else:
        actions = db.prices_weekly.distinct("symbol")

    prix_dict = {}
    for symbol in actions:
        if MODE_DAILY:
            docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        else:
            docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", 1))
        if len(docs) < min_history:
            continue

        prix = [d.get("close") for d in docs if d.get("close")]

        if len(prix) < min_history:
            continue
        prix_dict[symbol] = prix
    
    # Alignement des séries (tronquer à la plus courte)
    min_len = min(len(p) for p in prix_dict.values()) if prix_dict else 0
    if min_len < min_history or len(prix_dict) < 2:
        print("Pas assez de données pour la corrélation.")
        return
    prix_aligned = {k: v[-min_len:] for k, v in prix_dict.items()}
    df = pd.DataFrame(prix_aligned)
    # Calcul des rendements hebdomadaires
    returns = df.pct_change().dropna()
    corr_matrix = returns.corr()
    print(corr_matrix.round(2))
    # Top paires corrélées
    pairs = []
    for i, a1 in enumerate(corr_matrix.columns):
        for j, a2 in enumerate(corr_matrix.columns):
            if j <= i:
                continue
            corr = corr_matrix.loc[a1, a2]
            pairs.append(((a1, a2), corr))
    pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)
    print("\nTop paires les plus corrélées (absolu) :")
    for (a1, a2), corr in pairs_sorted[:top_n]:
        print(f"{a1} / {a2} : corrélation = {corr:.2f}")
# =====================
# ANALYSE PUBLICATION BRVM
# =====================

def analyser_publication_brvm(publication: dict) -> dict:
    """
    Analyse experte d'une publication officielle BRVM
    Retourne un impact score et un flag bloquant
    """


    from datetime import datetime

    score = 0
    bloquant = False
    details = []

    if not publication:
        return {"score": 0, "bloquant": False, "details": []}

    p_type = publication.get("type")
    pub_date = publication.get("date")
    if isinstance(pub_date, str):
        try:
            pub_date = datetime.fromisoformat(pub_date)
        except Exception:
            pub_date = None

    aujourd_hui = datetime.now()
    delta = (aujourd_hui - pub_date).days if pub_date else 9999

    # Facteur de fraîcheur par type
    def facteur_fraicheur(type_pub, delta):
        if type_pub == "RESULTATS":
            if delta <= 30:
                return 1.0
            elif delta <= 60:
                return 0.7
            elif delta <= 90:
                return 0.4
            else:
                return 0.0
        elif type_pub == "DIVIDENDE":
            if delta <= 60:
                return 1.0
            elif delta <= 120:
                return 0.7
            else:
                return 0.0
        elif type_pub == "ALERTE":
            if delta <= 180:
                return 1.0
            else:
                return 0.0
        elif type_pub == "GOUVERNANCE":
            if delta <= 45:
                return 0.7
            else:
                return 0.0
        return 0.0

    fraicheur = facteur_fraicheur(p_type, delta)
    if fraicheur == 0.0:
        return {"score": 0, "bloquant": False, "details": ["Publication trop ancienne ou ignorée"]}

    # === RÉSULTATS FINANCIERS ===
    if p_type == "RESULTATS":
        if publication.get("resultat") == "HAUSSE" and publication.get("ca") == "HAUSSE":
            score += 25
            details.append("Résultats et CA en hausse")
        elif publication.get("resultat") == "HAUSSE":
            score += 15
            details.append("Résultat en hausse")
        elif publication.get("resultat") == "BAISSE":
            score -= 25
            bloquant = True
            details.append("Résultat en baisse")

    # === DIVIDENDES ===
    if p_type == "DIVIDENDE":
        rendement = publication.get("rendement", 0)
        evolution = publication.get("evolution")

        if rendement >= 6:
            score += 20
            details.append(f"Dividende attractif ({rendement}%)")
        elif rendement >= 4:
            score += 10
            details.append(f"Dividende correct ({rendement}%)")

        if evolution == "BAISSE":
            score -= 15
            details.append("Dividende en baisse")

    # === ALERTES ===
    if p_type == "ALERTE":
        score -= 30
        bloquant = True
        details.append("Alerte négative officielle")

    # === IMPACT DU SENTIMENT ===
    sentiment = publication.get("sentiment")
    sentiment_score = publication.get("sentiment_score")
    # On considère le champ 'sentiment' ("positif", "negatif", "neutre") ou un score numérique [-1,1]
    if sentiment:
        if sentiment.lower() == "positif":
            score += 10
            details.append("Sentiment positif détecté (+10)")
        elif sentiment.lower() == "negatif":
            score -= 20
            bloquant = True
            details.append("Sentiment négatif détecté (-20, bloquant)")
        elif sentiment.lower() == "neutre":
            details.append("Sentiment neutre (aucun effet)")
    elif sentiment_score is not None:
        # Si score numérique, on applique une pondération
        try:
            s = float(sentiment_score)
            if s > 0.2:
                score += 10 * s
                details.append(f"Sentiment score positif (+{10*s:.1f})")
            elif s < -0.2:
                score += 20 * s  # négatif, donc malus
                bloquant = True
                details.append(f"Sentiment score négatif ({20*s:.1f}, bloquant)")
            else:
                details.append("Sentiment score neutre (aucun effet)")
        except Exception:
            details.append("Erreur lecture sentiment_score")

    # Application du facteur de fraîcheur
    impact = score * fraicheur

    return {
        "score": impact,
        "bloquant": bloquant if fraicheur > 0 else False,
        "details": details + [f"fraicheur={fraicheur:.2f}", f"age={delta}j"]
    }
"""
Moteur de recommandations BRVM
Analyse technique + logique métier + backtesting
VERSION STABLE V1
"""

# =====================
# IMPORTS
# =====================
import os
import sys
import math
import statistics
from datetime import datetime
from typing import List, Dict

# Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# =====================
# OUTILS TECHNIQUES
# =====================

def calculer_sma(prix: List[float], n: int):
    return sum(prix[-n:]) / n if len(prix) >= n else None

def calculer_ema(prix: List[float], n: int):
    if len(prix) < n:
        return None
    k = 2 / (n + 1)
    ema = prix[0]
    for p in prix[1:]:
        ema = p * k + ema * (1 - k)
    return ema

def calculer_rsi(prix: List[float], n: int = 14):
    if len(prix) < n + 1:
        return None
    gains, pertes = [], []
    for i in range(1, len(prix)):
        diff = prix[i] - prix[i - 1]
        gains.append(max(diff, 0))
        pertes.append(abs(min(diff, 0)))
    avg_gain = statistics.mean(gains[-n:])
    avg_loss = statistics.mean(pertes[-n:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculer_volatilite(prix: List[float], nb_transactions: List[int] = None, n: int = 8):
    """
    CORRECTION PHASE 1: ATR% ROBUSTE BRVM (Médian filtré)
    
    Expertise 30 ans BRVM:
    - Filtre semaines <10 transactions (données non-représentatives)
    - Utilise MÉDIAN au lieu de moyenne (robuste aberrations)
    - ATR% normal BRVM: Large-caps 8-15%, Small-caps 10-22%, Micro-caps 12-30%
    """
    if len(prix) < n + 1:
        return None
    
    # Filtre semaines valides (≥10 transactions si données disponibles)
    semaines_valides = list(range(1, len(prix)))

    if nb_transactions and len(nb_transactions) == len(prix):
        nb_valides = [v for v in nb_transactions if v and v > 0]
        if len(nb_valides) >= 5:  # Filtrer seulement si le champ est bien renseigné
            filtrees = [i for i in range(1, len(prix)) if nb_transactions[i] >= 10]
            if len(filtrees) >= 3:  # Ne pas filtrer si trop restrictif
                semaines_valides = filtrees

    if len(semaines_valides) < 3:  # Minimum 3 semaines valides
        return None
    
    # True Range % (normaliser par prix directement)
    true_ranges_pct = []
    for i in semaines_valides:
        if prix[i-1] > 0 and prix[i] > 0:
            tr_pct = abs(prix[i] - prix[i-1]) / prix[i] * 100
            true_ranges_pct.append(tr_pct)
    
    if len(true_ranges_pct) < 3:
        return None
    
    # ATR% = MÉDIAN des TR% (robuste outliers)
    atr_pct = statistics.median(true_ranges_pct[-n:])
    
    # Plafonner 60% max (micro-caps extrêmes)
    if atr_pct > 60.0:
        return 60.0
    
    return round(atr_pct, 2)

def calculer_volume_percentile(volumes: List[float], lookback: int = 20):
    """
    CORRECTION PHASE 1: Volume PERCENTILE (Robuste asymétrie BRVM)
    
    Expertise 30 ans BRVM:
    - Distribution volume très asymétrique (beaucoup de 0)
    - Percentile plus robuste que Z-score
    - 20 semaines historique (au lieu de 8)
    
    Retourne:
    - "VOLUME_EXCEPTIONNEL" si ≥90e percentile
    - "VOLUME_FORT" si ≥75e percentile
    - "VOLUME_FAIBLE" si ≤25e percentile
    - "VOLUME_NORMAL" sinon
    """
    if len(volumes) < 10:  # Minimum 10 semaines
        return None, None
    
    # Historique (exclure courant)
    volumes_hist = volumes[:-1] if len(volumes) > lookback else volumes[:-1]
    volumes_hist = volumes_hist[-lookback:]  # Dernières 20 semaines
    
    # Filtrer les 0 (normaux BRVM)
    volumes_non_nuls = [v for v in volumes_hist if v > 0]
    
    if len(volumes_non_nuls) < 5:  # Minimum 5 semaines actives
        return None, None
    
    current_vol = volumes[-1]
    
    if current_vol == 0:
        return "VOLUME_FAIBLE", 0
    
    # Percentile ranking
    percentile = percentileofscore(volumes_non_nuls, current_vol)
    
    # Classification
    if percentile >= 90:
        return "VOLUME_EXCEPTIONNEL", round(percentile, 1)
    elif percentile >= 75:
        return "VOLUME_FORT", round(percentile, 1)
    elif percentile <= 25:
        return "VOLUME_FAIBLE", round(percentile, 1)
    else:
        return "VOLUME_NORMAL", round(percentile, 1)

def calculer_drawdown(capital_history: List[float]):
    pic = capital_history[0]
    dd = 0
    for c in capital_history:
        pic = max(pic, c)
        dd = max(dd, (pic - c) / pic)
    return round(dd * 100, 2)

def calculer_momentum_regression(prix: List[float], lookback: int = 12):
    """
    CORRECTION PHASE 1: Momentum RÉGRESSION LINÉAIRE (Signal lent BRVM)
    
    Expertise 30 ans BRVM:
    - BRVM récompense signal LENT (pas rapide)
    - Pente régression 12 semaines filtre discontinuités
    - Annualisation: pente weekly × 52 = rendement attendu
    
    Retourne: Momentum annualisé en %
    """
    if len(prix) < lookback:
        return None
    
    # Dernières 12 semaines
    prix_recent = prix[-lookback:]
    
    # Filtrer prix invalides
    prix_valides = [p for p in prix_recent if p > 0]
    if len(prix_valides) < 8:  # Min 8 semaines valides
        return None
    
    # Régression linéaire sur log(prix)
    weeks = list(range(len(prix_valides)))
    log_prices = [np.log(p) for p in prix_valides]
    
    try:
        pente, intercept, r_value, p_value, std_err = linregress(weeks, log_prices)
    except Exception:
        return None
    
    # Annualiser: pente weekly → rendement annuel attendu
    momentum_annuel = pente * 52 * 100  # En %
    
    return round(momentum_annuel, 2)

def calculer_breakout_score(prix: List[float], lookback: int = 20):
    """
    MODULE A — Breakout structurel BRVM
    Mesure si le cours actuel dépasse le range des 20 derniers jours.
    Score = (close - max_range_20j) / ATR_abs_médian
    Positif = breakout, négatif = sous le range.
    """
    if len(prix) < lookback + 1:
        return None
    # max des 20 jours précédents (sans le jour courant)
    fenetre = prix[-lookback - 1:-1]
    if not fenetre:
        return None
    max_range = max(fenetre)
    close = prix[-1]
    # ATR absolu médian sur la même fenêtre pour normaliser
    trs = [abs(prix[i] - prix[i - 1]) for i in range(max(1, len(prix) - lookback), len(prix))]
    atr_abs = statistics.median(trs) if trs else None
    if not atr_abs or atr_abs == 0:
        return None
    score = (close - max_range) / atr_abs
    return round(score, 2)


def calculer_wos(highs: List[float], lows: List[float], closes: List[float], n: int = 3):
    """
    WOS — Weighted Order Strength (microstructure pression d'achat)
    WOS_jour = (Close - Low) / (High - Low)
    Valeur 0→pression vendeuse totale | 0.5→équilibre | 1→pression acheteuse totale

    WOS_n = moyenne glissante sur n jours → accumulation persistante
    Signal fort : WOS_n > 0.70 → accumulation institutionnelle
    """
    if not highs or not lows or not closes:
        return None, None
    if len(highs) < n or len(lows) < n or len(closes) < n:
        return None, None

    wos_values = []
    for i in range(len(closes)):
        h = highs[i]
        l = lows[i]
        c = closes[i]
        if h is None or l is None or c is None:
            continue
        rang = h - l
        if rang <= 0:
            continue
        wos_values.append((c - l) / rang)

    if not wos_values:
        return None, None

    wos_today = round(wos_values[-1], 3)
    wos_n = round(statistics.mean(wos_values[-n:]), 3) if len(wos_values) >= n else wos_today
    return wos_today, wos_n


def calculer_vcp_score(
    prix: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
) -> dict:
    """
    VCP — Volatility Contraction Pattern (Minervini adapté BRVM)
    Détecte l'accumulation silencieuse avant un breakout hebdomadaire.

    Fenêtre DÉCALÉE [-11:-6] pour le court terme (5j excluant les 5 derniers jours)
    ↳ Évite l'overlap avec VolatilityExpansion qui utilise les 5 derniers jours.

    3 signaux combinés (pondérés) :
      50% — ATR_5_delayed / ATR_20  : compression de la volatilité structurelle
      30% — Range_5_delayed / Range_20 : contraction du range prix
      20% — Volume_5_delayed / Volume_20 : disparition des vendeurs

    Score [0-1] :
      >= 0.60 → VCP_FORT    (compression profonde, entrée imminente)
      >= 0.35 → VCP_MODERE  (compression partielle)
      >= 0.15 → VCP_FAIBLE  (signal léger)
      < 0.15  → absent
    """
    if len(prix) < 22:  # Minimum : 21 TR + 1 prix de base
        return {"vcp_score": 0.0, "vcp_label": None, "vcp_atr_ratio": None}

    trs = [abs(prix[i] - prix[i - 1]) for i in range(1, len(prix))]

    # --- Signal 1 : ATR ratio (fenêtre décalée J-10 à J-6) ---
    score_atr = 0.0
    vcp_atr_ratio = None
    if len(trs) >= 11:
        atr_5_delayed = statistics.mean(trs[-11:-6]) if len(trs[-11:-6]) == 5 else None
        atr_20 = statistics.mean(trs[-20:]) if len(trs) >= 20 else None
        if atr_5_delayed and atr_20 and atr_20 > 0:
            vcp_atr_ratio = round(atr_5_delayed / atr_20, 3)
            score_atr = max(0.0, min(1.0, 1.0 - vcp_atr_ratio))

    # --- Signal 2 : Range contraction (fenêtre décalée J-10 à J-6) ---
    score_range = 0.0
    if (highs and lows
            and len(highs) >= 20 and len(lows) >= 20
            and len(highs[-11:-6]) == 5):
        range_5  = max(highs[-11:-6]) - min(lows[-11:-6])
        range_20 = max(highs[-20:])   - min(lows[-20:])
        if range_20 > 0:
            ratio_range = range_5 / range_20
            # Score max quand ratio proche 0, nul quand ratio >= 0.4
            score_range = max(0.0, min(1.0, 1.0 - ratio_range / 0.4))

    # --- Signal 3 : Volume en baisse (fenêtre décalée J-10 à J-6) ---
    score_vol = 0.0
    if volumes and len(volumes) >= 20:
        vols_delayed = [v for v in volumes[-11:-6] if v and v > 0]
        vols_20      = [v for v in volumes[-20:]  if v and v > 0]
        if vols_delayed and vols_20:
            moy_delayed = statistics.mean(vols_delayed)
            moy_20      = statistics.mean(vols_20)
            if moy_20 > 0:
                ratio_vol = moy_delayed / moy_20
                # Score max quand ratio proche 0, nul quand ratio >= 0.8
                score_vol = max(0.0, min(1.0, 1.0 - ratio_vol / 0.8))

    # Score composite pondéré
    vcp_score = round(0.50 * score_atr + 0.30 * score_range + 0.20 * score_vol, 3)

    if vcp_score >= 0.60:
        vcp_label = "VCP_FORT"
    elif vcp_score >= 0.35:
        vcp_label = "VCP_MODERE"
    elif vcp_score >= 0.15:
        vcp_label = "VCP_FAIBLE"
    else:
        vcp_label = None

    return {
        "vcp_score": vcp_score,
        "vcp_label": vcp_label,
        "vcp_atr_ratio": vcp_atr_ratio,
    }


def calculer_score_alpha(
    breakout_raw,
    vol_today,
    vols_20j,
    rs_cumul,
    prix,
    vcp_score=0.0,
    wos_n=None,  # conservé pour rétrocompatibilité, non utilisé dans le score
):
    """
    Breakout Acceleration Score (formule desk quant)
    Détecte les surperformeurs potentiels +8 à +15% sur 1-2 semaines.

    SCORE_ALPHA = 0.30*Breakout + 0.25*VolumeShock + 0.20*RS + 0.15*VolExpansion + 0.10*VCP
    Résultat entre 0 et 1 :
      > 0.75 → SURPERFORMEUR candidat
      0.60-0.75 → swing fort
      0.45-0.60 → trade moyen
      < 0.45 → ignorer
    """
    import math

    # --- Composant 1: Breakout normalisé [0-1] ---
    # breakout_raw = (close - max_20j) / ATR_abs
    if breakout_raw is not None:
        b_norm = min(1.0, max(0.0, breakout_raw / 2.0))
    else:
        b_norm = 0.0

    # --- Composant 2: VolumeShock log-normalisé [0-1] ---
    # vol×3 → 1.0 | vol×2 → 0.73 | vol×1.3 → 0.29
    v_norm = 0.0
    if vol_today and vols_20j:
        vols_valid = [v for v in vols_20j if v and v > 0]
        if vols_valid:
            vol_mean_20j = statistics.mean(vols_valid)
            if vol_mean_20j > 0:
                vol_ratio = vol_today / vol_mean_20j
                v_norm = min(1.0, math.log(vol_ratio + 1) / math.log(3))

    # --- Composant 3: RelativeStrength sigmoid [0-1] ---
    # Centré sur 0.5 (neutre quand RS=0)
    if rs_cumul is not None:
        rs_norm = 1.0 / (1.0 + math.exp(-rs_cumul / 10.0))
    else:
        rs_norm = 0.5  # neutre (BRVMC indisponible)

    # --- Composant 4: VolatilityExpansion ATR_5j/ATR_20j [0-1] ---
    # Fenêtre courante [-5:] — détecte l'explosion en cours aujourd'hui
    ve_norm = 0.0
    if len(prix) >= 21:
        trs = [abs(prix[i] - prix[i - 1]) for i in range(1, len(prix))]
        if len(trs) >= 20:
            atr_5j  = statistics.median(trs[-5:])
            atr_20j = statistics.median(trs[-20:])
            if atr_20j > 0:
                ve_norm = min(1.0, (atr_5j / atr_20j) / 2.0)

    # --- Composant 5: VCP — compression pré-breakout [0-1] ---
    # Fenêtre décalée [-11:-6] — détecte l'accumulation silencieuse J-10 à J-6
    # Orthogonal à VolExp (fenêtres non-superposées)
    vcp_norm = max(0.0, min(1.0, float(vcp_score))) if vcp_score else 0.0

    score = round(
        0.30 * b_norm
        + 0.25 * v_norm
        + 0.20 * rs_norm
        + 0.15 * ve_norm
        + 0.10 * vcp_norm,
        3
    )

    if score >= 0.75:
        label = "SURPERFORMEUR"
    elif score >= 0.60:
        label = "SWING_FORT"
    elif score >= 0.45:
        label = "SWING_MOYEN"
    else:
        label = "IGNORER"

    return {
        "score_alpha": score,
        "alpha_label": label,
        "alpha_breakout": round(b_norm, 3),
        "alpha_vol_shock": round(v_norm, 3),
        "alpha_rs": round(rs_norm, 3),
        "alpha_vol_exp": round(ve_norm, 3),
        "alpha_vcp": round(vcp_norm, 3),
    }


def calculer_atr_expansion(prix: List[float], lookback: int = 10):
    """
    MODULE B — Expansion de volatilité BRVM
    Ratio ATR du jour courant / ATR moyen des 10 jours précédents.
    ratio >= 1.5 = volatilité en expansion (précurseur d'explosion).
    ratio >= 2.0 = explosion confirmée.
    """
    if len(prix) < lookback + 2:
        return None
    # True Range approximé = |close[i] - close[i-1]|
    trs = [abs(prix[i] - prix[i - 1]) for i in range(1, len(prix))]
    if len(trs) < lookback + 1:
        return None
    tr_today = trs[-1]
    atr_hist = trs[-lookback - 1:-1]
    atr_10j = statistics.mean(atr_hist) if atr_hist else None
    if not atr_10j or atr_10j == 0:
        return None
    return round(tr_today / atr_10j, 2)


def calculer_relative_strength_cumul(prix_action: List[float], prix_brvm_composite: List[float], lookback: int = 12):
    """
    CORRECTION PHASE 1: Relative Strength CUMULÉE (12 semaines)
    
    Expertise 30 ans BRVM:
    - Mesurer rendement cumulé vs BRVM Composite
    - 12 semaines = signal robuste (pas 1 semaine = bruit)
    - Surperformance >10% = très fort
    
    Retourne: RS cumulé en % (positif = surperformance)
    """
    if len(prix_action) < lookback or len(prix_brvm_composite) < lookback:
        return None
    
    # Dernières 12 semaines
    action_recent = prix_action[-lookback:]
    brvm_recent = prix_brvm_composite[-lookback:]
    
    if action_recent[0] <= 0 or brvm_recent[0] <= 0:
        return None
    
    # Rendement cumulé 12 semaines
    rdt_action = (action_recent[-1] / action_recent[0] - 1) * 100
    rdt_brvm = (brvm_recent[-1] / brvm_recent[0] - 1) * 100
    
    # Relative Strength = différence
    rs_cumul = rdt_action - rdt_brvm
    
    return round(rs_cumul, 2)

def detecter_regime_marche(db):
    """
    Détecte régime marché BRVM (haussier/baissier/neutre)
    
    Méthode expert: Moyenne variations toutes actions
    > +1% = HAUSSIER
    < -1% = BAISSIER
    Sinon = NEUTRE
    """
    # Source selon mode : daily = dernier jour, weekly = dernière semaine
    from datetime import datetime
    if MODE_DAILY:
        today = datetime.now().strftime("%Y-%m-%d")
        all_actions = list(db.prices_daily.find({'date': today}, {'variation_pct': 1}))
        if not all_actions:
            last = db.prices_daily.find_one(sort=[("date", -1)])
            if last:
                all_actions = list(db.prices_daily.find({'date': last['date']}, {'variation_pct': 1}))
    else:
        week_str = datetime.now().strftime("%Y-W%V")
        all_actions = list(db.prices_weekly.find({'week': week_str}, {'variation_pct': 1}))
    
    if not all_actions:
        return 'NEUTRAL', 0
    
    variations = [a.get('variation_pct', 0) for a in all_actions]
    avg_var = statistics.mean(variations)
    
    if avg_var > 1:
        return 'BULLISH', avg_var
    elif avg_var < -1:
        return 'BEARISH', avg_var
    else:
        return 'NEUTRAL', avg_var

# =====================
# LOGIQUE MÉTIER BRVM
# =====================

def analyser_action_brvm(
    symbol: str,
    prix: List[float],
    indicateurs: Dict,
    publication: dict = None
) -> Dict | None:
    """
    Logique métier volontairement sobre (BRVM-friendly)
    """

    # CORRECTION EXPERT: 3 semaines minimum pour trading hebdomadaire (pas 30)
    # Suffisant pour RSI(14), SMA(20), ATR avec données collectées depuis 4 mois
    if len(prix) < 3:
        return None

    score = 0
    details = []
    motif_bloquant = False

    # Tendance
    if indicateurs["trend"] == "UP":
        score += 30
        details.append("Tendance haussière (UP)")
    else:
        score -= 20
        details.append("Tendance baissière (DOWN) [BLOQUANT]")
        motif_bloquant = True

    # ========================================
    # CORRECTION 2: RSI PONDÉRÉ PAR LIQUIDITÉ
    # ========================================
    rsi = indicateurs["rsi"]
    volume_moyen_12sem = indicateurs.get("volume_moyen_12sem", 0)
    
    # Seuils liquidité selon mode (daily=÷5 vs weekly)
    LIQUIDE = 1000 if MODE_DAILY else 5000   # tx/jour vs tx/semaine
    MOYEN   =  200 if MODE_DAILY else 1000
    FAIBLE  =   40 if MODE_DAILY else  200
    
    if rsi:
        if volume_moyen_12sem >= LIQUIDE:
            # Blue chip: RSI strict (fiable)
            if 40 <= rsi <= 65:
                score += 20
                details.append(f"RSI favorable ({rsi:.1f}) [LIQUIDE]")
            elif rsi > 80:
                score -= 10
                details.append(f"RSI trop élevé ({rsi:.1f}) [BLOQUANT]")
                motif_bloquant = True
            elif rsi > 65:
                score -= 5
                details.append(f"RSI élevé ({rsi:.1f}) [ALERTE - non bloquant]")
            else:
                details.append(f"RSI neutre ({rsi:.1f})")
        
        elif volume_moyen_12sem >= MOYEN:
            # Mid-cap: RSI souple
            if 35 <= rsi <= 70:
                score += 15
                details.append(f"RSI favorable ({rsi:.1f}) [MID-CAP]")
            elif rsi > 80:
                score -= 5
                details.append(f"RSI élevé ({rsi:.1f}) [ALERTE]")
            else:
                details.append(f"RSI neutre ({rsi:.1f})")
        
        elif volume_moyen_12sem >= FAIBLE:
            # Small-cap: RSI très souple
            if 30 <= rsi <= 75:
                score += 10
                details.append(f"RSI ({rsi:.1f}) [SMALL-CAP]")
            else:
                details.append(f"RSI ({rsi:.1f}) [SMALL-CAP - peu fiable]")
        
        else:
            # Micro-cap: IGNORER RSI (non fiable)
            details.append(f"RSI ({rsi:.1f}) [MICRO-CAP - IGNORÉ, trop peu liquide]")

    # Volatilité (ATR%) - Calibration BRVM réaliste
    vol = indicateurs["volatilite"]
    
    # PHASE 10: Plafonner ATR% à 30% max (nettoyage aberrations)
    if vol is not None and vol > 30.0:
        details.append(f"[!] ATR% aberrant ({vol:.1f}%) PLAFONNE a 30%")
        vol = 30.0
    
    if vol is None:
        details.append("ATR% non calculable")
    elif MODE_DAILY:
        # Seuils ATR journalier BRVM (sweet spot 1-3%)
        # Seuil 0.56% aligné avec decision_finale_brvm.py (gain < 1% = non tradable BRVM)
        if vol < 0.56:
            score -= 15
            details.append(f"ATR% trop faible ({vol:.2f}%) - gain <1% non tradable BRVM [BLOQUANT]")
            motif_bloquant = True
        elif 1.0 <= vol <= 3.0:
            score += 20
            details.append(f"ATR% optimal ({vol:.1f}%) [SWEET SPOT DAILY]")
        elif 0.56 <= vol < 1.0 or 3.0 < vol <= 5.0:
            score += 10
            details.append(f"ATR% acceptable ({vol:.1f}%)")
        elif vol > 5.0:
            score -= 15
            details.append(f"ATR% excessif ({vol:.1f}%) - risque news [BLOQUANT]")
            motif_bloquant = True
        else:
            details.append(f"ATR% modéré ({vol:.1f}%)")
    else:
        # Seuils ATR hebdomadaire BRVM (sweet spot 8-15%)
        if vol < 5:
            score -= 15
            details.append(f"ATR% trop faible ({vol:.1f}%) - marché inerte [BLOQUANT]")
            motif_bloquant = True
        elif 8 <= vol <= 15:
            score += 20
            details.append(f"ATR% optimal ({vol:.1f}%) [SWEET SPOT WEEKLY]")
        elif 5 <= vol < 8 or 15 < vol <= 22:
            score += 10
            details.append(f"ATR% acceptable ({vol:.1f}%)")
        elif vol > 22:
            score -= 15
            details.append(f"ATR% excessif ({vol:.1f}%) - risque news [BLOQUANT]")
            motif_bloquant = True
        else:
            details.append(f"ATR% modéré ({vol:.1f}%)")

    # ========================================
    # CORRECTION 4: VOLUME PERCENTILE (20 SEMAINES)
    # ========================================
    volume_signal = indicateurs.get("volume_signal")
    volume_percentile = indicateurs.get("volume_percentile")
    
    if volume_signal:
        # Scoring expert BRVM 30 ans (percentile plus robuste asymétrie)
        if volume_signal == "VOLUME_EXCEPTIONNEL":
            score += 25
            details.append(f"[!] VOLUME EXCEPTIONNEL: {volume_percentile}e percentile (top 10%)")
        elif volume_signal == "VOLUME_FORT":
            score += 15
            details.append(f"Volume élevé: {volume_percentile}e percentile")
        elif volume_signal == "VOLUME_NORMAL":
            score += 5
            details.append(f"Volume normal: {volume_percentile}e percentile")
        elif volume_signal == "VOLUME_FAIBLE":
            details.append(f"Volume faible: {volume_percentile}e percentile [BLOQUANT]")
            motif_bloquant = True
    else:
        # Fallback: ratio legacy si percentile non calculable
        if indicateurs["volume_ratio"] >= 1.2:
            score += 15
            details.append(f"Volume exceptionnel : {indicateurs['volume_ratio']:.2f}x la moyenne")
        elif indicateurs["volume_ratio"] < 0.7:
            details.append(f"Volume trop faible : {indicateurs['volume_ratio']:.2f}x la moyenne [BLOQUANT]")
            motif_bloquant = True
        else:
            details.append(f"Volume normal : {indicateurs['volume_ratio']:.2f}x la moyenne")

    # ========================================
    # VSR : VOLUME SPIKE RATIO (SIGNAL PRÉCURSEUR)
    # Ratio brut volume actuel / moyenne 10j : détecte la demande institutionnelle
    # ========================================
    vsr = indicateurs.get("vsr")
    if vsr is not None:
        if vsr >= 3.0:
            score += 20
            details.append(f"[!] VSR SPIKE: {vsr:.1f}x volume moyen 10j (signal précurseur fort)")
        elif vsr >= 2.0:
            score += 10
            details.append(f"VSR élevé: {vsr:.1f}x volume moyen 10j")
        elif vsr >= 1.0:
            details.append(f"VSR normal: {vsr:.1f}x volume moyen 10j")
        else:
            details.append(f"VSR faible: {vsr:.1f}x volume moyen 10j")

    # ========================================
    # CORRECTION 3: MOMENTUM RÉGRESSION (12 SEMAINES)
    # En mode daily: informatif uniquement (momentum_5j remplace pour le scoring)
    # ========================================
    momentum_regression = indicateurs.get("momentum_regression")
    if momentum_regression is not None:
        if MODE_DAILY:
            # Mode daily: label uniquement, pas de contribution au score
            if momentum_regression >= 25:
                details.append(f"[!] MOMENTUM FORT: +{momentum_regression:.1f}% annualise (tendance robuste)")
            elif momentum_regression >= 10:
                details.append(f"Momentum positif: +{momentum_regression:.1f}% annualisé")
            elif momentum_regression >= 0:
                details.append(f"Momentum stable: +{momentum_regression:.1f}% annualisé")
            elif momentum_regression < -15:
                details.append(f"Momentum négatif fort: {momentum_regression:.1f}% annualisé [ALERTE]")
            else:
                details.append(f"Momentum négatif: {momentum_regression:.1f}% annualisé")
        else:
            # Mode weekly: momentum annualisé contribue au score (horizon compatible)
            if momentum_regression >= 25:
                score += 25
                details.append(f"[!] MOMENTUM FORT: +{momentum_regression:.1f}% annualise (tendance robuste)")
            elif momentum_regression >= 10:
                score += 15
                details.append(f"Momentum positif: +{momentum_regression:.1f}% annualisé")
            elif momentum_regression >= 0:
                score += 5
                details.append(f"Momentum stable: +{momentum_regression:.1f}% annualisé")
            elif momentum_regression < -15:
                score -= 10
                details.append(f"Momentum négatif fort: {momentum_regression:.1f}% annualisé [ALERTE]")
            else:
                details.append(f"Momentum négatif: {momentum_regression:.1f}% annualisé")

    # Momentum 5j brut : observable, sans extrapolation (daily seulement)
    if MODE_DAILY:
        momentum_5j = indicateurs.get("momentum_5j")
        if momentum_5j is not None:
            if momentum_5j >= 3.0:
                details.append(f"Momentum 5j: +{momentum_5j:.1f}% (accélération court terme)")
            elif momentum_5j >= 1.0:
                details.append(f"Momentum 5j: +{momentum_5j:.1f}%")
            elif momentum_5j <= -3.0:
                details.append(f"Momentum 5j: {momentum_5j:.1f}% (repli récent)")
            else:
                details.append(f"Momentum 5j: {momentum_5j:.1f}%")
    
    # ========================================
    # CORRECTION 5: RELATIVE STRENGTH CUMULÉE (12 SEMAINES)
    # ========================================
    rs_cumul = indicateurs.get("rs_cumul")
    if rs_cumul is not None:
        # Surperformance vs BRVM Composite (expertise: signal institutionnel)
        if rs_cumul >= 10:
            score += 20
            details.append(f"[TOP] SURPERFORMANCE FORTE: +{rs_cumul:.1f}% vs BRVM (12sem)")
        elif rs_cumul >= 5:
            score += 15
            details.append(f"Surperformance: +{rs_cumul:.1f}% vs BRVM")
        elif rs_cumul >= -5:
            score += 5
            details.append(f"Performance neutre: {rs_cumul:+.1f}% vs BRVM")
        elif rs_cumul < -10:
            score -= 10
            details.append(f"Sous-performance forte: {rs_cumul:.1f}% vs BRVM [ALERTE]")
        else:
            details.append(f"Sous-performance: {rs_cumul:.1f}% vs BRVM")

    # ========================================
    # MODULE A: BREAKOUT STRUCTUREL (close > max range 20j)
    # ========================================
    publication_analysis = analyser_publication_brvm(publication if 'publication' in locals() else None)
    breakout_score = indicateurs.get("breakout_score")
    if breakout_score is not None:
        if breakout_score > 1.5:
            score += 35
            details.append(f"[BREAKOUT] EXPLOSION: +{breakout_score:.1f}x ATR au-dessus du range 20j [SIGNAL FORT]")
        elif breakout_score > 0.5:
            score += 20
            details.append(f"[BREAKOUT] Cassure haussiere: +{breakout_score:.1f}x ATR au-dessus du range 20j")
        elif breakout_score > 0.0:
            score += 10
            details.append(f"[BREAKOUT] Proche resistance: {breakout_score:.2f}x ATR du range 20j")
        elif breakout_score > -1.0:
            details.append(f"Dans le range ({breakout_score:.2f}x ATR du range 20j)")
        else:
            score -= 5
            details.append(f"Sous le range 20j ({breakout_score:.2f}x ATR)")

    # ========================================
    # MODULE B: ATR EXPANSION (volatilite en expansion)
    # ========================================
    atr_expansion = indicateurs.get("atr_expansion")
    if atr_expansion is not None:
        if atr_expansion >= 2.0:
            score += 20
            details.append(f"[ATR-EXP] EXPLOSION VOLATILITE: {atr_expansion:.1f}x ATR moyen 10j [PRECURSEUR]")
        elif atr_expansion >= 1.5:
            score += 12
            details.append(f"[ATR-EXP] Volatilite en expansion: {atr_expansion:.1f}x ATR moyen 10j")
        elif atr_expansion >= 1.2:
            score += 5
            details.append(f"[ATR-EXP] Legere expansion: {atr_expansion:.1f}x ATR moyen 10j")
        else:
            details.append(f"ATR stable: {atr_expansion:.1f}x moyen 10j")

    # ========================================
    # MODULE C: VOLUME SHOCK DEDIE (VSR + percentile combines)
    # Bonus additionnel quand les DEUX conditions sont reunies
    # ========================================
    vol_shock_score = indicateurs.get("vol_shock_score", 0)
    vol_shock_label = indicateurs.get("vol_shock_label")
    if vol_shock_label == "SHOCK_FORT":
        score += vol_shock_score
        details.append(f"[VOL-SHOCK] DEMANDE INSTITUTIONNELLE FORTE: VSR x volume percentile>=90 [SIGNAL TOP]")
    elif vol_shock_label == "SHOCK_MODERE":
        score += vol_shock_score
        details.append(f"[VOL-SHOCK] Volume shock modere: double confirmation VSR+percentile")
    elif vol_shock_label == "SHOCK_FAIBLE":
        score += vol_shock_score
        details.append(f"[VOL-SHOCK] Signal volume inhabituel (faible)")

    # ========================================
    # MODULE WOS: PRESSION ACHETEUSE MICROSTRUCTURE
    # Informatif uniquement — remplacé par VCP dans SCORE_ALPHA
    # ========================================
    wos_3 = indicateurs.get("wos_3")
    wos_today = indicateurs.get("wos_today")
    if wos_3 is not None:
        if wos_3 >= 0.70:
            details.append(f"[WOS] Accumulation institutionnelle: WOS_3={wos_3:.2f} (pression acheteuse forte)")
        elif wos_3 >= 0.50:
            details.append(f"[WOS] Pression équilibrée: WOS_3={wos_3:.2f}")
        else:
            details.append(f"[WOS] Pression vendeuse: WOS_3={wos_3:.2f} (signal baissier microstructure)")

    # ========================================
    # MODULE VCP: VOLATILITY CONTRACTION PATTERN (Minervini)
    # Détecte l'accumulation silencieuse J-10 à J-6 (orthogonal à VolExp)
    # ========================================
    vcp_label = indicateurs.get("vcp_label")
    vcp_score_val = indicateurs.get("vcp_score", 0.0)
    vcp_atr_ratio = indicateurs.get("vcp_atr_ratio")
    if vcp_label == "VCP_FORT":
        details.append(f"[VCP] COMPRESSION FORTE: score={vcp_score_val:.2f} ATR_ratio={vcp_atr_ratio} — setup pré-breakout")
    elif vcp_label == "VCP_MODERE":
        details.append(f"[VCP] Compression modérée: score={vcp_score_val:.2f} ATR_ratio={vcp_atr_ratio}")
    elif vcp_label == "VCP_FAIBLE":
        details.append(f"[VCP] Légère compression: score={vcp_score_val:.2f}")

    # === IMPACT PUBLICATIONS BRVM ===
    score += publication_analysis["score"]
    if publication_analysis.get("details"):
        for d in publication_analysis["details"]:
            if "trop ancienne" in d or "baisse" in d or "Alerte" in d or "bloquant" in d or "négatif" in d:
                details.append(f"[Publication] {d} [BLOQUANT]")
                motif_bloquant = True
            else:
                details.append(f"[Publication] {d}")

    # Récupération du sentiment agrégé
    from plateforme_centralisation.mongo import get_mongo_db as _get_mongo_db
    try:
        _, db = _get_mongo_db()
    except Exception:
        db = None
    sentiment_data = get_sentiment_for_symbol(db, symbol) if db is not None else None
    if sentiment_data:
        if sentiment_data.get("sentiment") == "negative":
            details.append(f"Sentiment agrégé : {sentiment_data} [BLOQUANT]")
            motif_bloquant = True
        else:
            details.append(f"Sentiment agrégé : {sentiment_data}")

    # Fusion score technique + sentiment
    score_final, blocage_buy = appliquer_sentiment_au_score(
        score_technique=score,
        sentiment_data=sentiment_data
    )

    # === AJUSTEMENT PAR LA CORRÉLATION (si matrice fournie) ===
    try:
        from correlation_engine_brvm import ajuster_score_avec_correlation
        if 'correlation_matrix' in globals() and correlation_matrix is not None:
            score_final = ajuster_score_avec_correlation(
                symbol=symbol,
                score_initial=score_final,
                portefeuille=globals().get('portefeuille_actuel', []),
                watchlist_buy=globals().get('actions_buy_fortes', []),
                corr_matrix=correlation_matrix
            )
    except Exception as e:
        pass

    # Génération du signal (tolérance zéro)
    if blocage_buy or publication_analysis["bloquant"] or motif_bloquant:
        signal = "SELL"
    elif score_final >= 70:
        signal = "BUY"
    elif score_final >= 50:
        signal = "HOLD"
    else:
        signal = "SELL"

    confiance = min(100, max(0, score_final))

    return {
        "symbol": symbol,
        "score": score_final,
        "signal": signal,
        "confiance": confiance,
        "prix_actuel": prix[-1],
        "details": details,
        "sentiment": sentiment_data,
        "vsr": indicateurs.get("vsr"),
        "momentum_5j": indicateurs.get("momentum_5j"),
        "momentum_10j": indicateurs.get("momentum_10j"),
        "breakout_score": indicateurs.get("breakout_score"),   # MODULE A
        "atr_expansion": indicateurs.get("atr_expansion"),    # MODULE B
        "vol_shock_label": indicateurs.get("vol_shock_label"), # MODULE C
        "wos_today": indicateurs.get("wos_today"),             # WOS microstructure J0
        "wos_3": indicateurs.get("wos_3"),                     # WOS moyen 3 séances
        "vcp_score": indicateurs.get("vcp_score"),             # VCP compression [0-1]
        "vcp_label": indicateurs.get("vcp_label"),             # VCP_FORT/MODERE/FAIBLE
        "vcp_atr_ratio": indicateurs.get("vcp_atr_ratio"),     # ATR_5_delayed/ATR_20
        "timestamp": datetime.now().isoformat()
    }

# =====================
# BACKTEST SIMPLE
# =====================

def backtest_action_brvm(symbol: str, historique: List[Dict], engine):
    if len(historique) < 260:
        return None

    capital = 1_000_000
    capital_history = []

    for i in range(252, len(historique) - 21, 21):
        window = historique[:i]
        prix = [d["prix"] for d in window]
        indicateurs = engine._get_indicateurs(prix)

        res = analyser_action_brvm(symbol, prix, indicateurs)
        if res and res["signal"] == "BUY":
            rendement = (historique[i + 21]["prix"] - prix[-1]) / prix[-1]
            capital *= (1 + rendement)

        capital_history.append(capital)

    return {
        "symbol": symbol,
        "capital_final": round(capital, 0),
        "performance_pct": round((capital - 1_000_000) / 1_000_000 * 100, 2),
        "drawdown": calculer_drawdown(capital_history)
    }

# =====================
# ENGINE
# =====================

class RecommendationEngine:

    def __init__(self, db):
        self.db = db

    def _get_indicateurs(self, prix: List[float], volumes: List[float] = None, nb_transactions: List[int] = None, prix_brvm_composite: List[float] = None, highs: List[float] = None, lows: List[float] = None):
        """
        PHASE 1: Calcul indicateurs avec corrections BRVM
        """
        # SMA5 vs SMA10 : compatible 18 semaines BRVM (SMA50 requiert 50 semaines)
        sma5  = calculer_sma(prix, 5)
        sma10 = calculer_sma(prix, 10)
        trend = "UP" if sma5 and sma10 and sma5 > sma10 else "DOWN"

        # CORRECTION 1: ATR% robuste (médian filtré)
        atr_pct = calculer_volatilite(prix, nb_transactions, n=14 if MODE_DAILY else 8)

        # CORRECTION 4: Volume Percentile (20 semaines / 20 jours)
        volume_signal = None
        volume_percentile = None
        if volumes and len(volumes) >= 10:
            volume_signal, volume_percentile = calculer_volume_percentile(volumes, lookback=20)

        # CORRECTION 3: Momentum Régression (30j daily / 12sem weekly)
        momentum_regression = calculer_momentum_regression(prix, lookback=30 if MODE_DAILY else 12)

        # CORRECTION 5: Relative Strength Cumulé (20j daily / 12sem weekly)
        rs_cumul = None
        if prix_brvm_composite and len(prix_brvm_composite) >= (20 if MODE_DAILY else 12):
            rs_cumul = calculer_relative_strength_cumul(prix, prix_brvm_composite, lookback=20 if MODE_DAILY else 12)

        # VSR : Volume Spike Ratio (volume J0 / moyenne 10 jours précédents)
        # Remplace le fallback statique 1.5 — signal précurseur BRVM
        vsr = None
        if volumes and len(volumes) >= 11:
            vols_hist = [v for v in volumes[-11:-1] if v and v > 0]
            if vols_hist:
                moy_vol_10j = statistics.mean(vols_hist)
                current_vol = volumes[-1] if volumes[-1] else 0
                vsr = round(current_vol / moy_vol_10j, 2) if moy_vol_10j > 0 else None

        # Momentum récent brut : observable, sans extrapolation annualisée
        momentum_5j = None
        momentum_10j = None
        if len(prix) >= 6 and prix[-6] and prix[-6] > 0:
            momentum_5j = round((prix[-1] - prix[-6]) / prix[-6] * 100, 2)
        if len(prix) >= 11 and prix[-11] and prix[-11] > 0:
            momentum_10j = round((prix[-1] - prix[-11]) / prix[-11] * 100, 2)

        # =====================================================================
        # MODULE A — Breakout structurel (close > max range 20j)
        # =====================================================================
        breakout_score = calculer_breakout_score(prix, lookback=20)

        # =====================================================================
        # MODULE B — ATR Expansion (volatilité du jour / ATR moyen 10j)
        # =====================================================================
        atr_expansion = calculer_atr_expansion(prix, lookback=10)

        # =====================================================================
        # MODULE C — Volume Shock dédié (combinaison VSR + percentile)
        # Signal de demande institutionnelle soudaine : DEUX conditions ensemble
        # =====================================================================
        vol_shock_score = 0
        vol_shock_label = None
        if vsr is not None and volume_percentile is not None:
            if vsr >= 2.0 and volume_percentile >= 90:
                vol_shock_score = 30
                vol_shock_label = "SHOCK_FORT"
            elif vsr >= 2.0 and volume_percentile >= 75:
                vol_shock_score = 15
                vol_shock_label = "SHOCK_MODERE"
            elif vsr >= 1.5 and volume_percentile >= 80:
                vol_shock_score = 8
                vol_shock_label = "SHOCK_FAIBLE"

        # =====================================================================
        # MODULE WOS — Pression acheteuse microstructure (High/Low/Close)
        # =====================================================================
        wos_today = None
        wos_3 = None
        if highs and lows and len(highs) >= 3 and len(lows) >= 3:
            try:
                wos_today, wos_3 = calculer_wos(highs, lows, prix, n=3)
            except Exception:
                pass

        # =====================================================================
        # MODULE VCP — Volatility Contraction Pattern (Minervini adapté BRVM)
        # Fenêtre décalée [-11:-6] : orthogonal à VolExp ([-5:])
        # =====================================================================
        vcp_result = calculer_vcp_score(prix, highs or [], lows or [], volumes or [])

        return {
            "trend": trend,
            "rsi": calculer_rsi(prix),
            "volatilite": atr_pct,  # ATR% robuste
            "volume_signal": volume_signal,  # EXCEPTIONNEL/FORT/NORMAL/FAIBLE
            "volume_percentile": volume_percentile,  # 0-100
            "volume_ratio": vsr if vsr is not None else 1.5,  # VSR réel (fini le fallback statique)
            "vsr": vsr,                      # Volume Spike Ratio brut (>3 = spike fort)
            "momentum_regression": momentum_regression,  # Momentum annualisé (signal lent)
            "momentum_5j": momentum_5j,      # Momentum 5j brut observable
            "momentum_10j": momentum_10j,    # Momentum 10j brut observable
            "rs_cumul": rs_cumul,            # Surperformance vs BRVM
            "breakout_score": breakout_score,     # MODULE A: Breakout structurel normalisé ATR
            "atr_expansion": atr_expansion,       # MODULE B: Ratio ATR jour / ATR moyen 10j
            "vol_shock_score": vol_shock_score,   # MODULE C: Score volume shock combiné
            "vol_shock_label": vol_shock_label,   # MODULE C: SHOCK_FORT / MODERE / FAIBLE
            "wos_today": wos_today,               # WOS microstructure séance courante
            "wos_3": wos_3,                       # WOS moyen 3 séances (pression persistante)
            "vcp_score": vcp_result["vcp_score"],       # VCP compression pré-breakout [0-1]
            "vcp_label": vcp_result["vcp_label"],       # VCP_FORT / VCP_MODERE / VCP_FAIBLE
            "vcp_atr_ratio": vcp_result["vcp_atr_ratio"],  # ATR_5_delayed / ATR_20
        }

    def _get_score_alpha(self, indicateurs: dict, volumes: list, prix: list) -> dict:
        """
        Calcule le Breakout Acceleration Score depuis les indicateurs déjà calculés.
        Séparé de _get_indicateurs pour ne pas surcharger la méthode.
        """
        vol_today = volumes[-1] if volumes else None
        vols_20j  = volumes[-21:-1] if len(volumes) > 1 else []
        return calculer_score_alpha(
            breakout_raw=indicateurs.get("breakout_score"),
            vol_today=vol_today,
            vols_20j=vols_20j,
            rs_cumul=indicateurs.get("rs_cumul"),
            prix=prix,
            vcp_score=indicateurs.get("vcp_score", 0.0),
        )

    def analyser_une_action(self, symbol: str):
        # Source de données selon le mode
        if MODE_DAILY:
            docs = list(self.db.prices_daily.find({"symbol": symbol}).sort("date", 1))
            min_docs = 20  # P2 — ATR(14) fiable exige min 20 jours (10 était trop faible)
        else:
            docs = list(self.db.prices_weekly.find({"symbol": symbol}).sort("week", 1))
            min_docs = 2

        if len(docs) < min_docs:
            return None

        # P1 — Liquidity Stability Score (daily mode uniquement)
        # Exclure actions trop peu actives : < 60% jours avec volume > 0 OU valeur échangée < 500K FCFA/j
        # Note: valeur = volume × close (le champ "valeur" du scraper est le prix unitaire, pas la valeur totale)
        if MODE_DAILY:
            derniers_20 = docs[-20:]
            jours_actifs = sum(1 for d in derniers_20 if (d.get("volume") or 0) > 0)
            ratio_actifs = jours_actifs / len(derniers_20) if derniers_20 else 0
            # Valeur échangée réelle = volume × close (FCFA/jour)
            valeur_moy = sum(
                (d.get("volume") or 0) * (d.get("close") or 0)
                for d in derniers_20
            ) / len(derniers_20) if derniers_20 else 0
            if ratio_actifs < 0.60:
                print(f"  [{symbol}] [BLOQUANT-LIQ] {ratio_actifs:.0%} jours avec volume / 20 (min 60%) — action sans marché régulier")
                return None
            if valeur_moy < 500_000:
                print(f"  [{symbol}] [BLOQUANT-LIQ] Valeur échangée moy. {valeur_moy:,.0f} FCFA/j < 500 000 — exécution trop risquée")
                return None

        # Extraction du prix de clôture, volumes, nb_transactions, highs, lows
        prix = [d.get("close") for d in docs if d.get("close")]
        volumes = [d.get("volume", 0) for d in docs]
        nb_transactions = [d.get("nb_transactions", 0) for d in docs]
        highs = [d.get("high") for d in docs]
        lows  = [d.get("low")  for d in docs]

        if len(prix) < min_docs:
            return None

        # PHASE 1: Récupérer BRVM Composite pour RS cumulé
        if MODE_DAILY:
            brvm_docs = list(self.db.prices_daily.find({"symbol": "BRVMC"}).sort("date", 1))
        else:
            brvm_docs = list(self.db.prices_weekly.find({"symbol": "BRVMC"}).sort("week", 1))
        prix_brvm_composite = [d.get("close") for d in brvm_docs if d.get("close")] if brvm_docs else None
        
        # Utiliser les indicateurs déjà calculés si disponibles
        last_doc = docs[-1]
        if last_doc.get("indicators_computed"):
            # Utiliser les indicateurs pré-calculés (legacy)
            indicateurs = {
                "trend": last_doc.get("trend", "NEUTRAL"),
                "rsi": last_doc.get("rsi"),
                "volatilite": last_doc.get("atr_pct"),
                "volume_ratio": last_doc.get("volume_ratio", 1.0),
                "volume_signal": last_doc.get("volume_signal"),
                "volume_percentile": last_doc.get("volume_percentile"),
                "momentum_regression": last_doc.get("momentum_regression"),
                "rs_cumul": last_doc.get("rs_cumul")
            }
        else:
            # PHASE 1: Calculer avec nouvelles fonctions
            indicateurs = self._get_indicateurs(
                prix=prix,
                volumes=volumes,
                nb_transactions=nb_transactions,
                prix_brvm_composite=prix_brvm_composite,
                highs=highs,
                lows=lows,
            )
            # En mode WEEKLY: utiliser atr_pct pré-calculé (H/L/C, build_weekly.py)
            # calculer_volatilite() n'utilise que les closes → sous-estime l'ATR réel BRVM
            if not MODE_DAILY and last_doc.get("atr_pct"):
                indicateurs["volatilite"] = last_doc.get("atr_pct")

        # Ajouter volume_moyen pour RSI pondéré (PHASE 1 - CORRECTION 2)
        if volumes:
            volumes_valides = [v for v in volumes[-12:] if v > 0]
            volume_moyen = statistics.mean(volumes_valides) if volumes_valides else 0
            indicateurs["volume_moyen_12sem"] = volume_moyen

        # Récupération de la dernière publication officielle pour ce symbole
        publication = self.db.publications_officielles.find_one(
            {"key": symbol}, sort=[("date", -1)]
        )

        result = analyser_action_brvm(symbol, prix, indicateurs, publication=publication)
        if result:
            # Calcul et injection du Breakout Acceleration Score
            alpha = self._get_score_alpha(indicateurs, volumes, prix)
            result.update(alpha)
        return result

# =====================
# MAIN
# =====================

def main():
    print("=" * 80)
    print("ANALYSE BRVM – VERSION STABLE")
    print("=" * 80)


    _, db = get_mongo_db()
    engine = RecommendationEngine(db)

    # Affichage d'un échantillon de publications collectées à la BRVM (tous champs bruts)
    print("\n=== ÉCHANTILLON PUBLICATIONS BRVM (champs bruts) ===")
    import pprint
    pubs = list(db.publications_officielles.find().sort("date", -1).limit(10))
    for pub in pubs:
        pprint.pprint(pub)

    # CORRECTION EXPERT: Utiliser le dictionnaire des 47 actions BRVM valides
    from collecter_publications_brvm import ACTIONS_BRVM
    
    # FILTRER : seulement les 47 actions BRVM officielles (depuis prices_daily)
    symboles_db = set(db.prices_daily.distinct("symbol"))
    
    # FILTRER : seulement les 47 actions BRVM officielles
    actions = [symbole for symbole in ACTIONS_BRVM.keys() if symbole in symboles_db]
    
    # Filtrer aussi les indices (au cas où)
    indices_brvm = ['BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10']
    actions = [a for a in actions if a and a not in indices_brvm]
    
    print(f"{len(actions)} actions BRVM tradables détectées (sur 47 officielles)\n")

    # 1. Calcul de la matrice de corrélation (pour tout le marché)
    import pandas as pd
    prix_dict = {}
    min_history = 20 if MODE_DAILY else 2  # P2 — 20 jours minimum pour ATR(14) fiable (était 10)

    label_mode = "journalières (prices_daily)" if MODE_DAILY else "hebdomadaires (prices_weekly)"
    print(f"\n[CORRÉLATION] Analyse des données {label_mode}...")
    for symbol in actions:
        if MODE_DAILY:
            docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        else:
            docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", 1))
        
        if len(docs) < min_history:
            print(f"  [{symbol}] Seulement {len(docs)} semaines - IGNORÉ (min {min_history})")
            continue
            
        # Extraire les prix de clôture
        prix = [d.get("close") for d in docs if d.get("close")]
        
        if len(prix) < min_history:
            print(f"  [{symbol}] Seulement {len(prix)} prix valides - IGNORÉ")
            continue
        prix_dict[symbol] = prix
        print(f"  [{symbol}] OK {len(prix)} donnees")
    min_len = min(len(p) for p in prix_dict.values()) if prix_dict else 0
    correlation_matrix = None
    
    print(f"\n[CORRÉLATION] {len(prix_dict)} actions avec ≥ {min_history} semaines")
    
    # Minimum selon mode pour corrélation
    if min_len >= min_history and len(prix_dict) >= 2:
        prix_aligned = {k: v[-min_len:] for k, v in prix_dict.items()}
        df = pd.DataFrame(prix_aligned)
        returns = df.pct_change().dropna()
        correlation_matrix = returns.corr()
        print(f"[OK] Matrice de correlation calculee ({len(prix_dict)} actions)")
    else:
        print(f"[!] Pas assez de donnees pour la correlation (min_len={min_len}, actions={len(prix_dict)}).")
        print(f"   Actions disponibles: {len(actions)}, Actions avec données: {len(prix_dict)}")

    # 2. Définir le portefeuille actuel (exemple : vide ou à remplir dynamiquement)
    portefeuille_actuel = []  # À remplir selon la logique utilisateur ou historique

    # 3. Première passe : calculer tous les scores pour détecter les BUY forts
    print("\n" + "="*80)
    print("[ANALYSE] Première passe - Calcul des scores techniques")
    print("="*80 + "\n")
    
    resultats = {}
    actions_buy_fortes = []
    actions_rejetees = []
    
    for symbol in actions:
        res = engine.analyser_une_action(symbol)
        if res:
            resultats[symbol] = res
            if res["signal"] == "BUY" and res["score"] >= 70:
                actions_buy_fortes.append(symbol)
            # Sauvegarde IA standardisée
            sauvegarder_analyse_ia(db, symbol, res)
            print(f"[OK] {symbol:6s} | {res['signal']:4s} | Score: {res['score']:5.1f} | Confiance: {res['confiance']:3.0f}%")
        else:
            actions_rejetees.append(symbol)
            
    print(f"\n[RÉSUMÉ] {len(resultats)} actions analysées, {len(actions_rejetees)} rejetées (données insuffisantes)")
    if actions_rejetees:
        print(f"Actions rejetées: {', '.join(actions_rejetees[:10])}" + (" ..." if len(actions_rejetees) > 10 else ""))
    
    # 4. Deuxième passe : recalculer les scores avec la corrélation (si matrice dispo)
    print("\n" + "="*80)
    print("[RECOMMANDATIONS] Deuxième passe - Ajustement corrélation")
    print("="*80 + "\n")
    for symbol in actions:
        res = resultats.get(symbol)
        if not res:
            print(f"{symbol:10s} | REJETÉ (données insuffisantes ou score faible)")
            continue
        # Injection des variables globales pour l'appel de la fonction
        globals()["correlation_matrix"] = correlation_matrix
        globals()["portefeuille_actuel"] = portefeuille_actuel
        globals()["actions_buy_fortes"] = actions_buy_fortes
        # Relancer l'analyse pour appliquer l'ajustement corrélation
        res_corr = engine.analyser_une_action(symbol)
        # Affichage détaillé : signal, score, raisons/détails
        print(f"\n--- {symbol} ---")
        print(f"Signal : {res_corr['signal']} | Score : {res_corr['score']}")
        if res_corr.get('details'):
            print("Détails :")
            for d in res_corr['details']:
                print(f"  - {d}")
        if res_corr.get('sentiment'):
            print(f"Sentiment agrégé : {res_corr['sentiment']}")

    print("\n=== BACKTEST ===\n")
    for symbol in actions:
        # CORRECTION: Utiliser prices_daily au lieu de curated_observations
        hist = list(
            db.prices_daily.find(
                {"symbol": symbol}
            ).sort("date", 1)
        )
        bt = backtest_action_brvm(symbol, hist, engine)
        if bt:
            print(symbol, bt["performance_pct"], "%", "DD:", bt["drawdown"], "%")

    # Analyse de corrélation inter-actions (affichage complet)
    analyser_correlation_actions(db)

if __name__ == "__main__":
    main()

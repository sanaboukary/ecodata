#!/usr/bin/env python3
"""
ALPHA SCORE V2 - SHADOW MODE (Early Momentum Dominant)
======================================================

Architecture: Hedge Fund Grade - BRVM Adapted
Mode: Shadow deployment (tracking only, NO client impact)

Objectif: Detecter FUTURS leaders (pas leaders passes)

Scoring:
- 35% Early Momentum (3j vs 20j)
- 25% Volume Spike relatif sectorial
- 20% Event Score (resultats, dividendes)
- 20% Sentiment Score (multi-facteurs)

Filtres:
- RS Percentile < 85 (exclut titres deja chers)
- Volume median 5j > seuil minimum
- Liquidite executable

Status: SHADOW MODE - Comparaison v1 vs v2 uniquement
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


# ==========================================
# FILTRES BRVM (Marche illiquide)
# ==========================================

def check_liquidity_filter(db, symbol: str) -> dict:
    """
    Filtre liquidite executable (critique BRVM)
    
    Retourne:
    - executable: bool
    - volume_median_5j: float
    - raison_rejet: str
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # Buffer données historiques
    
    prices = list(db.prices_daily.find({
        "key": symbol,
        "ts": {"$gte": start_date.strftime("%Y-%m-%d")}
    }).sort("ts", -1).limit(5))
    
    if len(prices) < 3:
        return {"executable": False, "volume_median_5j": 0, "raison": "Donnees insuffisantes"}
    
    volumes = []
    for p in prices:
        vol = p.get("attrs", {}).get("Volume", 0)
        if vol > 0:
            volumes.append(vol)
    
    if not volumes:
        return {"executable": False, "volume_median_5j": 0, "raison": "Volume nul"}
    
    volume_median = statistics.median(volumes)
    
    # Seuil BRVM: minimum 100 titres/jour median (executable sans slippage excessif)
    SEUIL_MIN_BRVM = 100
    
    if volume_median < SEUIL_MIN_BRVM:
        return {
            "executable": False, 
            "volume_median_5j": volume_median,
            "raison": f"Liquidite trop faible ({volume_median:.0f} < {SEUIL_MIN_BRVM})"
        }
    
    return {"executable": True, "volume_median_5j": volume_median, "raison": "OK"}


def calculate_rs_percentile(db, symbol: str) -> float:
    """Calcul RS percentile (rank parmi 47 actions)"""
    try:
        # Recuperer RS de toutes les actions
        all_actions = list(db.curated_observations.find({
            "dataset": "ANALYSE_TECHNIQUE_SIMPLE",
            "attrs.rs": {"$exists": True}
        }))
        
        if len(all_actions) < 10:
            return 50.0  # Neutre si pas assez de donnees
        
        # Extraire RS
        rs_values = []
        symbol_rs = None
        
        for action in all_actions:
            rs = action.get("attrs", {}).get("rs", 0)
            if rs > 0:
                rs_values.append(rs)
                if action["key"] == symbol:
                    symbol_rs = rs
        
        if symbol_rs is None or not rs_values:
            return 50.0
        
        # Calcul percentile
        rank = sum(1 for v in rs_values if v < symbol_rs)
        percentile = (rank / len(rs_values)) * 100
        
        return percentile
    
    except Exception:
        return 50.0


# ==========================================
# FACTEUR 1: EARLY MOMENTUM (30%)
# ==========================================

def calculate_early_momentum(db, symbol: str) -> dict:
    """
    Early Momentum = RS_3j / RS_20j × (1 + ΔVolume_relatif)
    
    Capture acceleration RECENTE vs historique
    """
    try:
        end_date = datetime.now()
        start_date_20d = end_date - timedelta(days=60)  # Buffer données historiques
        
        prices = list(db.prices_daily.find({
            "key": symbol,
            "ts": {"$gte": start_date_20d.strftime("%Y-%m-%d")}
        }).sort("ts", -1).limit(20))
        
        if len(prices) < 10:
            return {"score": 0, "details": "Donnees insuffisantes"}
        
        # RS 3 jours
        closes_3d = []
        volumes_3d = []
        for i in range(min(3, len(prices))):
            c = prices[i].get("value", 0) or prices[i].get("attrs", {}).get("Close", 0)
            v = prices[i].get("attrs", {}).get("Volume", 0)
            if c > 0:
                closes_3d.append(c)
                volumes_3d.append(v)
        
        # RS 20 jours
        closes_20d = []
        volumes_20d = []
        for p in prices:
            c = p.get("value", 0) or p.get("attrs", {}).get("Close", 0)
            v = p.get("attrs", {}).get("Volume", 0)
            if c > 0:
                closes_20d.append(c)
                volumes_20d.append(v)
        
        if len(closes_3d) < 2 or len(closes_20d) < 10:
            return {"score": 0, "details": "Donnees insuffisantes"}
        
        # Calcul RS (variation relative)
        rs_3d = ((closes_3d[0] - closes_3d[-1]) / closes_3d[-1]) * 100
        rs_20d = ((closes_20d[0] - closes_20d[-1]) / closes_20d[-1]) * 100
        
        # Ratio acceleration
        if abs(rs_20d) < 0.01:
            momentum_ratio = 1.0
        else:
            momentum_ratio = rs_3d / rs_20d if rs_20d != 0 else 1.0
        
        # Delta volume relatif
        vol_avg_3d = statistics.mean(volumes_3d) if volumes_3d else 1
        vol_avg_20d = statistics.mean(volumes_20d) if volumes_20d else 1
        
        delta_volume = (vol_avg_3d / vol_avg_20d - 1) if vol_avg_20d > 0 else 0
        
        # Score final (normalise 0-100)
        raw_score = momentum_ratio * (1 + delta_volume)
        
        # Normalisation -2 a +2 → 0 a 100
        score = max(0, min(100, 50 + raw_score * 25))
        
        return {
            "score": score,
            "details": {
                "rs_3d": round(rs_3d, 2),
                "rs_20d": round(rs_20d, 2),
                "momentum_ratio": round(momentum_ratio, 2),
                "delta_volume": round(delta_volume, 2)
            }
        }
    
    except Exception as e:
        return {"score": 0, "details": f"Erreur: {str(e)}"}


# ==========================================
# FACTEUR 2: PARTICIPATION RATIO (20%)
# ==========================================

def calculate_participation_ratio(db, symbol: str) -> dict:
    """
    Participation = Volume_jour / Volume_median_20j
    
    Robuste aux volumes faibles BRVM
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Buffer données historiques
        
        prices = list(db.prices_daily.find({
            "key": symbol,
            "ts": {"$gte": start_date.strftime("%Y-%m-%d")}
        }).sort("ts", -1).limit(20))
        
        if len(prices) < 5:
            return {"score": 0, "details": "Donnees insuffisantes"}
        
        # Volume aujourd'hui (ou dernier jour disponible)
        vol_today = prices[0].get("attrs", {}).get("Volume", 0)
        
        # Volumes 20j
        volumes_20d = []
        for p in prices:
            v = p.get("attrs", {}).get("Volume", 0)
            if v > 0:
                volumes_20d.append(v)
        
        if not volumes_20d or vol_today == 0:
            return {"score": 0, "details": "Volume nul"}
        
        vol_median = statistics.median(volumes_20d)
        
        if vol_median == 0:
            return {"score": 0, "details": "Volume median nul"}
        
        participation = vol_today / vol_median
        
        # Score (0-100): participation 0.5x = 25, 1x = 50, 2x = 75, 4x+ = 100
        score = min(100, 25 + (participation - 0.5) * 50)
        score = max(0, score)
        
        return {
            "score": score,
            "details": {
                "volume_today": vol_today,
                "volume_median_20j": round(vol_median, 0),
                "participation_ratio": round(participation, 2)
            }
        }
    
    except Exception as e:
        return {"score": 0, "details": f"Erreur: {str(e)}"}


# ==========================================
# FACTEUR 3: EVENT SCORE (20%)
# ==========================================

def calculate_event_score(db, symbol: str) -> dict:
    """
    Event Score = Poids selon type evenement recent
    
    RESULTATS = 100, DIVIDENDE = 90, NOTATION = 80, etc.
    """
    try:
        # Chercher agregation semantique (deja calcule)
        semantic_data = db.curated_observations.find_one({
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key": symbol
        })
        
        if not semantic_data:
            return {"score": 0, "details": "Pas de donnees semantiques"}
        
        attrs = semantic_data.get("attrs", {})
        events = attrs.get("types_events", [])
        
        # Ponderation evenements (BRVM = news-driven market)
        EVENT_SCORES = {
            "RESULTATS": 100,
            "DIVIDENDE": 90,
            "NOTATION": 80,
            "PARTENARIAT": 70,
            "COMMUNIQUE": 50,
            "CITATION": 30,
            "AUTRE": 20
        }
        
        if not events:
            return {"score": 20, "details": "Aucun evenement"}
        
        # Score = max des evenements detectes
        max_score = max(EVENT_SCORES.get(e, 20) for e in events)
        
        return {
            "score": max_score,
            "details": {
                "events": events,
                "event_principal": events[0] if events else "AUCUN"
            }
        }
    
    except Exception as e:
        return {"score": 0, "details": f"Erreur: {str(e)}"}


# ==========================================
# FACTEUR 4: SENTIMENT SCORE (15%)
# ==========================================

def calculate_sentiment_score(db, symbol: str) -> dict:
    """
    Sentiment Score = Score semantique normalise (multi-facteurs)
    """
    try:
        semantic_data = db.curated_observations.find_one({
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key": symbol
        })
        
        if not semantic_data:
            return {"score": 50, "details": "Donnees manquantes (neutre)"}
        
        attrs = semantic_data.get("attrs", {})
        score_semaine = attrs.get("score_semantique_semaine", 0)
        sentiment = attrs.get("sentiment_global", "NEUTRE")
        
        # Normalisation -500 a +500 → 0 a 100
        # (ajuste selon distribution reelle observee)
        normalized = 50 + (score_semaine / 10)  # Echelle approximative
        normalized = max(0, min(100, normalized))
        
        return {
            "score": normalized,
            "details": {
                "score_semaine": round(score_semaine, 1),
                "sentiment": sentiment
            }
        }
    
    except Exception as e:
        return {"score": 50, "details": f"Erreur: {str(e)} (neutre)"}


# ==========================================
# FACTEUR 5: ACCUMULATION SCORE (15%)
# ==========================================

def calculate_accumulation_score(db, symbol: str) -> dict:
    """
    Accumulation Score = (Close - Low) / (High - Low)
    
    Proxy Order Flow pour BRVM (pas de bid/ask separé)
    0.8-1.0 = acheteurs dominants
    0.5 = equilibre
    0.0-0.2 = vendeurs dominants
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20)  # Buffer données historiques
        
        prices = list(db.prices_daily.find({
            "key": symbol,
            "ts": {"$gte": start_date.strftime("%Y-%m-%d")}
        }).sort("ts", -1).limit(5))
        
        if not prices:
            return {"score": 50, "details": "Donnees insuffisantes (neutre)"}
        
        # Moyenne 5 derniers jours
        accumulation_scores = []
        
        for p in prices:
            attrs = p.get("attrs", {})
            high = attrs.get("High", 0)
            low = attrs.get("Low", 0)
            close = attrs.get("Close", 0)
            
            if high > low and close > 0:
                acc = (close - low) / (high - low)
                accumulation_scores.append(acc)
        
        if not accumulation_scores:
            return {"score": 50, "details": "Calcul impossible (neutre)"}
        
        # Moyenne accumulation 5j
        avg_accumulation = statistics.mean(accumulation_scores)
        
        # Score 0-100 (0.5 = neutre 50)
        score = avg_accumulation * 100
        
        # Interpretation
        if avg_accumulation >= 0.8:
            interpretation = "FORTE ACCUMULATION"
        elif avg_accumulation >= 0.6:
            interpretation = "ACCUMULATION"
        elif avg_accumulation >= 0.4:
            interpretation = "NEUTRE"
        elif avg_accumulation >= 0.2:
            interpretation = "DISTRIBUTION"
        else:
            interpretation = "FORTE DISTRIBUTION"
        
        return {
            "score": score,
            "details": {
                "accumulation_5j": round(avg_accumulation, 3),
                "interpretation": interpretation
            }
        }
    
    except Exception as e:
        return {"score": 50, "details": f"Erreur: {str(e)} (neutre)"}


# ==========================================
# CALCUL ALPHA V2
# ==========================================

def calculate_alpha_v2(db, symbol: str) -> dict:
    """
    ALPHA SCORE V2 - Early Momentum Dominant (4 facteurs)
    
    Formule:
    35% Early Momentum (RS acceleration)
    25% Volume Spike relatif sectorial
    20% Event Score (news-driven)
    20% Sentiment Score (multi-facteurs)
    
    Filtres:
    - RS < 85 percentile
    - Liquidite minimum
    """
    
    # FILTRE 1: Liquidite
    liquidity = check_liquidity_filter(db, symbol)
    if not liquidity["executable"]:
        return {
            "symbol": symbol,
            "alpha_v2": 0,
            "categorie": "REJECTED",
            "raison_rejet": liquidity["raison"],
            "details": None
        }
    
    # FILTRE 2: RS < 85 (exclut titres deja chers)
    rs_percentile = calculate_rs_percentile(db, symbol)
    if rs_percentile >= 85:
        return {
            "symbol": symbol,
            "alpha_v2": 0,
            "categorie": "REJECTED",
            "raison_rejet": f"RS trop eleve P{rs_percentile:.0f} (deja cher)",
            "details": {"rs_percentile": rs_percentile}
        }
    
    # CALCUL FACTEURS (4 facteurs)
    early_momentum = calculate_early_momentum(db, symbol)
    volume_spike = calculate_participation_ratio(db, symbol)  # Renomme: Volume Spike relatif
    event = calculate_event_score(db, symbol)
    sentiment = calculate_sentiment_score(db, symbol)
    
    # ALPHA V2 = Somme ponderee (formule 4 facteurs)
    alpha_v2 = (
        0.35 * early_momentum["score"] +
        0.25 * volume_spike["score"] +
        0.20 * event["score"] +
        0.20 * sentiment["score"]
    )
    
    # Categorie signal
    if alpha_v2 >= 70:
        categorie = "BUY"
    elif alpha_v2 >= 50:
        categorie = "HOLD"
    else:
        categorie = "AVOID"
    
    return {
        "symbol": symbol,
        "alpha_v2": round(alpha_v2, 1),
        "categorie": categorie,
        "raison_rejet": None,
        "details": {
            "rs_percentile": round(rs_percentile, 1),
            "liquidity_ok": True,
            "volume_median_5j": liquidity["volume_median_5j"],
            "early_momentum": early_momentum,
            "volume_spike": volume_spike,
            "event": event,
            "sentiment": sentiment
        }
    }


# ==========================================
# MAIN - SHADOW MODE
# ==========================================

def main():
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("ALPHA SCORE V2 - SHADOW MODE (Early Momentum Dominant)")
    print("Status: TRACKING ONLY - Aucun impact client")
    print("=" * 80 + "\n")
    
    # Liste 47 actions BRVM
    ACTIONS_BRVM_47 = [
        "ABJC", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS",
        "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC", "NEIC", "NSBC",
        "NTLC", "ONTBF", "ORGT", "PALC", "PRSC", "SAFH", "SAFC", "SCRC", "SDCC",
        "SDSC", "SEMC", "SGBC", "SGOC", "SHEC", "SIBC", "SICC", "SIVC", "SLBC",
        "SMBC", "SNTS", "SOGC", "SPHC", "STAC", "STBC", "SVOC", "TTLC", "TTLS",
        "UNXC", "UNLC"
    ]
    
    results = []
    
    print(">> Calcul ALPHA v2 pour 47 actions...\n")
    
    for symbol in ACTIONS_BRVM_47:
        result = calculate_alpha_v2(db, symbol)
        results.append(result)
        
        # Logging progress (chaque 10 actions)
        if len(results) % 10 == 0:
            print(f"   ... {len(results)}/47 actions traitees")
    
    print(f"\nOK - {len(results)} actions traitees\n")
    
    # Tri par ALPHA v2
    results_sorted = sorted(
        [r for r in results if r["categorie"] != "REJECTED"],
        key=lambda x: x["alpha_v2"],
        reverse=True
    )
    
    rejected = [r for r in results if r["categorie"] == "REJECTED"]
    
    # SAUVEGARDE MONGODB (shadow mode)
    print("=" * 80)
    print("SAUVEGARDE RESULTATS (Shadow Mode - Collection separee)")
    print("=" * 80 + "\n")
    
    for result in results:
        doc = {
            "source": "ALPHA_SCORE_V2_SHADOW",
            "dataset": "ALPHA_V2_SHADOW",
            "key": result["symbol"],
            "ts": datetime.utcnow().strftime("%Y-%m-%d"),
            "value": result["alpha_v2"],
            "attrs": {
                "symbol": result["symbol"],
                "alpha_v2": result["alpha_v2"],
                "categorie": result["categorie"],
                "raison_rejet": result["raison_rejet"],
                "details": result["details"],
                "shadow_mode": True,
                "version": "v2_early_momentum",
                "timestamp": datetime.utcnow()
            }
        }
        
        # Upsert
        db.curated_observations.update_one(
            {"dataset": "ALPHA_V2_SHADOW", "key": result["symbol"]},
            {"$set": doc},
            upsert=True
        )
    
    print(f"OK - {len(results)} scores sauvegardes (dataset=ALPHA_V2_SHADOW)\n")
    
    # AFFICHAGE RESULTATS
    print("=" * 80)
    print("TOP 10 ALPHA V2 (Shadow Mode)")
    print("=" * 80 + "\n")
    
    for i, r in enumerate(results_sorted[:10], 1):
        details = r.get("details", {})
        rs_p = details.get("rs_percentile", 0)
        
        print(f"{i:2d}. {r['symbol']:6s} | Alpha v2: {r['alpha_v2']:5.1f} | {r['categorie']:5s} | RS P{rs_p:.0f}")
        
        # Details facteurs (top 5 seulement)
        if i <= 5:
            em = details.get("early_momentum", {})
            part = details.get("participation", {})
            acc = details.get("accumulation", {})
            
            print(f"    Early Momentum: {em.get('score', 0):5.1f} | Details: {em.get('details', {})}")
            print(f"    Participation:  {part.get('score', 0):5.1f} | Ratio: {part.get('details', {}).get('participation_ratio', 0)}")
            print(f"    Accumulation:   {acc.get('score', 0):5.1f} | {acc.get('details', {}).get('interpretation', 'N/A')}")
            print()
    
    print("=" * 80)
    print(f"ACTIONS REJETEES: {len(rejected)}")
    print("=" * 80)
    
    for r in rejected[:5]:  # Afficher 5 premiers rejets
        print(f"  {r['symbol']:6s}: {r['raison_rejet']}")
    
    if len(rejected) > 5:
        print(f"  ... et {len(rejected) - 5} autres\n")
    
    print("\n" + "=" * 80)
    print("SHADOW MODE ACTIF - Comparaison v1 vs v2 disponible")
    print("=" * 80)
    print("\nProchain script: comparaison_v1_v2.py (metriques validation)")
    print()


if __name__ == "__main__":
    main()
